from ml.person_detector import PersonDetector


def test_model_load():
    detector = PersonDetector()
    assert detector.net is not None
