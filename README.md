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

## Raspberry Pi 5 setup (install all requirements)

### 1) Enable camera interface
```bash
sudo raspi-config
```
Then go to **Interface Options → Camera → Enable**, and reboot.

### 2) Install system packages
```bash
sudo apt update
sudo apt install -y \
  python3-venv python3-dev build-essential libcap-dev \
  libzbar0 git curl
```

### 3) Install Node.js (for frontend)
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node -v
npm -v
```

### 4) Create Python virtual environment
From the repo root (`AiCamera/`):
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 5) Install Python dependencies
```bash
pip install -r requirements.txt
```
Optional dev tools:
```bash
pip install -r requirements-dev.txt
```

### 6) Install frontend dependencies
```bash
cd frontend
npm install
cd ..
```

### 7) Configure environment
```bash
cp .env.example .env
```
Edit `.env` as needed (defaults are usually fine to start):
- `APP_HOST=0.0.0.0`
- `APP_PORT=5000`
- `CAMERA_PROFILE=balanced`

## Run backend + frontend

You can run in **production style** (single Flask server serving built frontend) or **dev style** (separate backend/frontend terminals).

### Option A: Production style (recommended on Pi)
1. Build frontend:
   ```bash
   cd frontend
   npm run build
   cd ..
   ```
2. Start backend (serves API + dashboard):
   ```bash
   source .venv/bin/activate
   python -m app.main
   ```
3. Open in browser:
   - Dashboard: `http://<PI_IP>:5000/dashboard`
   - API health: `http://<PI_IP>:5000/api/health`

### Option B: Dev style (two terminals)
Terminal 1 (backend):
```bash
cd /path/to/AiCamera
source .venv/bin/activate
python -m app.main
```

Terminal 2 (frontend):
```bash
cd /path/to/AiCamera/frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

Then open `http://<PI_IP>:5173` for Vite dev UI.

## Quick backend check
```bash
curl http://127.0.0.1:5000/api/health
```
Expected response contains a JSON status payload.

## Local test harness (optional)
For non-Pi testing with webcam/video/mock input:
```bash
python run_local_test.py --source mock --preview --max-frames 300
```

## Troubleshooting
- **`python-prctl` install error**: usually fixed by installing `libcap-dev` + `python3-dev` (see system packages above).
- **No dashboard at `/dashboard`**: run `npm run build` in `frontend/` first, then restart backend.
- **Camera access issues**: re-check `raspi-config` camera setting and reboot.
