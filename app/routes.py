from flask import Blueprint, Response, jsonify
from backend.camera.stream import generate_frames
import json
import os

api = Blueprint("api", __name__)

EVENTS_FILE = "backend/events/events.json"


def load_events():
    if not os.path.exists(EVENTS_FILE):
        return {"events": []}

    try:
        with open(EVENTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"events": []}


@api.route("/api/stream")
def stream():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@api.route("/api/events")
def get_events():
    return jsonify(load_events())


@api.route("/api/stats")
def get_stats():
    data = load_events()
    events = data.get("events", [])

    latest_event = events[0] if events else None

    return jsonify({
        "motion": latest_event is not None,
        "person_detected": latest_event is not None and latest_event.get("type") == "intrusion",
        "area": latest_event.get("motion_area", 0) if latest_event else 0,
        "people": latest_event.get("people", 0) if latest_event else 0,
        "camera_index": latest_event.get("camera_index") if latest_event else None,
        "last_event_time": latest_event.get("timestamp") if latest_event else None,
        "event_count": len(events)
    })