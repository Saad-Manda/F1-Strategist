"""Safety cars: how often they come and go, and how slow their laps are (D33)."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.calibration.fitting_races import FittingRace
from src.calibration.models.chains import count_steps, shares
from src.calibration.models.fields import Fields
from src.common.config import ConfigSection
from src.common.errors import CalibrationError

STATUSES = ("GREEN", "SC", "VSC")
FLAG_FIELDS = {"SC": "safety_car", "VSC": "virtual_safety_car"}


@dataclass(frozen=True)
class FlagPeriod:
    """An SC or VSC period between green laps. `extra` is its time lost, in green laps."""

    race: str
    status: str
    laps: int
    extra: float


def status_fields(circuit: str, races: list[FittingRace], config: ConfigSection) -> Fields:
    """Status chain and flag lap times of `circuit`. Only its green lap is its own."""
    start, counts = status_counts(races)
    periods = [period for race in races for period in flag_periods(race, config)]
    green = _circuit_green_lap(circuit, races, config)
    values = {
        "status_start": shares(start),
        "status_transition": {s: shares(counts.loc[s]) for s in STATUSES},
        "flag_noise_std": config["flag_laps"]["noise_std"],
    }
    provenance = {
        "status_start": "pooled",
        "status_transition": "pooled",
        "flag_noise_std": "prior",
    }
    ratios = {}
    for status, field in FLAG_FIELDS.items():
        ratios[status] = flag_lap_ratio(periods, status)
        values[field] = {"lap_time": ratios[status] * green}
        provenance[f"{field}.lap_time"] = "pooled"
    return Fields(
        values,
        provenance,
        diagnostics={
            "races": len(races),
            "start_counts": start.to_dict(),
            "transition_counts": counts.T.to_dict(),
            "flag_lap_ratio": ratios,
            "flag_periods": {s: sum(p.status == s for p in periods) for s in FLAG_FIELDS},
            "green_lap": green,
        },
    )


def status_counts(races: list[FittingRace]) -> tuple[pd.Series, pd.DataFrame]:
    """Status of lap 1, and steps from lap to lap. Red flags are not modelled (D21)."""
    return count_steps((r.conditions.table["status"] for r in races), STATUSES)


def flag_periods(race: FittingRace, config: ConfigSection) -> list[FlagPeriod]:
    """Dry SC and VSC periods that begin and end under green.

    The lap after a period is still slow, because status is taken at the lap's end (D31).
    Its lost time belongs to the period.
    """
    table = race.conditions.table
    status = table["status"]
    duration = table["end_s"] - table["start_s"]
    green = _green_lap(race, config)
    dry = _is_dry(race)
    period = (status != status.shift()).cumsum()
    found = []
    for _, laps in status.groupby(period):
        name, first, last = laps.iloc[0], laps.index[0], laps.index[-1]
        around = range(first - 1, last + 2)
        if name not in FLAG_FIELDS or first < config["flag_laps"]["min_lap"]:
            continue
        if last == status.index[-1] or not dry.loc[around].all():
            continue
        if status[first - 1] != "GREEN" or status[last + 1] != "GREEN":
            continue
        lost = duration.loc[first : last + 1].sum() / green - (len(laps) + 1)
        found.append(FlagPeriod(race.race.id, name, len(laps), float(lost)))
    return found


def flag_lap_ratio(periods: list[FlagPeriod], status: str) -> float:
    """Lap time in green laps, such that the labelled laps lose as much time as the real ones."""
    chosen = [p for p in periods if p.status == status]
    if not chosen:
        raise CalibrationError(f"no {status} period to take a lap time from")
    return 1 + sum(p.extra for p in chosen) / sum(p.laps for p in chosen)


def _is_dry(race: FittingRace) -> pd.Series:
    """Laps known to be dry; a race with rejected weather has none."""
    return (race.conditions.table["regime"] == "DRY").fillna(False).astype(bool)


def _green_lap(race: FittingRace, config: ConfigSection) -> float:
    """Median dry green lap of the leader."""
    table = race.conditions.table
    laps = (table["status"] == "GREEN") & _is_dry(race)
    laps &= table.index >= config["flag_laps"]["min_lap"]
    return float((table["end_s"] - table["start_s"])[laps].median())


def _circuit_green_lap(circuit: str, races: list[FittingRace], config: ConfigSection) -> float:
    laps = [_green_lap(r, config) for r in races if r.race.circuit == circuit and r.fully_dry]
    if not laps:
        raise CalibrationError(f"{circuit}: no dry race to take a green lap from")
    return float(np.median(laps))
