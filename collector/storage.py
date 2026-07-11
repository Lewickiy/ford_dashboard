"""SQLite-backed telemetry persistence."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).with_name("migrations")


class TelemetryStorage:
    """Persist vehicles, connection sessions, and sensor metrics safely."""

    def __init__(self, db_path="telemetry.sqlite3", migrations_dir=MIGRATIONS_DIR):
        self.db_path = Path(db_path)
        self.migrations_dir = Path(migrations_dir)
        self.lock = threading.Lock()
        self._ensure_parent_dir()
        self._migrate()

    def _ensure_parent_dir(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _migrate(self):
        with self.lock, self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT "
                "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now')))"
            )
            applied = {
                row[0]
                for row in conn.execute("SELECT version FROM schema_migrations")
            }
            for migration in sorted(self.migrations_dir.glob("*.sql")):
                if migration.name in applied:
                    continue
                conn.executescript(migration.read_text(encoding="utf-8"))
                conn.execute(
                    "INSERT INTO schema_migrations(version) VALUES (?)",
                    (migration.name,),
                )

    def start_session(self, vin):
        with self.lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO vehicles(vin) VALUES (?) "
                "ON CONFLICT(vin) DO UPDATE SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')",
                (vin,),
            )
            cursor = conn.execute("INSERT INTO sessions(vin) VALUES (?)", (vin,))
            return cursor.lastrowid

    def end_session(self, session_id):
        if session_id is None:
            return
        with self.lock, self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET ended_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') "
                "WHERE id = ? AND ended_at IS NULL",
                (session_id,),
            )

    def _metric_params(self, session_id, state):
        return (
            session_id,
            float(state.get("speed") or 0),
            float(state.get("rpm") or 0),
            float(state.get("temp") or 0),
            float(state.get("throttle") or 0),
            float(state.get("load") or 0),
            float(state.get("intake") or 0),
            float(state.get("voltage") or 0),
            float(state.get("fuel_level") or 0),
            json.dumps(state.get("dtc"), ensure_ascii=False),
            state.get("connection_status") or "disconnected",
        )

    def save_metrics(self, session_id, state):
        self.save_metrics_batch(session_id, [state])

    def save_metrics_batch(self, session_id, states):
        if session_id is None or not states:
            return
        with self.lock, self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO metrics(
                    session_id, speed, rpm, coolant_temp, throttle, engine_load,
                    intake_pressure, voltage, fuel_level, dtc_json, connection_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [self._metric_params(session_id, state) for state in states],
            )
