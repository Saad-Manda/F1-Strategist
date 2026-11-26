"""GREEN, SC, VSC or RED for each lap of the leader."""

import numpy as np
import pandas as pd

from src.common.errors import CalibrationError

SC_CODES = ("4",)
VSC_CODES = ("6", "7")
RED_CODES = ("5",)


def lap_status(timeline: pd.DataFrame, track_status: pd.DataFrame) -> pd.Series:
    """Track status when the leader finishes the lap, which is when a car would stop (D31)."""
    begins = track_status["time_s"].to_numpy(float)
    codes = track_status["code"].to_numpy()
    active = np.searchsorted(begins, timeline["end_s"], side="right") - 1
    if active.min() < 0:
        raise CalibrationError("no track status before the end of the first lap")
    at_end = pd.Series(codes[active], index=timeline.index)
    red = _overlaps(timeline, track_status, RED_CODES)
    # The lap after a red flag is the restart, which is not normal racing.
    red |= red.shift(1, fill_value=False)
    status = np.select(
        [red, at_end.isin(SC_CODES), at_end.isin(VSC_CODES)],
        ["RED", "SC", "VSC"],
        default="GREEN",
    )
    return pd.Series(status, index=timeline.index, name="status", dtype="string")


def _overlaps(
    timeline: pd.DataFrame, track_status: pd.DataFrame, codes: tuple[str, ...]
) -> pd.Series:
    """Whether one of the codes was active at any time during each lap."""
    begins = track_status["time_s"].to_numpy(float)
    ends = np.append(begins[1:], np.inf)
    active = track_status["code"].isin(codes).to_numpy(bool)
    hits = [
        bool((active & (begins < end) & (ends > start)).any())
        for start, end in zip(timeline["start_s"], timeline["end_s"])
    ]
    return pd.Series(hits, index=timeline.index)
