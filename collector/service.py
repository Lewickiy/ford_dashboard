"""Background telemetry collector decoupled from sensor polling."""

from __future__ import annotations

import threading

from .storage import TelemetryStorage

UNKNOWN_VIN = "UNKNOWN"
DEFAULT_BATCH_SIZE = 10


class TelemetryCollector:
    """Collect telemetry snapshots and persist them in bounded batches."""

    def __init__(
            self, state_provider, storage=None, save_interval=1.0, batch_size=DEFAULT_BATCH_SIZE
    ):
        self.state_provider = state_provider
        self.storage = storage or TelemetryStorage()
        self.save_interval = max(float(save_interval), 0.1)
        self.batch_size = max(int(batch_size), 1)
        self.current_session_id = None
        self.current_vin = None
        self.running = False
        self._stop_event = threading.Event()
        self._thread = None
        self._pending_metrics = []
        self._lock = threading.Lock()

    def _session_vin(self, state):
        vin = (state.get("vin") or "").strip()
        return vin or UNKNOWN_VIN

    def _flush_pending_locked(self):
        if self.current_session_id is None or not self._pending_metrics:
            self._pending_metrics.clear()
            return
        self.storage.save_metrics_batch(self.current_session_id, self._pending_metrics)
        self._pending_metrics.clear()

    def _ensure_session_locked(self, state):
        status = state.get("connection_status")
        if status == "disconnected":
            self._flush_pending_locked()
            self.storage.end_session(self.current_session_id)
            self.current_session_id = None
            self.current_vin = None
            return None

        vin = self._session_vin(state)
        if self.current_session_id is None or vin != self.current_vin:
            self._flush_pending_locked()
            self.storage.end_session(self.current_session_id)
            self.current_session_id = self.storage.start_session(vin)
            self.current_vin = vin
        return self.current_session_id

    def _collect_once(self):
        state = self.state_provider()
        with self._lock:
            session_id = self._ensure_session_locked(state)
            if session_id is None:
                return
            self._pending_metrics.append(state.copy())
            if len(self._pending_metrics) >= self.batch_size:
                self._flush_pending_locked()

    def loop(self):
        self.running = True
        while not self._stop_event.is_set():
            try:
                self._collect_once()
            except Exception as exc:
                print("[COLLECTOR ERROR]", exc)
            self._stop_event.wait(self.save_interval)
        self._shutdown_persistence()
        self.running = False

    def _shutdown_persistence(self):
        with self._lock:
            try:
                self._flush_pending_locked()
            finally:
                self.storage.end_session(self.current_session_id)
                self.current_session_id = None
                self.current_vin = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return self._thread
        self._stop_event.clear()
        thread = threading.Thread(
            target=self.loop, name="telemetry-collector", daemon=False
        )
        self._thread = thread
        thread.start()
        return thread

    def stop(self, timeout=10.0):
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=timeout)
        if thread is None or not thread.is_alive():
            self._shutdown_persistence()
        return thread is None or not thread.is_alive()
