import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "events.db"
SCHEMA_PATH = ROOT / "db" / "schema.sql"

DEFAULT_SETTINGS = {
    "profile": "balanced",
    "motion_enabled": True,
    "person_enabled": True,
    "face_enabled": True,
    "snapshot_enabled": True,
    "clip_enabled": False,
    "motion_min_area": 1200,
    "person_confidence": 0.5,
    "face_confidence": 1.1,
    "retention_days": 14,
}


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text())
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )
        conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def get_settings() -> dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    parsed: dict[str, Any] = {}
    for row in rows:
        parsed[row["key"]] = json.loads(row["value"])
    return parsed


def update_settings(payload: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as conn:
        for key, value in payload.items():
            conn.execute(
                """
                INSERT INTO settings(key, value, updated_at)
                VALUES(?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
                """,
                (key, json.dumps(value)),
            )
        conn.commit()
    return get_settings()
