import time
import cv2
from picamera2 import Picamera2


class CameraController:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        self.picam2 = None
        self.active_path = "picamera2"
        self._open_camera()

    def _open_camera(self):
        if self.picam2 is not None:
            return

        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(1)

    def get_frame(self):
        if self.picam2 is None:
            self._open_camera()

        frame_rgb = self.picam2.capture_array()
        if frame_rgb is None:
            raise RuntimeError("Failed to capture frame from Pi camera")

        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        return frame_bgr

    def get_active_path(self):
        return self.active_path

    def stop(self):
        if self.picam2 is not None:
            self.picam2.stop()
            self.picam2.close()
            self.picam2 = None