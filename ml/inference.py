import time
from dataclasses import dataclass

import cv2

from ml.face_detector import FaceDetector
from ml.person_detector import PersonDetector

try:
    from pyzbar.pyzbar import decode as qr_decode
except Exception:  # pragma: no cover
    qr_decode = None


@dataclass
class DetectionSettings:
    motion_enabled: bool = True
    person_enabled: bool = True
    face_enabled: bool = True
    motion_min_area: int = 1200
    person_confidence: float = 0.5
    cooldown_sec: float = 2.0


class InferenceEngine:
    def __init__(self, settings: DetectionSettings):
        self.settings = settings
        self.previous_gray = None
        self.last_inference = 0.0
        self.person_detector = PersonDetector(confidence_threshold=settings.person_confidence)
        self.face_detector = FaceDetector()

    def process(self, frame):
        motion, motion_area = self._motion(frame)
        person_boxes = []
        face_boxes = []
        qr_tokens = []

        if qr_decode is not None:
            qr_tokens = [obj.data.decode("utf-8") for obj in qr_decode(frame)]

        now = time.time()
        should_run = (not self.settings.motion_enabled or motion) and (now - self.last_inference > self.settings.cooldown_sec)
        if should_run:
            if self.settings.person_enabled:
                person_boxes = self.person_detector.detect(frame)
            if self.settings.face_enabled:
                face_boxes = self.face_detector.detect(frame)
            self.last_inference = now

        return {
            "motion_detected": motion,
            "motion_area": motion_area,
            "person_boxes": person_boxes,
            "face_boxes": face_boxes,
            "person_detected": len(person_boxes) > 0,
            "face_detected": len(face_boxes) > 0,
            "qr_tokens": qr_tokens,
        }

    def _motion(self, frame):
        if not self.settings.motion_enabled:
            return False, 0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if self.previous_gray is None:
            self.previous_gray = gray
            return False, 0
        delta = cv2.absdiff(self.previous_gray, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        max_area = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.settings.motion_min_area:
                max_area = max(max_area, int(area))
        self.previous_gray = gray
        return max_area > 0, max_area
