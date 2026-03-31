from io import BytesIO
from pathlib import Path

import qrcode
from flask import Blueprint, Response, jsonify, request, send_from_directory

from app.services import repository
from camera.stream import stream_service
from db.db import get_settings, update_settings

api = Blueprint("api", __name__)
ROOT = Path(__file__).resolve().parents[1]


@api.route("/api/health")
@api.route("/api/status")
def health():
    return jsonify({"status": "ok", "camera": stream_service.health()})


@api.route("/api/stream")
def stream():
    return Response(stream_service.generate_frames(get_settings), mimetype="multipart/x-mixed-replace; boundary=frame")


@api.route("/api/events")
def events():
    unresolved_only = request.args.get("unresolved") == "1"
    limit = int(request.args.get("limit", 100))
    return jsonify({"events": repository.list_events(limit=limit, unresolved_only=unresolved_only)})


@api.route("/api/events/<int:event_id>")
def event_detail(event_id: int):
    event = repository.get_event(event_id)
    return (jsonify(event), 200) if event else (jsonify({"error": "not found"}), 404)


@api.route("/api/events/<int:event_id>/confirm", methods=["POST"])
def confirm_event(event_id: int):
    payload = request.get_json(force=True)
    method = payload.get("method", "manual")
    notes = payload.get("notes")
    if method == "qr":
        event = repository.confirm_event_by_qr(event_id, payload["qr_token"], notes)
    elif method == "pin":
        event = repository.confirm_event_by_pin(event_id, payload["pin_code"], notes)
    else:
        event = repository.confirm_event(event_id, payload.get("member_id"), "manual", notes)
    return (jsonify(event), 200) if event else (jsonify({"error": "confirmation failed"}), 400)


@api.route("/api/stats")
def stats():
    return jsonify(repository.stats())


@api.route("/api/snapshots")
def snapshots_list():
    files = sorted((ROOT / "snapshots").glob("*.jpg"), reverse=True)
    return jsonify({"snapshots": [f"snapshots/{f.name}" for f in files[:200]]})


@api.route("/api/recordings")
def recordings_list():
    files = sorted((ROOT / "recordings").glob("*.mp4"), reverse=True)
    return jsonify({"recordings": [f"recordings/{f.name}" for f in files[:200]]})


@api.route("/api/settings", methods=["GET", "PUT"])
def settings():
    if request.method == "GET":
        return jsonify(get_settings())
    updated = update_settings(request.get_json(force=True))
    return jsonify(updated)


@api.route("/api/members", methods=["GET", "POST"])
def members():
    if request.method == "GET":
        return jsonify({"members": repository.list_members()})
    return jsonify(repository.create_member(request.get_json(force=True))), 201


@api.route("/api/members/<int:member_id>", methods=["PUT", "DELETE"])
def member_detail(member_id: int):
    if request.method == "DELETE":
        return ("", 204) if repository.delete_member(member_id) else (jsonify({"error": "not found"}), 404)
    updated = repository.update_member(member_id, request.get_json(force=True))
    return (jsonify(updated), 200) if updated else (jsonify({"error": "not found"}), 404)


@api.route("/api/members/<int:member_id>/qr")
def member_qr(member_id: int):
    member = repository.get_member(member_id)
    if not member:
        return jsonify({"error": "not found"}), 404
    image = qrcode.make(member["qr_token"])
    buf = BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")


@api.route("/snapshots/<path:filename>")
def snapshots(filename):
    return send_from_directory("snapshots", filename)


@api.route("/recordings/<path:filename>")
def recordings(filename):
    return send_from_directory("recordings", filename)
