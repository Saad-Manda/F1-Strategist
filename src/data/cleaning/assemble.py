"""Finish a race that a reader has loaded, so every source ends in the same format."""

import pandas as pd

from src.data.cleaning.lap_flags import accurate_laps, lap_track_status
from src.data.spec.frames import (
    LAP_DTYPES,
    STATUS_DTYPES,
    WEATHER_DTYPES,
    RaceFrames,
    enforce_format,
)


def build_frames(
    laps: pd.DataFrame,
    weather: pd.DataFrame,
    track_status: pd.DataFrame,
    race_laps: int,
    sector_sum_tolerance_s: float,
) -> RaceFrames:
    """Finish the columns both sources share and enforce the format."""
    inside = laps["lap"] <= race_laps
    laps = laps[inside].copy()
    laps["is_accurate"] = accurate_laps(laps, sector_sum_tolerance_s)
    laps["track_status"] = lap_track_status(laps, track_status)
    return RaceFrames(
        laps=enforce_format(laps, LAP_DTYPES, ["driver_number", "lap"]),
        weather=enforce_format(weather, WEATHER_DTYPES, ["time_s"]),
        track_status=enforce_format(track_status, STATUS_DTYPES, ["time_s"]),
        race_laps=race_laps,
        dropped_laps=int((~inside).sum()),
    )
