from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np


class FrameSource(ABC):
    @abstractmethod
    def read(self) -> tuple[bool, np.ndarray | None, dict]:
        raise NotImplementedError

    def release(self) -> None:
        return None


class WebcamSource(FrameSource):
    def __init__(self, camera_index: int = 0):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Unable to open webcam index {camera_index}")

    def read(self):
        ok, frame = self.cap.read()
        return ok, frame, {"source": "webcam"}

    def release(self) -> None:
        self.cap.release()


class VideoFileSource(FrameSource):
    def __init__(self, path: str, loop: bool = False):
        self.path = str(path)
        self.loop = loop
        self.cap = cv2.VideoCapture(self.path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Unable to open video file {self.path}")

    def read(self):
        ok, frame = self.cap.read()
        if ok:
            return True, frame, {"source": "video", "path": self.path}
        if not self.loop:
            return False, None, {"source": "video", "path": self.path}
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = self.cap.read()
        return ok, frame, {"source": "video", "path": self.path, "looped": True}

    def release(self) -> None:
        self.cap.release()


class ImageFolderSource(FrameSource):
    def __init__(self, path: str, repeat_images: int = 1):
        root = Path(path)
        if not root.exists() or not root.is_dir():
            raise RuntimeError(f"Image folder does not exist: {path}")
        image_ext = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        self.images = sorted([p for p in root.iterdir() if p.suffix.lower() in image_ext])
        if not self.images:
            raise RuntimeError(f"No supported images found in {path}")
        self.repeat_images = max(1, int(repeat_images))
        self.index = 0
        self.repeat_index = 0

    def read(self):
        if self.index >= len(self.images):
            return False, None, {"source": "images"}
        image_path = self.images[self.index]
        frame = cv2.imread(str(image_path))
        if frame is None:
            self.index += 1
            self.repeat_index = 0
            return self.read()

        self.repeat_index += 1
        if self.repeat_index >= self.repeat_images:
            self.index += 1
            self.repeat_index = 0
        return True, frame, {"source": "images", "path": str(image_path)}


class MockSource(FrameSource):
    def __init__(self, resolution: tuple[int, int] = (640, 480)):
        self.width, self.height = resolution
        self.step = 0

    def read(self):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        x = (self.step * 7) % max(50, self.width - 100)
        cv2.rectangle(frame, (x, 80), (x + 90, 300), (255, 255, 255), -1)
        cv2.putText(frame, f"MOCK {self.step}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        self.step += 1
        return True, frame, {"source": "mock", "frame": self.step}


def build_source(source: str, path: str | None, camera_index: int, repeat_images: int, loop_video: bool, mock_resolution):
    source = source.lower().strip()
    if source == "webcam":
        return WebcamSource(camera_index=camera_index)
    if source == "video":
        if not path:
            raise ValueError("--path is required for source=video")
        return VideoFileSource(path=path, loop=loop_video)
    if source == "images":
        if not path:
            raise ValueError("--path is required for source=images")
        return ImageFolderSource(path=path, repeat_images=repeat_images)
    if source == "mock":
        return MockSource(resolution=mock_resolution)
    raise ValueError(f"Unsupported source '{source}'")
