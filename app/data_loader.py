import pandas as pd
from pathlib import Path

from .config import STATIC_DIR


class StaticData:
    """
    Loads static GTFS-derived tables once when the server starts.
    """

    def __init__(self):
        self.stops = self._load("stops_clean.csv")
        self.routes = self._load("routes_clean.csv")
        self.trips = self._load("trips_clean.csv")
        self.schedule = self._load("schedule_data.csv")

    @staticmethod
    def _load(filename):
        path = STATIC_DIR / filename

        # Large schedule data is stored as gzip to remain
        # deployment/GitHub friendly.
        if filename == "schedule_data.csv":
            compressed_path = STATIC_DIR / "schedule_data.csv.gz"

            if compressed_path.exists():
                return pd.read_csv(
                    compressed_path,
                    compression="gzip",
                    low_memory=False
                )

        if not path.exists():
            raise FileNotFoundError(
                f"Required static GTFS file not found: {path}"
            )

        return pd.read_csv(
            path,
            low_memory=False
        )


static_data = StaticData()
