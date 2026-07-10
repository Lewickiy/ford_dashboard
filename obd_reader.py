import threading
import time

import obd


class ObdReader:
    OBD_PORT = "/dev/ttyUSB0"

    def __init__(self):

        self.connection = None

        self.connection_lock = threading.Lock()

        self.state = {
            "speed": 0.0,
            "rpm": 0.0,
            "temp": 0.0,
            "throttle": 0.0,
            "load": 0.0,
            "intake": 0.0,
            "maf": 0.0,
            "fuel_level": 0.0,
            "dtc": None,
            "reverse": False,
            "connected": False
        }

        self.state_lock = threading.Lock()

    def safe(self, response):

        try:
            if response is None:
                return 0.0

            if response.is_null():
                return 0.0

            value = response.value

            if value is None:
                return 0.0

            return float(
                getattr(value, "magnitude", value)
            )

        except Exception:
            return 0.0

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

        if self.connection.status() != obd.OBDStatus.CAR_CONNECTED:
            raise RuntimeError(
                "OBD disconnected"
            )

        return self.connection.query(command)

    def connect(self):

        while True:

            try:

                print("[OBD] Connecting...")

                conn = obd.OBD(
                    self.OBD_PORT,
                    fast=False,
                    timeout=5
                )

                if conn.status() != obd.OBDStatus.CAR_CONNECTED:
                    print(
                        "[OBD] Waiting for vehicle..."
                    )

                    time.sleep(3)
                    continue

                self.connection = conn

                with self.state_lock:
                    self.state["connected"] = True

                print("[OBD] Connected")

                return


            except Exception as e:

                print(
                    "[OBD] Connect error:",
                    e
                )

                self.connection = None

                with self.state_lock:
                    self.state["connected"] = False

                time.sleep(3)

    def loop(self):

        while True:

            try:

                if self.connection is None:
                    self.connect()

                with self.connection_lock:

                    speed = self.query(
                        obd.commands.SPEED
                    )

                    rpm = self.query(
                        obd.commands.RPM
                    )

                    temp = self.query(
                        obd.commands.COOLANT_TEMP
                    )

                    throttle = self.query(
                        obd.commands.THROTTLE_POS
                    )

                    load = self.query(
                        obd.commands.ENGINE_LOAD
                    )

                    intake = self.query(
                        obd.commands.INTAKE_PRESSURE
                    )

                    maf = self.query_optional("MAF")

                    fuel_level = self.query_optional("FUEL_LEVEL")

                    dtc = self.query(
                        obd.commands.GET_DTC
                    )

                with self.state_lock:

                    self.state["speed"] = self.safe(speed)
                    self.state["rpm"] = self.safe(rpm)
                    self.state["temp"] = self.safe(temp)

                    self.state["throttle"] = self.safe(throttle)
                    self.state["load"] = self.safe(load)
                    self.state["intake"] = self.safe(intake)
                    self.state["maf"] = self.safe(maf)
                    self.state["fuel_level"] = self.safe(fuel_level)

                    self.state["dtc"] = (
                        dtc.value
                        if dtc and not dtc.is_null()
                        else None
                    )

                    self.state["connected"] = True

                print(
                    "[OBD]",
                    self.state["speed"],
                    self.state["rpm"],
                    self.state["temp"]
                )

                time.sleep(0.25)



            except Exception as e:

                print(
                    "[OBD ERROR]",
                    e
                )

                with self.state_lock:
                    self.state["connected"] = False

                try:
                    if self.connection:
                        self.connection.close()

                except:
                    pass

                self.connection = None

                time.sleep(2)

    def start(self):

        thread = threading.Thread(
            target=self.loop,
            daemon=True
        )

        thread.start()

    def get_state(self):

        with self.state_lock:
            return self.state.copy()
