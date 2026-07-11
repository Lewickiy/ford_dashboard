import os
import threading
import time

import obd


class ObdReader:
    OBD_PORT = os.getenv("OBD_PORT", "/dev/ttyUSB0")
    REALTIME_INTERVAL = float(os.getenv("OBD_REALTIME_INTERVAL", "0.25"))
    TEMP_INTERVAL = float(os.getenv("OBD_TEMP_INTERVAL", "5"))
    RECONNECT_INTERVAL = float(os.getenv("OBD_RECONNECT_INTERVAL", "2"))

    def __init__(self):
        self.connection = None
        self.connection_lock = threading.Lock()
        self.last_temp_read = 0.0
        self.state = {
            "speed": 0.0,
            "rpm": 0.0,
            "temp": 0.0,
            "throttle": 0.0,
            "load": 0.0,
            "intake": 0.0,
            "voltage": 0.0,
            "vin": "",
            "fuel_level": 0.0,
            "dtc": None,
            "reverse": False,
            "connected": False,
            "connection_status": "disconnected",
        }
        self.state_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None

    def safe(self, response):
        try:
            if response is None or response.is_null():
                return 0.0
            value = response.value
            if value is None:
                return 0.0
            return float(getattr(value, "magnitude", value))
        except Exception:
            return 0.0

    def safe_text(self, response):
        try:
            if response is None or response.is_null() or response.value is None:
                return ""
            value = response.value
            if isinstance(value, (list, tuple)):
                value = value[0] if value else ""
            return str(value).strip()
        except Exception:
            return ""

    def command(self, name):
        return getattr(obd.commands, name, None)

    def query_optional(self, name):
        command = self.command(name)
        if command is None:
            return None
        return self.query(command)

    def query(self, command):
        if self.connection is None:
            return None
        return self.connection.query(command)

    def _cable_connected(self, status):
        return status != obd.OBDStatus.NOT_CONNECTED

    def _can_query_vehicle(self, status):
        return status == obd.OBDStatus.CAR_CONNECTED

    def _connection_status(self, cable_connected, rpm, voltage, vin):
        if not cable_connected:
            return "disconnected"
        if rpm > 0:
            return "koer"
        if vin and voltage > 10:
            return "koeo"
        return "connected"

    def connect(self):
        while not self._stop_event.is_set():
            try:
                print("[OBD] Connecting...")
                conn = obd.OBD(self.OBD_PORT, fast=False, timeout=5)
                self.connection = conn
                status = conn.status()
                cable_connected = self._cable_connected(status)
                with self.state_lock:
                    self.state["connected"] = cable_connected
                    self.state["connection_status"] = (
                        "connected" if cable_connected else "disconnected"
                    )
                print("[OBD] Adapter status:", status)
                return
            except Exception as e:
                print("[OBD] Connect error:", e)
                self.connection = None
                with self.state_lock:
                    self.state["connected"] = False
                    self.state["connection_status"] = "disconnected"
                if self._stop_event.wait(self.RECONNECT_INTERVAL):
                    return

    def _read_voltage(self):
        for name in ("CONTROL_MODULE_VOLTAGE", "ELM_VOLTAGE"):
            response = self.query_optional(name)
            value = self.safe(response)
            if value:
                return value
        return 0.0

    def loop(self):
        while not self._stop_event.is_set():
            try:
                if self.connection is None:
                    self.connect()
                    if self.connection is None:
                        continue

                with self.connection_lock:
                    status = self.connection.status()
                    cable_connected = self._cable_connected(status)
                    if not cable_connected:
                        raise RuntimeError("OBD cable disconnected")

                    speed = rpm = throttle = load = intake = fuel_level = dtc = None
                    temp = None
                    vin = ""
                    voltage = 0.0

                    if self._can_query_vehicle(status):
                        speed = self.query(obd.commands.SPEED)
                        rpm = self.query(obd.commands.RPM)
                        throttle = self.query(obd.commands.THROTTLE_POS)
                        load = self.query(obd.commands.ENGINE_LOAD)
                        intake = self.query(obd.commands.INTAKE_PRESSURE)
                        voltage = self._read_voltage()
                        vin = self.safe_text(self.query_optional("VIN"))
                        fuel_level = self.query_optional("FUEL_LEVEL")
                        dtc = self.query(obd.commands.GET_DTC)
                        now = time.monotonic()
                        if now - self.last_temp_read >= self.TEMP_INTERVAL:
                            temp = self.query(obd.commands.COOLANT_TEMP)
                            self.last_temp_read = now

                with self.state_lock:
                    self.state["speed"] = self.safe(speed)
                    self.state["rpm"] = self.safe(rpm)
                    if temp is not None:
                        self.state["temp"] = self.safe(temp)
                    self.state["throttle"] = self.safe(throttle)
                    self.state["load"] = self.safe(load)
                    self.state["intake"] = self.safe(intake)
                    self.state["voltage"] = voltage
                    if vin:
                        self.state["vin"] = vin
                    self.state["fuel_level"] = self.safe(fuel_level)
                    self.state["dtc"] = dtc.value if dtc and not dtc.is_null() else None
                    self.state["connected"] = cable_connected
                    self.state["connection_status"] = self._connection_status(
                        cable_connected,
                        self.state["rpm"],
                        self.state["voltage"],
                        self.state["vin"],
                    )

                print("[OBD]", self.state["connection_status"], self.state["speed"], self.state["rpm"], self.state["temp"], self.state["voltage"])
                self._stop_event.wait(self.REALTIME_INTERVAL)
            except Exception as e:
                print("[OBD ERROR]", e)
                with self.state_lock:
                    self.state["connected"] = False
                    self.state["connection_status"] = "disconnected"
                try:
                    if self.connection:
                        self.connection.close()
                except Exception:
                    pass
                self.connection = None
                self._stop_event.wait(self.RECONNECT_INTERVAL)
        self.close()

    def start(self):
        if self._thread and self._thread.is_alive():
            return self._thread
        self._stop_event.clear()
        thread = threading.Thread(target=self.loop, name="obd-reader", daemon=False)
        self._thread = thread
        thread.start()
        return thread

    def close(self):
        with self.connection_lock:
            try:
                if self.connection:
                    self.connection.close()
            except Exception as exc:
                print("[OBD CLOSE ERROR]", exc)
            finally:
                self.connection = None
                with self.state_lock:
                    self.state["connected"] = False
                    self.state["connection_status"] = "disconnected"

    def stop(self, timeout=10.0):
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=timeout)
        if thread is None or not thread.is_alive():
            self.close()
        return thread is None or not thread.is_alive()

    def get_state(self):
        with self.state_lock:
            return self.state.copy()
