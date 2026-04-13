import logging
import time
from dataclasses import dataclass

import cv2

try:
    from picamera2 import Picamera2
except Exception:
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
        if Picamera2 is None:
            raise RuntimeError("Picamera2 is not installed or could not be imported")

        try:
            self.picam2 = Picamera2()

            config = self.picam2.create_video_configuration(
                main={
                    "size": (self.profile.width, self.profile.height),
                    "format": "RGB888",
                },
                controls={
                    "FrameRate": self.profile.fps,
                },
                buffer_count=4,
            )

            self.picam2.configure(config)
            self.picam2.start()
            time.sleep(2)

            frame = self.picam2.capture_array()
            if frame is None or getattr(frame, "size", 0) == 0:
                raise RuntimeError("Picamera2 started but returned empty frame")

            self.active_path = "picamera2"
            self.last_error = None
            LOGGER.info(
                "Initialized Picamera2 capture profile=%s resolution=%sx%s fps=%s",
                self.profile_name,
                self.profile.width,
                self.profile.height,
                self.profile.fps,
            )

        except Exception as exc:
            self.last_error = str(exc)
            LOGGER.exception("Picamera2 initialization failed")

            if self.picam2 is not None:
                try:
                    self.picam2.stop()
                except Exception:
                    pass
                try:
                    self.picam2.close()
                except Exception:
                    pass
                self.picam2 = None

            raise RuntimeError(f"Picamera2 failed to initialize: {exc}")

    def get_frame(self):
        if self.picam2 is None:
            raise RuntimeError("No active Picamera2 source")

        try:
            frame_rgb = self.picam2.capture_array()
            if frame_rgb is None or getattr(frame_rgb, "size", 0) == 0:
                raise RuntimeError("Picamera2 returned empty frame")
            return cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        except Exception as exc:
            self.last_error = str(exc)
            raise RuntimeError(f"Picamera2 capture failed: {exc}")

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
            try:
                self.picam2.stop()
            except Exception:
                pass
            try:
                self.picam2.close()
            except Exception:
                pass
            self.picam2 = None

        if self.cv_cap is not None:
            self.cv_cap.release()
            self.cv_cap = None
