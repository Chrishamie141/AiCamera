from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import cv2

from local_test.config import LocalTestConfig
from local_test.sink import LocalEvent, LocalEventSink
from local_test.sources import build_source
from ml.inference import DetectionSettings, InferenceEngine


@dataclass
class RuntimeStats:
    frames_processed: int = 0
    motion_events: int = 0
    person_detections: int = 0
    face_detections: int = 0


class LocalTestRunner:
    def __init__(self, config: LocalTestConfig):
        self.config = config
        dirs = self.config.ensure_dirs()
        self.snapshot_dir = dirs["snapshots"]
        self.clip_dir = dirs["clips"]
        self.sink = LocalEventSink(dirs["root"])
        self.stats = RuntimeStats()
        self.engine = InferenceEngine(
            DetectionSettings(
                motion_enabled=config.motion_enabled,
                person_enabled=config.person_enabled,
                face_enabled=config.face_enabled,
                motion_min_area=config.motion_min_area,
                person_confidence=config.person_confidence,
                cooldown_sec=config.cooldown_sec,
            )
        )
        self.source = build_source(
            source=config.source,
            path=config.path,
            camera_index=config.camera_index,
            repeat_images=config.repeat_images,
            loop_video=config.loop_video,
            mock_resolution=config.mock_resolution,
        )
        self.clip_writer = None
        self.clip_frames_left = 0
        self.last_event_id = None

    def run(self):
        started = time.time()
        try:
            if self.config.preview:
                cv2.namedWindow("Local Test Preview", cv2.WINDOW_NORMAL)
            while True:
                ok, frame, frame_info = self.source.read()
                if not ok or frame is None:
                    break
                self.stats.frames_processed += 1

                result = self.engine.process(frame)
                self._accumulate(result)

                event_created = self._maybe_create_event(frame, result, frame_info)
                annotated = self._annotate(frame.copy(), result, event_created)
                self._handle_clip(annotated)

                if self.config.preview:
                    cv2.imshow("Local Test Preview", annotated)
                    if cv2.getWindowProperty("Local Test Preview", cv2.WND_PROP_VISIBLE) < 1:
                        break
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord("q"), 27):
                        break

                if self.config.max_frames and self.stats.frames_processed >= self.config.max_frames:
                    break
                if self.config.run_seconds and time.time() - started >= self.config.run_seconds:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self._print_summary()
            self._shutdown()

    def _accumulate(self, result: dict):
        if result.get("motion_detected"):
            self.stats.motion_events += 1
        self.stats.person_detections += len(result.get("person_boxes", []))
        self.stats.face_detections += len(result.get("face_boxes", []))

    def _maybe_create_event(self, frame, result: dict, frame_info: dict) -> bool:
        detection_type = None
        confidence = 0.0
        if result.get("person_boxes"):
            detection_type = "person"
            confidence = max(b.get("confidence", 0.0) for b in result["person_boxes"])
        elif result.get("face_boxes"):
            detection_type = "face"
            confidence = 1.0

        if not detection_type:
            return False

        ts = datetime.now(timezone.utc).isoformat()
        snapshot_path = None
        if self.config.save_snapshots:
            snapshot_path = self._save_snapshot(frame, ts)

        event = LocalEvent(
            timestamp=ts,
            event_type="arrival",
            detection_type=detection_type,
            confidence=round(float(confidence), 3),
            status="pending",
            snapshot_path=str(snapshot_path) if snapshot_path else None,
            clip_path=None,
            metadata={
                "motion_detected": result.get("motion_detected", False),
                "motion_area": result.get("motion_area", 0),
                "person_boxes": result.get("person_boxes", []),
                "face_boxes": result.get("face_boxes", []),
                "qr_tokens": result.get("qr_tokens", []),
                "frame_info": frame_info,
            },
        )
        event_id = self.sink.create_pending_event(event)
        self.last_event_id = event_id

        if self.config.save_clips:
            self._start_clip(frame.shape[1], frame.shape[0], event_id)

        qr_tokens = result.get("qr_tokens", [])
        if qr_tokens:
            self.sink.confirm_event(event_id, method="qr", notes=f"tokens={qr_tokens}")
        return True

    def _save_snapshot(self, frame, timestamp: str) -> Path:
        safe_ts = timestamp.replace(":", "-").replace(".", "-")
        filename = self.snapshot_dir / f"event_{safe_ts}.jpg"
        cv2.imwrite(str(filename), frame)
        return filename

    def _annotate(self, frame, result: dict, event_created: bool):
        for box in result.get("person_boxes", []):
            cv2.rectangle(frame, (box["x1"], box["y1"]), (box["x2"], box["y2"]), (0, 200, 0), 2)
            cv2.putText(
                frame,
                f"person {box.get('confidence', 0):.2f}",
                (box["x1"], max(10, box["y1"] - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 200, 0),
                1,
            )
        for box in result.get("face_boxes", []):
            cv2.rectangle(frame, (box["x1"], box["y1"]), (box["x2"], box["y2"]), (255, 180, 0), 2)
            cv2.putText(frame, "face", (box["x1"], max(10, box["y1"] - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 180, 0), 1)

        status = f"motion={result.get('motion_detected')} event={'yes' if event_created else 'no'}"
        cv2.putText(frame, status, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        return frame

    def _start_clip(self, width: int, height: int, event_id: int):
        if self.clip_writer is not None:
            self.clip_writer.release()
        clip_path = self.clip_dir / f"event_{event_id}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.clip_writer = cv2.VideoWriter(str(clip_path), fourcc, 15.0, (width, height))
        self.clip_frames_left = max(1, int(self.config.clip_frames_after_event))

    def _handle_clip(self, frame):
        if self.clip_writer is None:
            return
        self.clip_writer.write(frame)
        self.clip_frames_left -= 1
        if self.clip_frames_left <= 0:
            self.clip_writer.release()
            self.clip_writer = None

    def _shutdown(self):
        self.source.release()
        if self.clip_writer is not None:
            self.clip_writer.release()
        self.sink.close()
        if self.config.preview:
            cv2.destroyAllWindows()

    def _print_summary(self):
        db_counts = self.sink.summary_counts()
        print("\n=== Local Test Summary ===")
        print(f"Frames processed   : {self.stats.frames_processed}")
        print(f"Motion events      : {self.stats.motion_events}")
        print(f"Person detections  : {self.stats.person_detections}")
        print(f"Face detections    : {self.stats.face_detections}")
        print(f"Pending arrivals   : {db_counts['pending_arrivals']}")
        print(f"Confirmed arrivals : {db_counts['confirmed_arrivals']}")
        print(f"Total events       : {db_counts['total_events']}")
        print(f"Output directory   : {self.config.output_dir.resolve()}")
