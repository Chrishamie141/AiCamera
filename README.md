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