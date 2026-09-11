
import pickle
import json
import numpy as np
import pandas as pd

MODEL_PATH = r"/kaggle/working/models/final_eta_gradient_boosting.pkl"
CONFIG_PATH = r"/kaggle/working/models/eta_model_config.json"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

FEATURES = config["features"]

MEDIANS = pd.Series(
    config["training_medians"]
)


def create_context_features(data):

    data = data.copy()

    numeric_columns = [
        "distance_to_next_stop_km",
        "observed_speed_kmh",
        "arrival_delay_sec",
        "delay_minutes",
        "hour",
        "minute_of_day",
        "bearing",
        "current_stop_sequence",
        "next_stop_sequence",
        "latitude",
        "longitude",
        "next_stop_lat",
        "next_stop_lon",
        "time_since_previous_sec"
    ]

    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

    data["is_zero_speed"] = (
        data["observed_speed_kmh"] <= 0
    ).astype(int)

    data["is_low_speed"] = (
        data["observed_speed_kmh"] < 10
    ).astype(int)

    data["is_high_speed"] = (
        data["observed_speed_kmh"] > 50
    ).astype(int)

    data["is_long_distance"] = (
        data["distance_to_next_stop_km"] > 1
    ).astype(int)

    data["is_very_long_distance"] = (
        data["distance_to_next_stop_km"] > 2
    ).astype(int)

    data["absolute_delay_sec"] = np.abs(
        data["arrival_delay_sec"]
    )

    data["is_delayed"] = (
        data["arrival_delay_sec"] > 60
    ).astype(int)

    data["is_highly_delayed"] = (
        data["arrival_delay_sec"] > 300
    ).astype(int)

    data["is_early"] = (
        data["arrival_delay_sec"] < -60
    ).astype(int)

    safe_speed = (
        data["observed_speed_kmh"]
        .replace(0, np.nan)
    )

    data["distance_speed_ratio"] = (
        data["distance_to_next_stop_km"]
        / safe_speed
    )

    data["estimated_travel_minutes"] = (
        data["distance_speed_ratio"]
        * 60
    )

    data["distance_x_speed"] = (
        data["distance_to_next_stop_km"]
        * data["observed_speed_kmh"]
    )

    data["distance_x_delay"] = (
        data["distance_to_next_stop_km"]
        * data["delay_minutes"]
    )

    data["speed_x_delay"] = (
        data["observed_speed_kmh"]
        * data["delay_minutes"]
    )

    data["is_morning_peak"] = (
        data["hour"].between(7, 9)
    ).astype(int)

    data["is_evening_peak"] = (
        data["hour"].between(16, 18)
    ).astype(int)

    data["is_peak_period"] = (
        data["hour"].between(7, 9)
        |
        data["hour"].between(16, 18)
    ).astype(int)

    data["stop_progress"] = (
        data["current_stop_sequence"]
        /
        data["next_stop_sequence"].replace(
            0,
            np.nan
        )
    )

    return data


def predict_eta(record):

    row = pd.DataFrame([record])

    row = create_context_features(row)

    X = row[FEATURES].apply(
        pd.to_numeric,
        errors="coerce"
    )

    X = X.fillna(MEDIANS)

    prediction = model.predict(X)[0]

    prediction = float(
        np.clip(
            prediction,
            0,
            30
        )
    )

    return round(
        prediction,
        2
    )
