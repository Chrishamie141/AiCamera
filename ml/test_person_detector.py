import numpy as np

from ml.person_detector import PersonDetector


def test_detector_empty_frame():
    detector = PersonDetector()
    frame = np.zeros((300, 300, 3), dtype=np.uint8)
    boxes = detector.detect(frame)
    assert isinstance(boxes, list)
