from __future__ import annotations

import argparse
from pathlib import Path

from local_test.config import LocalTestConfig
from local_test.runner import LocalTestRunner


def parse_args():
    parser = argparse.ArgumentParser(description="Run isolated local laptop test harness")
    parser.add_argument("--source", choices=["webcam", "video", "images", "mock"], default="webcam")
    parser.add_argument("--path", help="Video file path or image folder path")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--repeat-images", type=int, default=1)
    parser.add_argument("--loop-video", action="store_true")
    parser.add_argument("--mock-width", type=int, default=640)
    parser.add_argument("--mock-height", type=int, default=480)

    parser.add_argument("--motion-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--person-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--face-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--motion-threshold", type=int)
    parser.add_argument("--person-confidence", type=float)
    parser.add_argument("--cooldown-sec", type=float)

    parser.add_argument("--preview", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--save-snapshots", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--save-clips", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--clip-frames-after-event", type=int, default=60)
    parser.add_argument("--run-seconds", type=float)
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--output-dir", default="local_test_output")

    parser.add_argument("--performance-mode", choices=["low-power", "balanced", "high-accuracy"], default="balanced")
    return parser.parse_args()


def mode_overrides(mode: str):
    if mode == "low-power":
        return {"cooldown_sec": 3.5, "person_confidence": 0.6, "motion_min_area": 1600}
    if mode == "high-accuracy":
        return {"cooldown_sec": 0.7, "person_confidence": 0.35, "motion_min_area": 800}
    return {"cooldown_sec": 2.0, "person_confidence": 0.5, "motion_min_area": 1200}


def main():
    args = parse_args()
    overrides = mode_overrides(args.performance_mode)

    config = LocalTestConfig(
        source=args.source,
        path=args.path,
        camera_index=args.camera_index,
        repeat_images=args.repeat_images,
        loop_video=args.loop_video,
        mock_resolution=(args.mock_width, args.mock_height),
        motion_enabled=args.motion_enabled,
        person_enabled=args.person_enabled,
        face_enabled=args.face_enabled,
        motion_min_area=args.motion_threshold if args.motion_threshold else overrides["motion_min_area"],
        person_confidence=args.person_confidence if args.person_confidence else overrides["person_confidence"],
        cooldown_sec=args.cooldown_sec if args.cooldown_sec else overrides["cooldown_sec"],
        preview=args.preview,
        save_snapshots=args.save_snapshots,
        save_clips=args.save_clips,
        clip_frames_after_event=args.clip_frames_after_event,
        output_dir=Path(args.output_dir),
        run_seconds=args.run_seconds,
        max_frames=args.max_frames,
    )

    runner = LocalTestRunner(config)
    runner.run()


if __name__ == "__main__":
    main()
