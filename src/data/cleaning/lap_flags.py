"""What each lap is usable for: complete timing, and the flags shown during it."""

import numpy as np
import pandas as pd


def accurate_laps(laps: pd.DataFrame, tolerance_s: float) -> pd.Series:
    """Laps with complete, consistent timing that are not in-laps or out-laps."""
    sectors = laps[["sector1_s", "sector2_s", "sector3_s"]].sum(axis=1)
    consistent = (sectors - laps["lap_time_s"]).abs() <= tolerance_s
    return consistent & (laps["lap"] > 1) & ~laps["is_in_lap"] & ~laps["is_out_lap"]


def lap_track_status(laps: pd.DataFrame, track_status: pd.DataFrame) -> list[str]:
    """Every status code that was active during each lap, or '' when its times are unknown."""
    starts = track_status["time_s"].to_numpy(float)
    ends = np.append(starts[1:], np.inf)
    codes = track_status["code"].to_numpy(str)
    result = []
    for lap_start, lap_end in zip(laps["lap_start_s"], laps["lap_end_s"]):
        if np.isnan(lap_start) or np.isnan(lap_end):
            result.append("")
            continue
        active = (starts < lap_end) & (ends > lap_start)
        result.append("".join(sorted(set(codes[active]))))
    return result
