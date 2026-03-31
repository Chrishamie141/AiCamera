from pathlib import Path
import cv2
import numpy as np


class PersonDetector:
    CLASSES = [
        "background", "aeroplane", "bicycle", "bird", "boat",
        "bottle", "bus", "car", "cat", "chair",
        "cow", "diningtable", "dog", "horse", "motorbike",
        "person", "pottedplant", "sheep", "sofa",
        "train", "tvmonitor"
    ]

    PERSON_CLASS_ID = 15

    def __init__(
        self,
        prototxt_path="backend/ml/models/MobileNetSSD_deploy.prototxt",
        model_path="backend/ml/models/MobileNetSSD_deploy.caffemodel",
        confidence_threshold=0.5,
        input_size=(300, 300),
    ):
        self.prototxt = Path(prototxt_path)
        self.model = Path(model_path)

        if not self.prototxt.exists():
            raise FileNotFoundError(f"Missing prototxt file: {self.prototxt}")

        if not self.model.exists():
            raise FileNotFoundError(f"Missing caffemodel file: {self.model}")

        self.confidence_threshold = float(confidence_threshold)
        self.input_size = input_size

        self.net = cv2.dnn.readNetFromCaffe(
            str(self.prototxt),
            str(self.model)
        )

    def detect(self, frame):
        """
        Returns:
            detected (bool)
            boxes (list of (x1, y1, x2, y2, confidence))
        """
        if frame is None or frame.size == 0:
            return False, []

        (h, w) = frame.shape[:2]

        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, self.input_size),
            scalefactor=0.007843,
            size=self.input_size,
            mean=127.5
        )

        self.net.setInput(blob)
        detections = self.net.forward()

        boxes = []

        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])
            class_id = int(detections[0, 0, i, 1])

            if confidence < self.confidence_threshold:
                continue

            if class_id != self.PERSON_CLASS_ID:
                continue

            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (x1, y1, x2, y2) = box.astype("int")

            x1 = max(0, min(x1, w - 1))
            y1 = max(0, min(y1, h - 1))
            x2 = max(0, min(x2, w - 1))
            y2 = max(0, min(y2, h - 1))

            if x2 > x1 and y2 > y1:
                boxes.append((x1, y1, x2, y2, confidence))

        return len(boxes) > 0, boxes