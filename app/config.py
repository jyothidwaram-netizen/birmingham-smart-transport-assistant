import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
STATIC_DIR = DATA_DIR / "static"
LIVE_DIR = DATA_DIR / "live"
MODEL_DIR = BASE_DIR / "models"
WEB_DIR = BASE_DIR / "web"

TFWM_APP_ID = os.getenv("TFWM_APP_ID", "").strip()
TFWM_APP_KEY = os.getenv("TFWM_APP_KEY", "").strip()

TFWM_BASE_URL = "http://api.tfwm.org.uk/gtfs"

VEHICLE_POSITIONS_URL = f"{TFWM_BASE_URL}/vehicle_positions"
TRIP_UPDATES_URL = f"{TFWM_BASE_URL}/trip_updates"

REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "60"))

PORT = int(os.getenv("PORT", "8000"))

TIMEZONE = "Europe/London"
