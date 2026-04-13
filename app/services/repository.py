import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from db.db import get_connection

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = ROOT / "snapshots"
RECORDING_DIR = ROOT / "recordings"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ✅ NEW: helper to convert numpy types to native Python
def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    elif hasattr(obj, "item"):  # handles numpy types like int64, float32
        try:
            return obj.item()
        except Exception:
            return str(obj)
    else:
        return obj


def create_event(event: dict[str, Any]) -> int:
    safe_metadata = make_json_safe(event.get("metadata", {}))

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO events(timestamp, event_type, detection_type, confidence, snapshot_path, clip_path, status, metadata_json)
            VALUES(?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                event["timestamp"],
                event["event_type"],
                event["detection_type"],
                event["confidence"],
                event.get("snapshot_path"),
                event.get("clip_path"),
                json.dumps(safe_metadata),  # ✅ FIXED
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_events(limit: int = 100, unresolved_only: bool = False) -> list[dict[str, Any]]:
    query = """
    SELECT e.*, m.display_name AS member_display_name
    FROM events e
    LEFT JOIN members m ON m.id = e.confirmed_member_id
    """
    args: list[Any] = []
    if unresolved_only:
        query += " WHERE e.status != 'confirmed'"
    query += " ORDER BY e.timestamp DESC LIMIT ?"
    args.append(limit)
    with get_connection() as conn:
        rows = conn.execute(query, args).fetchall()
    return [serialize_event(dict(r)) for r in rows]


def get_event(event_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT e.*, m.display_name AS member_display_name
            FROM events e
            LEFT JOIN members m ON m.id = e.confirmed_member_id
            WHERE e.id = ?
            """,
            (event_id,),
        ).fetchone()
    return serialize_event(dict(row)) if row else None


def serialize_event(row: dict[str, Any]) -> dict[str, Any]:
    row["metadata"] = json.loads(row.get("metadata_json") or "{}")
    row.pop("metadata_json", None)
    return row


def list_members() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM members ORDER BY active DESC, display_name ASC").fetchall()
    return [dict(r) for r in rows]


def create_member(payload: dict[str, Any]) -> dict[str, Any]:
    token = payload.get("qr_token") or secrets.token_urlsafe(12)
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO members(name, display_name, role, notes, qr_token, pin_code, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["name"],
                payload.get("display_name") or payload["name"],
                payload.get("role"),
                payload.get("notes"),
                token,
                payload.get("pin_code"),
                1 if payload.get("active", True) else 0,
            ),
        )
        member_id = cur.lastrowid
        conn.commit()
    return get_member(int(member_id))


def get_member(member_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    return dict(row) if row else None


def update_member(member_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    current = get_member(member_id)
    if not current:
        return None
    merged = {**current, **payload}
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE members
            SET name=?, display_name=?, role=?, notes=?, qr_token=?, pin_code=?, active=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                merged["name"],
                merged.get("display_name"),
                merged.get("role"),
                merged.get("notes"),
                merged.get("qr_token"),
                merged.get("pin_code"),
                1 if merged.get("active", True) else 0,
                member_id,
            ),
        )
        conn.commit()
    return get_member(member_id)


def delete_member(member_id: int) -> bool:
    with get_connection() as conn:
        changed = conn.execute("DELETE FROM members WHERE id = ?", (member_id,)).rowcount
        conn.commit()
    return changed > 0


def confirm_event(event_id: int, member_id: int | None, method: str, notes: str | None = None) -> dict[str, Any] | None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE events
            SET status='confirmed', confirmed_member_id=?, confirmation_method=?, notes=?
            WHERE id=?
            """,
            (member_id, method, notes, event_id),
        )
        conn.commit()
    return get_event(event_id)


def confirm_event_by_qr(event_id: int, qr_token: str, notes: str | None = None) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM members WHERE qr_token=? AND active=1", (qr_token,)).fetchone()
    if not row:
        return None
    return confirm_event(event_id, int(row["id"]), "qr", notes)


def confirm_event_by_pin(event_id: int, pin_code: str, notes: str | None = None) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM members WHERE pin_code=? AND active=1", (pin_code,)).fetchone()
    if not row:
        return None
    return confirm_event(event_id, int(row["id"]), "pin", notes)


def stats() -> dict[str, Any]:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) c FROM events WHERE status != 'confirmed'").fetchone()["c"]
        confirmed = conn.execute("SELECT COUNT(*) c FROM events WHERE status='confirmed'").fetchone()["c"]
    return {"total_events": total, "pending_events": pending, "confirmed_events": confirmed}


def run_retention(retention_days: int) -> int:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    with get_connection() as conn:
        rows = conn.execute("SELECT id, snapshot_path, clip_path FROM events WHERE timestamp < ?", (cutoff,)).fetchall()
        deleted = 0
        for row in rows:
            for key in ("snapshot_path", "clip_path"):
                if row[key]:
                    p = ROOT / row[key]
                    if p.exists():
                        p.unlink(missing_ok=True)
            deleted += 1
        conn.execute("DELETE FROM events WHERE timestamp < ?", (cutoff,))
        conn.commit()
    return deleted
