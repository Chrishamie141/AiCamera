CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT,
    role TEXT,
    notes TEXT,
    qr_token TEXT NOT NULL UNIQUE,
    pin_code TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    detection_type TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0,
    snapshot_path TEXT,
    clip_path TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    confirmed_member_id INTEGER,
    confirmation_method TEXT,
    notes TEXT,
    metadata_json TEXT,
    FOREIGN KEY (confirmed_member_id) REFERENCES members(id)
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
