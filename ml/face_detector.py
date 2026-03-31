import cv2


class FaceDetector:
    def __init__(self, scale_factor: float = 1.1, min_neighbors: int = 5):
        cascade = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(cascade)
        if self.detector.empty():
            raise RuntimeError("Failed to load Haar cascade for face detection")
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(gray, scaleFactor=self.scale_factor, minNeighbors=self.min_neighbors)
        return [
            {"x1": int(x), "y1": int(y), "x2": int(x + w), "y2": int(y + h), "confidence": 1.0}
            for (x, y, w, h) in faces
        ]
