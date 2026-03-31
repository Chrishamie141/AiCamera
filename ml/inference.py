import cv2
import time

from backend.ml.person_detector import PersonDetector


class InferenceEngine:
    def __init__(self, min_area=800, cooldown=3, confidence_threshold=0.5):
        self.previous_frame = None
        self.min_area = min_area
        self.cooldown = cooldown
        self.motion_count = 0
        self.last_detection_time = 0
        self.person_detector = PersonDetector(
            confidence_threshold=confidence_threshold
        )

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.previous_frame is None:
            self.previous_frame = gray
            return {
                "frame": frame,
                "motion_detected": False,
                "motion_area": 0,
                "person_detected": False,
                "boxes": []
            }

        frame_delta = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        motion_detected = False
        motion_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
            motion_detected = True
            motion_area = max(motion_area, area)

        self.previous_frame = gray

        if motion_detected:
            self.motion_count += 1

        person_detected = False
        boxes = []

        now = time.time()
        if motion_detected and (now - self.last_detection_time >= self.cooldown):
            try:
                person_detected, boxes = self.person_detector.detect(frame)
                if person_detected:
                    self.last_detection_time = now
            except Exception as e:
                print(f"[INFERENCE ERROR] Person detection failed: {e}")

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

        return {
            "frame": frame,
            "motion_detected": motion_detected,
            "motion_area": motion_area,
            "person_detected": person_detected,
            "boxes": boxes
        }