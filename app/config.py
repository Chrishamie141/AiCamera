import os


class Config:
    """
    Global application configuration.
    """

    # =========================
    # Flask / Server Settings
    # =========================
    STREAM_PORT = int(os.getenv("STREAM_PORT", 5000))
    DEBUG = bool(int(os.getenv("DEBUG", 1)))

    # =========================
    # Camera Settings
    # =========================
    CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", 1280))
    CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", 720))
    CAMERA_FPS = int(os.getenv("CAMERA_FPS", 30))

    # =========================
    # Motion Detection Settings
    # (used later)
    # =========================
    MOTION_THRESHOLD = int(os.getenv("MOTION_THRESHOLD", 5000))
    BLUR_SIZE = int(os.getenv("BLUR_SIZE", 21))

    # =========================
    # Database (future)
    # =========================
    DATABASE_PATH = os.getenv(
        "DATABASE_PATH",
        os.path.join(os.getcwd(), "backend", "db", "events.db")
    )

    # =========================
    # Environment
    # =========================
    ENV = os.getenv("ENV", "development")
