"""The common format of one race. Both readers must produce exactly this."""

from dataclasses import dataclass

import pandas as pd

from src.common.errors import ContractError

COMPOUNDS = ("SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET")
UNKNOWN = "UNKNOWN"

# How far the compound and tyre age of a lap can be trusted.
LABELS = ("raw", "shifted", "repaired", "suspect", "missing")

# FastF1's codes: clear, yellow, safety car, red, VSC, VSC ending.
STATUS_CODES = ("1", "2", "4", "5", "6", "7")

# Times ending in _s are seconds; start and end count from the start of the data feed.
LAP_DTYPES = {
    "driver": "string",
    "driver_number": "int64",
    "lap": "int64",
    "lap_time_s": "float64",
    "lap_start_s": "float64",
    "lap_end_s": "float64",
    "sector1_s": "float64",
    "sector2_s": "float64",
    "sector3_s": "float64",
    "stint": "Int64",
    "compound": "string",
    "tyre_age": "Int64",
    "label": "string",
    "is_in_lap": "bool",
    "is_out_lap": "bool",
    "is_accurate": "bool",
    "track_status": "string",
}
WEATHER_DTYPES = {
    "time_s": "float64",
    "air_temp_c": "float64",
    "track_temp_c": "float64",
    "humidity_pct": "float64",
    "wind_speed_ms": "float64",
    "rainfall": "bool",
}
STATUS_DTYPES = {"time_s": "float64", "code": "string"}


@dataclass(frozen=True)
class RaceFrames:
    """One race in the common format."""

    laps: pd.DataFrame
    weather: pd.DataFrame
    track_status: pd.DataFrame
    race_laps: int
    dropped_laps: int


def enforce_format(frame: pd.DataFrame, dtypes: dict[str, str], key: list[str]) -> pd.DataFrame:
    """Keep the agreed columns, types and row order, or raise."""
    missing = set(dtypes) - set(frame.columns)
    if missing:
        raise ContractError(f"frame lacks columns {sorted(missing)}")
    frame = frame[list(dtypes)].astype(dtypes).sort_values(key, kind="stable")
    if "lap" in key and frame.duplicated(key).any():
        raise ContractError(f"frame repeats keys {key}")
    return frame.reset_index(drop=True)
