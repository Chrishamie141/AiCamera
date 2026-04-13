import os
import cv2
import logging
import face_recognition

LOGGER = logging.getLogger(__name__)

class FaceRecognizer:
    def __init__(self, known_faces_dir="known_faces"):
        self.known_encodings = []
        self.known_names = []
        # Look for known_faces in the root project directory
        self.known_faces_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), known_faces_dir)
        self._load_known_faces()

    def _load_known_faces(self):
        """Loads and encodes images from the known_faces directory on startup."""
        if not os.path.exists(self.known_faces_dir):
            os.makedirs(self.known_faces_dir)
            LOGGER.warning(f"Created {self.known_faces_dir} folder. Add .jpg images here.")
            return

        for filename in os.listdir(self.known_faces_dir):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
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

    def recognize(self, frame, haar_box):
        """
        Takes a frame and a Haar cascade bounding box (x, y, w, h).
        Expands the box slightly to ensure the whole face is caught, 
        then returns the recognized name.
        """
        if not self.known_encodings:
            return "Unknown"

        x, y, w, h = haar_box
        
        # 1. Sanity check: If the face is too small, it will be too blurry to encode
        if w < 50 or h < 50:
            return "Unknown"

        # 2. Expand the box by 20% to capture chin to hairline reliably
        frame_height, frame_width = frame.shape[:2]
        pad_w = int(w * 0.2)
        pad_h = int(h * 0.2)

        new_x = max(0, x - pad_w)
        new_y = max(0, y - pad_h)
        new_w = min(frame_width - new_x, w + (pad_w * 2))
        new_h = min(frame_height - new_y, h + (pad_h * 2))

        # Convert to face_recognition format: (top, right, bottom, left)
        css_box = (new_y, new_x + new_w, new_y + new_h, new_x)

        # 3. Convert OpenCV BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 4. Get encoding for the specific expanded box
        encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=[css_box])

        if not encodings:
            return "Unknown"

        face_encoding = encodings[0]

        # 5. Compare to known faces (Tolerance 0.55 is a bit strict to prevent false positives)
        matches = face_recognition.compare_faces(self.known_encodings, face_encoding, tolerance=0.55)
        
        if True in matches:
            first_match_index = matches.index(True)
            return self.known_names[first_match_index]

        return "Unknown"
