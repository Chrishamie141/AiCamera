from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class LocalEvent:
    timestamp: str
    event_type: str
    detection_type: str
    confidence: float
    status: str
    snapshot_path: str | None
    clip_path: str | None
    metadata: dict[str, Any]




def _to_jsonable(value):
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if hasattr(value, "item") and callable(value.item):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


class LocalEventSink:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.db_path = output_dir / "events.sqlite"
        self.jsonl_path = output_dir / "events.jsonl"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                detection_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                status TEXT NOT NULL,
                snapshot_path TEXT,
                clip_path TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def create_pending_event(self, event: LocalEvent) -> int:
        payload = asdict(event)
        metadata_json = json.dumps(_to_jsonable(payload.pop("metadata", {})))
        cursor = self.conn.execute(
            """
            INSERT INTO events(timestamp, event_type, detection_type, confidence, status, snapshot_path, clip_path, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["timestamp"],
                payload["event_type"],
                payload["detection_type"],
                payload["confidence"],
                payload["status"],
                payload["snapshot_path"],
                payload["clip_path"],
                metadata_json,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()
        event_id = int(cursor.lastrowid)

        json_payload = {"id": event_id, **payload, "metadata": json.loads(metadata_json)}
        with self.jsonl_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(json_payload) + "\n")
        return event_id

    def confirm_event(self, event_id: int, method: str, notes: str | None = None):
        event = self.conn.execute("SELECT metadata_json FROM events WHERE id=?", (event_id,)).fetchone()
        if not event:
            return
        meta = json.loads(event["metadata_json"] or "{}")
        meta["confirmation"] = {"method": method, "notes": notes}
        self.conn.execute("UPDATE events SET status='confirmed', metadata_json=? WHERE id=?", (json.dumps(meta), event_id))
        self.conn.commit()

    def summary_counts(self) -> dict[str, int]:
        row = self.conn.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending, "
            "SUM(CASE WHEN status='confirmed' THEN 1 ELSE 0 END) as confirmed FROM events"
        ).fetchone()
        return {
            "total_events": int(row["total"] or 0),
            "pending_arrivals": int(row["pending"] or 0),
            "confirmed_arrivals": int(row["confirmed"] or 0),
        }

    def close(self):
        self.conn.close()
