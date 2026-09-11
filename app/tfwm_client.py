import io
import time
import logging
from pathlib import Path

import requests
import pandas as pd

from .config import (
    TFWM_APP_ID,
    TFWM_APP_KEY,
    VEHICLE_POSITIONS_URL,
    TRIP_UPDATES_URL,
    LIVE_DIR,
)

logger = logging.getLogger(__name__)


class TfwmClient:
    """
    Server-side TfWM GTFS-RT client.

    Credentials are read only from environment variables.
    They are never sent to the browser.
    """

    def __init__(self):
        self.vehicle_positions = pd.DataFrame()
        self.trip_updates = pd.DataFrame()
        self.last_vehicle_refresh = None
        self.last_trip_refresh = None

    @property
    def configured(self):
        return bool(TFWM_APP_ID and TFWM_APP_KEY)

    def _params(self):
        return {
            "app_id": TFWM_APP_ID,
            "app_key": TFWM_APP_KEY,
        }

    def _get(self, url):
        if not self.configured:
            raise RuntimeError(
                "TfWM credentials are not configured. "
                "Set TFWM_APP_ID and TFWM_APP_KEY."
            )

        response = requests.get(
            url,
            params=self._params(),
            timeout=30,
        )

        response.raise_for_status()
        return response.content

    def refresh_vehicle_positions(self):
        """
        Download current GTFS-RT vehicle positions.

        The precise GTFS-RT protobuf decoding used in the Kaggle
        research notebook is intentionally not recreated here.
        This method provides the production refresh boundary.

        If protobuf decoding is available, decode it.
        Otherwise retain the last successful state.
        """

        try:
            raw = self._get(VEHICLE_POSITIONS_URL)

            # Try gtfs-realtime-bindings first.
            try:
                from google.transit import gtfs_realtime_pb2

                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(raw)

                records = []

                for entity in feed.entity:
                    if not entity.HasField("vehicle"):
                        continue

                    vehicle = entity.vehicle

                    row = {
                        "entity_id": entity.id,
                        "vehicle_id": (
                            vehicle.vehicle.id
                            if vehicle.HasField("vehicle")
                            else None
                        ),
                        "trip_id": (
                            vehicle.trip.trip_id
                            if vehicle.HasField("trip")
                            else None
                        ),
                        "route_id": (
                            vehicle.trip.route_id
                            if vehicle.HasField("trip")
                            else None
                        ),
                        "latitude": (
                            vehicle.position.latitude
                            if vehicle.HasField("position")
                            else None
                        ),
                        "longitude": (
                            vehicle.position.longitude
                            if vehicle.HasField("position")
                            else None
                        ),
                        "bearing": (
                            vehicle.position.bearing
                            if vehicle.HasField("position")
                            else None
                        ),
                        "speed": (
                            vehicle.position.speed
                            if vehicle.HasField("position")
                            else None
                        ),
                        "current_stop_sequence": (
                            vehicle.current_stop_sequence
                            if vehicle.HasField("current_stop_sequence")
                            else None
                        ),
                        "current_status": (
                            vehicle.current_status
                            if vehicle.HasField("current_status")
                            else None
                        ),
                    }

                    records.append(row)

                if records:
                    self.vehicle_positions = pd.DataFrame(records)

                    LIVE_DIR.mkdir(parents=True, exist_ok=True)

                    self.vehicle_positions.to_csv(
                        LIVE_DIR / "vehicle_positions_production_latest.csv",
                        index=False,
                    )

                    self.last_vehicle_refresh = time.time()

                    return self.vehicle_positions

            except Exception as decode_error:
                logger.warning(
                    "Vehicle protobuf decoding unavailable: %s",
                    decode_error,
                )

        except Exception as exc:
            logger.warning(
                "Vehicle positions refresh failed: %s",
                exc,
            )

        return self.vehicle_positions

    def refresh_trip_updates(self):
        """
        Download current GTFS-RT trip updates.
        """

        try:
            raw = self._get(TRIP_UPDATES_URL)

            try:
                from google.transit import gtfs_realtime_pb2

                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(raw)

                records = []

                for entity in feed.entity:
                    if not entity.HasField("trip_update"):
                        continue

                    update = entity.trip_update

                    trip_id = (
                        update.trip.trip_id
                        if update.HasField("trip")
                        else None
                    )

                    route_id = (
                        update.trip.route_id
                        if update.HasField("trip")
                        else None
                    )

                    for stop_update in update.stop_time_update:
                        arrival_delay = None
                        departure_delay = None

                        if stop_update.HasField("arrival"):
                            if stop_update.arrival.HasField("delay"):
                                arrival_delay = stop_update.arrival.delay

                        if stop_update.HasField("departure"):
                            if stop_update.departure.HasField("delay"):
                                departure_delay = stop_update.departure.delay

                        records.append({
                            "entity_id": entity.id,
                            "trip_id": trip_id,
                            "route_id": route_id,
                            "stop_id": (
                                stop_update.stop_id
                                if stop_update.HasField("stop_id")
                                else None
                            ),
                            "stop_sequence": (
                                stop_update.stop_sequence
                                if stop_update.HasField("stop_sequence")
                                else None
                            ),
                            "arrival_delay_sec": arrival_delay,
                            "departure_delay_sec": departure_delay,
                        })

                if records:
                    self.trip_updates = pd.DataFrame(records)

                    LIVE_DIR.mkdir(parents=True, exist_ok=True)

                    self.trip_updates.to_csv(
                        LIVE_DIR / "trip_updates_production_latest.csv",
                        index=False,
                    )

                    self.last_trip_refresh = time.time()

                    return self.trip_updates

            except Exception as decode_error:
                logger.warning(
                    "Trip-update protobuf decoding unavailable: %s",
                    decode_error,
                )

        except Exception as exc:
            logger.warning(
                "Trip updates refresh failed: %s",
                exc,
            )

        return self.trip_updates

    def refresh_all(self):
        self.refresh_vehicle_positions()
        self.refresh_trip_updates()

        return {
            "vehicle_records": len(self.vehicle_positions),
            "trip_update_records": len(self.trip_updates),
            "vehicle_refresh": self.last_vehicle_refresh,
            "trip_refresh": self.last_trip_refresh,
        }


tfwm_client = TfwmClient()
