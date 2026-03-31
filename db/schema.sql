CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    e_timestamp TEXT NOT NULL,
    motion_area INTEGER NOT NULL,
    snapshot TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cameras (
    c_id INTEGER PRIMARY KEY AUTOINCREMENT,
    c_name VARCHAR(20),
    source_type VARCHAR(20),
    enabled BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    settings_id INTEGER PRIMARY KEY AUTOINCREMENT,
    settings_value VARCHAR(20),
    updated_at TIMESTAMP
);

