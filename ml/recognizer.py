import os
import cv2
import logging
import face_recognition

LOGGER = logging.getLogger(__name__)


class FaceRecognizer:
    def __init__(self, known_faces_dir="known_faces"):
        self.known_encodings = []
        self.known_names = []
        self.known_faces_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            known_faces_dir,
        )
        self._load_known_faces()

    def _load_known_faces(self):
        if not os.path.exists(self.known_faces_dir):
            os.makedirs(self.known_faces_dir)
            LOGGER.warning(f"Created {self.known_faces_dir} folder. Add .jpg images here.")
            return

        for filename in os.listdir(self.known_faces_dir):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            name = os.path.splitext(filename)[0]
            filepath = os.path.join(self.known_faces_dir, filename)

            try:
                image = face_recognition.load_image_file(filepath)
                encodings = face_recognition.face_encodings(image)

                if encodings:
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(name)
                    LOGGER.info(f"Loaded known face: {name}")
                else:
                    LOGGER.warning(f"No face found in {filename}")
            except Exception as e:
                LOGGER.error(f"Failed to load {filename}: {e}")

    def _normalize_box(self, box):
        """
        Accepts either:
        - dict format: {"x1":..,"y1":..,"x2":..,"y2":..}
        - tuple/list format: (x, y, w, h)
        - tuple/list format: (x1, y1, x2, y2)
        Returns: (x, y, w, h)
        """
        if isinstance(box, dict):
            if all(k in box for k in ("x1", "y1", "x2", "y2")):
                x1 = int(box["x1"])
                y1 = int(box["y1"])
                x2 = int(box["x2"])
                y2 = int(box["y2"])
                return x1, y1, max(0, x2 - x1), max(0, y2 - y1)
            raise ValueError(f"Unsupported box dict format: {box}")

        if isinstance(box, (list, tuple)):
            if len(box) < 4:
                raise ValueError(f"Box does not have enough values: {box}")

            a, b, c, d = map(int, box[:4])

            # Heuristic:
            # if c > a and d > b, treat as (x1, y1, x2, y2)
            # otherwise treat as (x, y, w, h)
            if c > a and d > b:
                return a, b, c - a, d - b

            return a, b, c, d

        raise ValueError(f"Unsupported box type: {type(box)}")

    def recognize(self, frame, face_box):
        """
        Takes a frame and a face bounding box.
        Supports dict boxes from your face detector:
        {"x1","y1","x2","y2","confidence"}
        """
        if not self.known_encodings:
            return "Unknown"

        try:
            x, y, w, h = self._normalize_box(face_box)
        except Exception as e:
            LOGGER.error(f"Invalid face box passed to recognizer: {e}")
            return "Unknown"

        if w < 50 or h < 50:
            return "Unknown"

        frame_height, frame_width = frame.shape[:2]
        pad_w = int(w * 0.2)
        pad_h = int(h * 0.2)

        new_x = max(0, x - pad_w)
        new_y = max(0, y - pad_h)
        new_w = min(frame_width - new_x, w + (pad_w * 2))
        new_h = min(frame_height - new_y, h + (pad_h * 2))

        top = new_y
        right = new_x + new_w
        bottom = new_y + new_h
        left = new_x

        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(
                rgb_frame,
                known_face_locations=[(top, right, bottom, left)],
            )

            if not encodings:
                return "Unknown"

            face_encoding = encodings[0]
            matches = face_recognition.compare_faces(
                self.known_encodings,
                face_encoding,
                tolerance=0.55,
            )

            if True in matches:
                first_match_index = matches.index(True)
                return self.known_names[first_match_index]

            return "Unknown"

        except Exception as e:
            LOGGER.error(f"Face recognition failed: {e}")
            return "Unknown"
