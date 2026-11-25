"""DRY, DAMP or WET for each lap, from the tyres the field is using."""

import numpy as np
import pandas as pd

from src.common.config import ConfigSection

REGIMES = ("DRY", "DAMP", "WET")
UNTRUSTED_LABELS = ("suspect", "missing")


def tyre_shares(laps: pd.DataFrame) -> pd.DataFrame:
    """Per lap: share of cars with a trusted tyre, and INTERMEDIATE and WET shares among those."""
    trusted = ~laps["label"].isin(UNTRUSTED_LABELS)
    by_lap = laps["lap"]
    known_cars = trusted.groupby(by_lap).sum()
    shares = pd.DataFrame({"known_share": known_cars / laps.groupby("lap").size()})
    for column, compound in (("inter_share", "INTERMEDIATE"), ("wet_share", "WET")):
        cars = (trusted & (laps["compound"] == compound)).groupby(by_lap).sum()
        shares[column] = (cars / known_cars).astype(float)
    return shares


def weather_rejection(shares: pd.DataFrame, min_known_share: float) -> str:
    """Why a race cannot be labelled, or '' when it can."""
    low = shares.index[shares["known_share"] < min_known_share].tolist()
    if not low:
        return ""
    lowest = shares["known_share"].min()
    return f"known tyres fall to {lowest:.0%} (laps {low[0]}-{low[-1]})"


def lap_regimes(shares: pd.DataFrame, rules: ConfigSection) -> pd.Series:
    """Weather regime per lap. Rain sensors are ignored: slicks in light rain stay DRY (E2)."""
    rain = (shares["inter_share"] + shares["wet_share"]).to_numpy(float)
    level = np.zeros(len(rain), dtype=int)
    for first, last in _phases(rain >= rules["damp_start_share"]):
        # Teams stay on rain tyres too long while the track dries, so the tail is cut (D28).
        high = np.flatnonzero(rain[first : last + 1] >= rules["damp_end_share"])
        end = first + high[-1] if len(high) else last
        level[first : end + 1] = 1
    level[shares["wet_share"].to_numpy(float) >= rules["wet_share"]] = 2
    level = _median_filter(level, rules["median_filter_laps"])
    return pd.Series([REGIMES[i] for i in level], index=shares.index, name="regime", dtype="string")


def _phases(flags: np.ndarray) -> list[tuple[int, int]]:
    """First and last position of every unbroken run of True."""
    padded = np.concatenate([[False], flags, [False]]).astype(int)
    steps = np.diff(padded)
    return list(zip(np.flatnonzero(steps == 1), np.flatnonzero(steps == -1) - 1))


def _median_filter(level: np.ndarray, width: int) -> np.ndarray:
    """Remove flicker shorter than half the window; the ends keep their own value."""
    half = width // 2
    smooth = level.copy()
    for i in range(half, len(level) - half):
        smooth[i] = int(np.median(level[i - half : i + half + 1]))
    return smooth
