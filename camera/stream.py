import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2

from app.services import repository
from camera.camera_controller import CameraController
from ml.inference import DetectionSettings, InferenceEngine

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS_DIR = ROOT / "snapshots"
SNAPSHOTS_DIR.mkdir(exist_ok=True)


class StreamService:
    def __init__(self):
        self.camera = None
        self.engine = None
        self.last_status = {"camera": "init"}
        self.last_event_time = 0.0

    def start(self, settings: dict):
        profile = settings.get("profile", "balanced")
        self.camera = CameraController(profile=profile)
        detection_settings = DetectionSettings(
            motion_enabled=settings.get("motion_enabled", True),
            person_enabled=settings.get("person_enabled", True),
            face_enabled=settings.get("face_enabled", True),
            motion_min_area=int(settings.get("motion_min_area", 1200)),
            person_confidence=float(settings.get("person_confidence", 0.6)),
            cooldown_sec=float(settings.get("cooldown_sec", 2.0)),
        )
        self.engine = InferenceEngine(settings=detection_settings)
        self.last_status = {"camera": "running", **self.camera.health()}

    def ensure_started(self, settings: dict):
        if self.camera is None or self.engine is None:
            self.start(settings)

    def generate_frames(self, settings_getter):
        self.ensure_started(settings_getter())

        while True:
            frame = self.camera.get_frame()
            settings = settings_getter()
            result = self.engine.process(frame)

            for box in result["person_boxes"]:
                cv2.rectangle(
                    frame,
                    (box["x1"], box["y1"]),
                    (box["x2"], box["y2"]),
                    (0, 220, 0),
                    2,
                )

            for box in result["face_boxes"]:
                cv2.rectangle(
                    frame,
                    (box["x1"], box["y1"]),
                    (box["x2"], box["y2"]),
                    (255, 200, 0),
                    2,
                )

            motion_ok = result["motion_detected"] and result["motion_area"] > int(
                settings.get("event_motion_min_area", 2000)
            )

            min_box_area = int(settings.get("event_min_box_area", 5000))
            min_confidence = float(settings.get("event_person_confidence", 0.6))

            valid_person_boxes = []
            for b in result["person_boxes"]:
                w = b["x2"] - b["x1"]
                h = b["y2"] - b["y1"]
                area = w * h
                if area >= min_box_area and float(b["confidence"]) >= min_confidence:
                    valid_person_boxes.append(b)

            person_ok = len(valid_person_boxes) > 0
            face_ok = result["face_detected"]

            require_face = bool(settings.get("event_require_face", False))
            if require_face:
                event_needed = motion_ok and person_ok and face_ok
            else:
                event_needed = motion_ok and person_ok

            now = time.time()
            event_cooldown = float(settings.get("event_cooldown_sec", 3.0))

            if event_needed and (now - self.last_event_time > event_cooldown):
                self.last_event_time = now

                snapshot_rel = None
                if settings.get("snapshot_enabled", True):
                    snapshot_rel = self._save_snapshot(frame)

                event_id = repository.create_event(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "event_type": "arrival",
                        "detection_type": "person+face" if face_ok else "person",
                        "confidence": max(
                            [b["confidence"] for b in valid_person_boxes] + [0.0]
                        ),
                        "snapshot_path": snapshot_rel,
                        "metadata": {
                            "motion_detected": result["motion_detected"],
                            "motion_area": result["motion_area"],
                            "person_detected": person_ok,
                            "face_detected": face_ok,
                            "person_boxes": valid_person_boxes,
                            "face_boxes": result["face_boxes"],
                            "qr_tokens": result.get("qr_tokens", []),
                            "recognized_names": result.get("recognized_names", []), # <-- Identity logged here!
                        },
                    }
                )

                # --- NEW: Print a success message to the terminal! ---
                recognized_names = result.get("recognized_names", [])
                if recognized_names:
                    LOGGER.info(f"🔥 BIOMETRIC MATCH: Identity confirmed for {recognized_names} (Event ID: {event_id})")

                for token in result.get("qr_tokens", []):
                    repository.confirm_event_by_qr(
                        event_id, token, "auto-confirmed by live QR scan"
                    )

            ret, buf = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
            )

    def _save_snapshot(self, frame):
        name = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        path = SNAPSHOTS_DIR / name
        cv2.imwrite(str(path), frame)
        return f"snapshots/{name}"

    def health(self):
        return (
            self.last_status
            if self.camera is None
            else {"camera": "running", **self.camera.health()}
        )


stream_service = StreamService()
