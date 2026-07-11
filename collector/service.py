"""Background telemetry collector decoupled from sensor polling."""

from __future__ import annotations

import threading
import time

from .storage import TelemetryStorage

UNKNOWN_VIN = "UNKNOWN"


class TelemetryCollector:
    def __init__(self, state_provider, storage=None, save_interval=1.0):
        self.state_provider = state_provider
        self.storage = storage or TelemetryStorage()
        self.save_interval = float(save_interval)
        self.current_session_id = None
        self.current_vin = None
        self.running = False

    def _session_vin(self, state):
        vin = (state.get("vin") or "").strip()
        return vin or UNKNOWN_VIN

    def _ensure_session(self, state):
        status = state.get("connection_status")
        if status == "disconnected":
            self.storage.end_session(self.current_session_id)
            self.current_session_id = None
            self.current_vin = None
            return None

        vin = self._session_vin(state)
        if self.current_session_id is None or vin != self.current_vin:
            self.storage.end_session(self.current_session_id)
            self.current_session_id = self.storage.start_session(vin)
            self.current_vin = vin
        return self.current_session_id

    def loop(self):
        self.running = True
        while self.running:
            try:
                state = self.state_provider()
                session_id = self._ensure_session(state)
                if session_id is not None:
                    self.storage.save_metrics(session_id, state)
            except Exception as exc:
                print("[COLLECTOR ERROR]", exc)
            time.sleep(self.save_interval)

    def start(self):
        thread = threading.Thread(target=self.loop, daemon=True)
        thread.start()
