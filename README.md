# Raspberry Pi 5 Smart Arrival Camera

Privacy-safe smart arrival/security camera stack for Raspberry Pi 5 + official ribbon camera.

## What it does
- Pi Camera capture with `Picamera2` primary path and OpenCV fallback.
- Motion pre-filter + person detection (MobileNet SSD) + face detection (Haar cascade).
- Arrival event creation with snapshot persistence.
- No facial recognition or identity tracking from face data.
- Identity confirmation via QR token, manual assignment, or PIN confirmation.
- SQLite persistence for events, settings, and members.
- Flask API + React/Vite dashboard.

## Backend API
- `GET /api/health`
- `GET /api/stream` (MJPEG live feed)
- `GET /api/events?limit=100&unresolved=1`
- `GET /api/events/<id>`
- `POST /api/events/<id>/confirm`
- `GET /api/stats`
- `GET|PUT /api/settings`
- `GET|POST /api/members`
- `PUT|DELETE /api/members/<id>`
- `GET /api/members/<id>/qr`
- `GET /snapshots/<filename>`

## Raspberry Pi 5 setup
1. Enable camera: `sudo raspi-config` → Interface Options → Camera.
2. Install system packages:
   ```bash
   sudo apt update
   sudo apt install -y python3-venv libzbar0
   ```
3. Python setup:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Run backend:
   ```bash
   python -m app.main
   ```
5. Frontend (optional dev server):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Deployment notes
- Default profile is `balanced` for Pi 5 stability.
- Tune `/api/settings` to adjust motion/person/face toggles and thresholds.
- Retention is enforced at startup (`retention_days` setting).
- Keep service local-network only behind firewall or reverse proxy auth.

## Architecture summary
- `camera/`: Pi camera controller + stream service.
- `ml/`: person detector, face detector, motion/inference pipeline.
- `app/routes.py`: REST endpoints + stream + QR PNG generation.
- `app/services/repository.py`: event/member persistence and confirmation workflows.
- `db/schema.sql`: SQLite schema for events, members, settings.
- `frontend/`: React dashboard (live feed, pending arrivals, members).


## Local laptop test harness (non-destructive)
A separate local validation path is available and **does not use Flask routes or the React dashboard**. It is designed for Windows/Linux/macOS laptop testing before Pi deployment.

### Run examples
```bash
python run_local_test.py --source webcam
python run_local_test.py --source video --path ./sample.mp4 --no-preview
python run_local_test.py --source images --path ./test_images --repeat-images 5 --max-frames 300
python run_local_test.py --source mock --run-seconds 10 --preview
```

### Useful flags
- `--source webcam|video|images|mock`
- `--path` (required for `video` and `images`)
- `--motion-enabled/--no-motion-enabled`
- `--person-enabled/--no-person-enabled`
- `--face-enabled/--no-face-enabled`
- `--motion-threshold`, `--person-confidence`, `--cooldown-sec`
- `--save-snapshots/--no-save-snapshots`
- `--save-clips/--no-save-clips`
- `--preview/--no-preview`
- `--output-dir`, `--max-frames`, `--run-seconds`
- `--performance-mode low-power|balanced|high-accuracy`

### Output artifacts
The harness writes to `local_test_output/` (or your `--output-dir`):
- `events.sqlite` local event store
- `events.jsonl` newline JSON event log
- `snapshots/` captured snapshots for detections
- `clips/` optional short clips after events when `--save-clips` is enabled

This test harness is intentionally isolated under `local_test/` and does not modify the Pi-specific camera flow.
