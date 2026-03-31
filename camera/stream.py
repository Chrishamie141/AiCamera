import cv2
import time
import os
from datetime import datetime

from backend.camera.camera_controller import CameraController
from backend.ml.person_detector import PersonDetector
from backend.events.event_logger import log_event

MIN_MOTION_AREA = 800
MOTION_COOLDOWN = 3
BACKGROUND_RESET_INTERVAL = 30
SNAPSHOT_DIR = "backend/snapshots"

os.makedirs(SNAPSHOT_DIR, exist_ok=True)

camera = None
person_detector = PersonDetector(confidence_threshold=0.5)

first_frame = None
last_event_time = 0
last_background_reset = time.time()


def save_snapshot(frame):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"intrusion_{timestamp}.jpg"
    path = os.path.join(SNAPSHOT_DIR, filename)
    cv2.imwrite(path, frame)
    return filename


def generate_frames():
    global first_frame, last_event_time, last_background_reset, camera

    if camera is None:
        try:
            camera = CameraController(width=1280, height=720)
            print(f"[CAMERA] Initialized on {camera.get_active_path()}")
        except Exception as e:
            print(f"[CAMERA ERROR] Failed to initialize Pi camera: {e}")
            return

    while True:
        try:
            frame = camera.get_frame()
        except Exception as e:
            print(f"[STREAM ERROR] Failed to get frame: {e}")
            time.sleep(1)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        now = time.time()

        if first_frame is None:
            first_frame = gray
            last_background_reset = now
            continue

        if now - last_background_reset >= BACKGROUND_RESET_INTERVAL:
            first_frame = gray
            last_background_reset = now

        frame_delta = cv2.absdiff(first_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(
            thresh.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        motion_detected = False
        motion_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < MIN_MOTION_AREA:
                continue
            motion_detected = True
            motion_area = max(motion_area, area)

        boxes = []

        if motion_detected and (now - last_event_time >= MOTION_COOLDOWN):
            try:
                person_detected, boxes = person_detector.detect(frame)

                if person_detected:
                    snapshot = save_snapshot(frame)

                    log_event(
                        event_type="intrusion",
                        snapshot=snapshot,
                        metadata={
                            "people": len(boxes),
                            "motion_area": motion_area,
                            "camera_path": camera.get_active_path()
                        }
                    )

                    last_event_time = now
            except Exception as e:
                print(f"[ML ERROR] Person detection failed: {e}")

        for (x1, y1, x2, y2, conf) in boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"PERSON {conf:.2f}",
                (x1, max(y1 - 10, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )