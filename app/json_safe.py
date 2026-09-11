import math
import datetime

import numpy as np
import pandas as pd


def make_json_safe(obj):
    """
    Recursively convert pandas/numpy/Python objects into
    standard JSON-compatible values.

    Handles:
      numpy integers
      numpy floats
      numpy booleans
      pandas timestamps
      pandas NA/NaT
      dictionaries
      lists
      tuples
      sets
      DataFrames
      Series
    """

    # --------------------------------------------------------
    # None
    # --------------------------------------------------------

    if obj is None:
        return None

    # --------------------------------------------------------
    # pandas missing values
    # --------------------------------------------------------

    try:
        if pd.isna(obj):
            # pd.isna() can return an array for some objects,
            # so only use it when it is a scalar boolean.
            if isinstance(obj, (bool, np.bool_)):
                if bool(obj):
                    return None

    except Exception:
        pass

    # --------------------------------------------------------
    # NumPy scalar values
    # --------------------------------------------------------

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        value = float(obj)

        if not math.isfinite(value):
            return None

        return value

    if isinstance(obj, np.bool_):
        return bool(obj)

    # --------------------------------------------------------
    # Python float
    # --------------------------------------------------------

    if isinstance(obj, float):

        if not math.isfinite(obj):
            return None

        return obj

    # --------------------------------------------------------
    # NumPy arrays
    # --------------------------------------------------------

    if isinstance(obj, np.ndarray):
        return [
            make_json_safe(item)
            for item in obj.tolist()
        ]

    # --------------------------------------------------------
    # pandas Timestamp
    # --------------------------------------------------------

    if isinstance(obj, pd.Timestamp):

        if pd.isna(obj):
            return None

        return obj.isoformat()

    # --------------------------------------------------------
    # pandas Timedelta
    # --------------------------------------------------------

    if isinstance(obj, pd.Timedelta):

        if pd.isna(obj):
            return None

        return str(obj)

    # --------------------------------------------------------
    # Python datetime
    # --------------------------------------------------------

    if isinstance(
        obj,
        (
            datetime.datetime,
            datetime.date,
            datetime.time,
        ),
    ):
        return obj.isoformat()

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    if isinstance(obj, dict):

        return {
            str(key): make_json_safe(value)
            for key, value in obj.items()
        }

    # --------------------------------------------------------
    # List / tuple / set
    # --------------------------------------------------------

    if isinstance(
        obj,
        (
            list,
            tuple,
            set,
        ),
    ):

        return [
            make_json_safe(item)
            for item in obj
        ]

    # --------------------------------------------------------
    # pandas Series
    # --------------------------------------------------------

    if isinstance(obj, pd.Series):

        return [
            make_json_safe(item)
            for item in obj.tolist()
        ]

    # --------------------------------------------------------
    # pandas DataFrame
    # --------------------------------------------------------

    if isinstance(obj, pd.DataFrame):

        return [
            make_json_safe(record)
            for record in obj.to_dict(
                orient="records"
            )
        ]

    # --------------------------------------------------------
    # Strings / integers / booleans
    # --------------------------------------------------------

    if isinstance(
        obj,
        (
            str,
            int,
            bool,
        ),
    ):
        return obj

    # --------------------------------------------------------
    # Last-resort conversion
    # --------------------------------------------------------

    try:

        converted = obj.item()

        if converted is not obj:
            return make_json_safe(
                converted
            )

    except Exception:
        pass

    # --------------------------------------------------------
    # String fallback
    # --------------------------------------------------------

    return str(obj)
