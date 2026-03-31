import logging
import time
from dataclasses import dataclass

import cv2

try:
    from picamera2 import Picamera2
except Exception:  # pragma: no cover
    Picamera2 = None

LOGGER = logging.getLogger(__name__)


@dataclass
class CaptureProfile:
    width: int
    height: int
    fps: int


PROFILES = {
    "low-power": CaptureProfile(640, 360, 12),
    "balanced": CaptureProfile(960, 540, 18),
    "high-accuracy": CaptureProfile(1280, 720, 24),
}


class CameraController:
    def __init__(self, profile: str = "balanced", fallback_index: int = 0):
        self.profile_name = profile if profile in PROFILES else "balanced"
        self.profile = PROFILES[self.profile_name]
        self.fallback_index = fallback_index
        self.picam2 = None
        self.cv_cap = None
        self.active_path = None
        self.last_error = None
        self._open_camera()

    def _open_camera(self) -> None:
        if Picamera2 is not None:
            try:
                self.picam2 = Picamera2()
                config = self.picam2.create_preview_configuration(
                    main={"size": (self.profile.width, self.profile.height), "format": "RGB888"},
                    controls={"FrameRate": self.profile.fps},
                )
                self.picam2.configure(config)
                self.picam2.start()
                time.sleep(1)
                self.active_path = "picamera2"
                LOGGER.info("Initialized Picamera2 capture profile=%s", self.profile_name)
                return
            except Exception as exc:  # pragma: no cover
                self.last_error = str(exc)
                LOGGER.warning("Picamera2 unavailable, falling back to OpenCV: %s", exc)

        self.cv_cap = cv2.VideoCapture(self.fallback_index)
        self.cv_cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.profile.width)
        self.cv_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.profile.height)
        self.cv_cap.set(cv2.CAP_PROP_FPS, self.profile.fps)
        if not self.cv_cap.isOpened():
            raise RuntimeError(f"No camera source available (Picamera2 error: {self.last_error})")
        self.active_path = "opencv"

    def get_frame(self):
        if self.picam2 is not None:
            frame_rgb = self.picam2.capture_array()
            if frame_rgb is None:
                raise RuntimeError("Picamera2 returned empty frame")
            return cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        ok, frame = self.cv_cap.read()
        if not ok or frame is None:
            raise RuntimeError("OpenCV fallback returned empty frame")
        return frame

    def health(self) -> dict:
        return {
            "active_path": self.active_path,
            "profile": self.profile_name,
            "resolution": [self.profile.width, self.profile.height],
            "fps": self.profile.fps,
            "last_error": self.last_error,
        }

    def stop(self) -> None:
        if self.picam2 is not None:
            self.picam2.stop()
            self.picam2.close()
            self.picam2 = None
        if self.cv_cap is not None:
            self.cv_cap.release()
            self.cv_cap = None
