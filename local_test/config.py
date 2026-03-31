from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class LocalTestConfig:
    source: str = "webcam"
    path: str | None = None
    camera_index: int = 0
    mock_resolution: tuple[int, int] = (640, 480)
    repeat_images: int = 1
    loop_video: bool = False

    motion_enabled: bool = True
    person_enabled: bool = True
    face_enabled: bool = True
    motion_min_area: int = 1200
    person_confidence: float = 0.5
    cooldown_sec: float = 2.0

    preview: bool = True
    save_snapshots: bool = True
    save_clips: bool = False
    clip_frames_after_event: int = 60
    output_dir: Path = Path("local_test_output")
    run_seconds: float | None = None
    max_frames: int | None = None

    def ensure_dirs(self) -> dict[str, Path]:
        snapshots = self.output_dir / "snapshots"
        clips = self.output_dir / "clips"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        snapshots.mkdir(parents=True, exist_ok=True)
        clips.mkdir(parents=True, exist_ok=True)
        return {"root": self.output_dir, "snapshots": snapshots, "clips": clips}
