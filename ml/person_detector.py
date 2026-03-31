from pathlib import Path

import cv2
import numpy as np


class PersonDetector:
    PERSON_CLASS_ID = 15

    def __init__(self, confidence_threshold: float = 0.5, input_size=(300, 300)):
        base = Path(__file__).resolve().parent
        self.prototxt = base / "models" / "MobileNetSSD_deploy.prototxt"
        self.model = base / "models" / "MobileNetSSD_deploy.caffemodel"
        if not self.prototxt.exists() or not self.model.exists():
            raise FileNotFoundError(f"Model files missing at {self.prototxt} and/or {self.model}")
        self.confidence_threshold = float(confidence_threshold)
        self.input_size = input_size
        self.net = cv2.dnn.readNetFromCaffe(str(self.prototxt), str(self.model))

    def detect(self, frame):
        if frame is None or frame.size == 0:
            return []
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, self.input_size), 0.007843, self.input_size, 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()
        boxes = []
        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])
            class_id = int(detections[0, 0, i, 1])
            if class_id != self.PERSON_CLASS_ID or confidence < self.confidence_threshold:
                continue
            x1, y1, x2, y2 = (detections[0, 0, i, 3:7] * np.array([w, h, w, h])).astype("int")
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)
            if x2 > x1 and y2 > y1:
                boxes.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "confidence": round(confidence, 3)})
        return boxes
