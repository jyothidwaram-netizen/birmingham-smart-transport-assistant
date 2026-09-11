from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from ..data_loader import static_data
from ..tfwm_client import tfwm_client

TZ = ZoneInfo("Europe/London")


def _normalise(value):
    return str(value).strip().lower()


def _find_stop(name):
    stops = static_data.stops.copy()

    possible_name_columns = [
        "stop_name",
        "name",
    ]

    column = None

    for candidate in possible_name_columns:
        if candidate in stops.columns:
            column = candidate
            break

    if column is None:
        return None

    target = _normalise(name)

    exact = stops[
        stops[column]
        .astype(str)
        .str.lower()
        .eq(target)
    ]

    if not exact.empty:
        return exact.iloc[0]

    partial = stops[
        stops[column]
        .astype(str)
        .str.lower()
        .str.contains(target, na=False)
    ]

    if not partial.empty:
        return partial.iloc[0]

    return None


def _find_direct_schedule(origin, destination):
    """
    Conservative static-schedule fallback.

    Returns direct scheduled journeys when available.
    """

    schedule = static_data.schedule

    required = {
        "trip_id",
        "route_id",
        "stop_id",
        "arrival_time",
        "departure_time",
    }

    if not required.issubset(schedule.columns):
        return []

    origin_row = _find_stop(origin)
    destination_row = _find_stop(destination)

    if origin_row is None or destination_row is None:
        return []

    origin_id = str(
        origin_row.get("stop_id", "")
    )

    destination_id = str(
        destination_row.get("stop_id", "")
    )

    origin_rows = schedule[
        schedule["stop_id"].astype(str).eq(origin_id)
    ]

    destination_rows = schedule[
        schedule["stop_id"].astype(str).eq(destination_id)
    ]

    if origin_rows.empty or destination_rows.empty:
        return []

    origin_trips = set(
        origin_rows["trip_id"].astype(str)
    )

    destination_trips = set(
        destination_rows["trip_id"].astype(str)
    )

    common = origin_trips.intersection(destination_trips)

    if not common:
        return []

    results = []

    for trip_id in common:

        o = origin_rows[
            origin_rows["trip_id"].astype(str).eq(str(trip_id))
        ]

        d = destination_rows[
            destination_rows["trip_id"].astype(str).eq(str(trip_id))
        ]

        if o.empty or d.empty:
            continue

        o_row = o.iloc[0]
        d_row = d.iloc[0]

        try:
            departure = pd.to_datetime(
                o_row["departure_time"],
                format="mixed"
            )

            arrival = pd.to_datetime(
                d_row["arrival_time"],
                format="mixed"
            )

            if arrival < departure:
                continue

            results.append({
                "trip_id": trip_id,
                "route_id": o_row["route_id"],
                "origin": origin,
                "destination": destination,
                "departure_time": str(o_row["departure_time"]),
                "arrival_time": str(d_row["arrival_time"]),
            })

        except Exception:
            continue

    return results


def search_live_journey(origin, destination, route=None):
    """
    Production-safe journey entry point.

    Priority:
      1. live exact-trip matching when live data supports it
      2. conservative scheduled fallback

    Never fabricates a live ETA.
    """

    origin_stop = _find_stop(origin)
    destination_stop = _find_stop(destination)

    if origin_stop is None or destination_stop is None:
        return {
            "success": False,
            "message": (
                "I could not verify one or both stops "
                "from the TfWM stop dataset."
            ),
            "live_verified": False,
            "candidates": [],
        }

    # --------------------------------------------------------
    # LIVE EXACT-TRIP MATCHING
    # --------------------------------------------------------

    vehicles = tfwm_client.vehicle_positions
    trip_updates = tfwm_client.trip_updates

    live_candidates = []

    if (
        not vehicles.empty
        and "trip_id" in vehicles.columns
    ):
        working = vehicles.copy()

        if route and "route_id" in working.columns:
            working = working[
                working["route_id"]
                .astype(str)
                .str.upper()
                .eq(str(route).strip().upper())
            ]

        for _, vehicle in working.iterrows():

            trip_id = str(
                vehicle.get("trip_id", "")
            ).strip()

            if not trip_id:
                continue

            route_id = str(
                vehicle.get("route_id", "")
            ).strip()

            # We require a valid geographic vehicle position.
            try:
                lat = float(vehicle.get("latitude"))
                lon = float(vehicle.get("longitude"))
            except Exception:
                continue

            if pd.isna(lat) or pd.isna(lon):
                continue

            # ------------------------------------------------
            # Trip update delay, if available
            # ------------------------------------------------

            delay_sec = None

            if (
                not trip_updates.empty
                and "trip_id" in trip_updates.columns
            ):

                updates = trip_updates[
                    trip_updates["trip_id"]
                    .astype(str)
                    .eq(trip_id)
                ]

                if not updates.empty:

                    numeric_delay = pd.to_numeric(
                        updates.get("arrival_delay_sec"),
                        errors="coerce"
                    )

                    if numeric_delay.notna().any():
                        delay_sec = float(
                            numeric_delay.dropna().iloc[0]
                        )

            live_candidates.append({
                "trip_id": trip_id,
                "route": route_id,
                "current_latitude": lat,
                "current_longitude": lon,
                "delay_sec": delay_sec,
                "verified_live_position": True,
            })

    # --------------------------------------------------------
    # RETURN LIVE DATA ONLY IF IT CAN ACTUALLY BE VERIFIED
    # --------------------------------------------------------

    if live_candidates:
        return {
            "success": True,
            "origin": origin,
            "destination": destination,
            "route_filter": route,
            "live_verified": True,
            "live_candidates": live_candidates[:10],
            "candidates": live_candidates[:10],
            "message": (
                "Live vehicle data is available. "
                "Exact stop-level boarding ETA requires "
                "the complete trip/stop sequence match."
            ),
        }

    # --------------------------------------------------------
    # SCHEDULE FALLBACK
    # --------------------------------------------------------

    scheduled = _find_direct_schedule(
        origin,
        destination,
    )

    if scheduled:
        return {
            "success": True,
            "origin": origin,
            "destination": destination,
            "route_filter": route,
            "live_verified": False,
            "candidates": scheduled[:10],
            "message": (
                "No verified live vehicle candidate was available. "
                "Showing scheduled service instead."
            ),
        }

    return {
        "success": False,
        "origin": origin,
        "destination": destination,
        "live_verified": False,
        "candidates": [],
        "message": (
            "No verified direct journey was found."
        ),
    }
