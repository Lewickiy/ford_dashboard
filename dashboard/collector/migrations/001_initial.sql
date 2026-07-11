CREATE TABLE IF NOT EXISTS vehicles (
    vin TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    ended_at TEXT,
    FOREIGN KEY (vin) REFERENCES vehicles(vin) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    captured_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    speed REAL NOT NULL DEFAULT 0,
    rpm REAL NOT NULL DEFAULT 0,
    coolant_temp REAL NOT NULL DEFAULT 0,
    throttle REAL NOT NULL DEFAULT 0,
    engine_load REAL NOT NULL DEFAULT 0,
    intake_pressure REAL NOT NULL DEFAULT 0,
    voltage REAL NOT NULL DEFAULT 0,
    fuel_level REAL NOT NULL DEFAULT 0,
    dtc_json TEXT,
    connection_status TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_vin_started_at ON sessions(vin, started_at);
CREATE INDEX IF NOT EXISTS idx_metrics_session_captured_at ON metrics(session_id, captured_at);
