import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Config:
    HOST = os.getenv("APP_HOST", "0.0.0.0")
    PORT = int(os.getenv("APP_PORT", "5000"))
    DB_PATH = ROOT / "db" / "events.db"
    SNAPSHOT_DIR = ROOT / "snapshots"
    RECORDING_DIR = ROOT / "recordings"
