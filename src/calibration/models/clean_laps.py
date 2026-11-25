"""The laps the tyre model is fitted on: normal racing laps of fully dry races."""

from pathlib import Path

import pandas as pd

from src.calibration.conditions.regimes import UNTRUSTED_LABELS
from src.calibration.conditions.table import RaceConditions, race_conditions
from src.common.config import ConfigSection
from src.common.errors import CalibrationError
from src.data.spec.frames import RaceFrames
from src.data.spec.races import Race
from src.data.storage.frozen import load_race

DRY_COMPOUNDS = ("SOFT", "MEDIUM", "HARD")
CLEAR_TRACK = "1"


def collect_clean_laps(
    races: list[Race], interim_dir: str | Path, config: ConfigSection
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean laps of every fully dry race in the tyre seasons, and their counts per step."""
    seasons = config["tyres"]["fit_seasons"]
    laps, counts = {}, {}
    for race in races:
        if race.year not in seasons:
            continue
        if race.role == "holdout":
            raise CalibrationError(f"{race.id}: held out, but in fit_seasons (D25)")
        if race.role != "fit":
            continue
        frames = load_race(race.id, interim_dir)
        conditions = race_conditions(race, frames, config["conditions"])
        if is_fully_dry(conditions):
            laps[race.id], counts[race.id] = clean_laps(frames, conditions, config)
    if not laps:
        raise CalibrationError(f"no dry race to fit tyres on in {seasons}")
    return pd.concat(laps.values(), ignore_index=True), pd.DataFrame(counts).T


def is_fully_dry(conditions: RaceConditions) -> bool:
    """A drying track looks like tyre wear, so one damp lap excludes the race (D32)."""
    return not conditions.weather_rejection and bool((conditions.table["regime"] == "DRY").all())


def clean_laps(
    frames: RaceFrames, conditions: RaceConditions, config: ConfigSection
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clean laps of one race with fuel removed, and how many laps are left after each step."""
    rules = config["tyres"]
    laps = frames.laps
    lap_status = laps["lap"].map(conditions.table["status"])
    steps = {
        "known_dry_tyre": laps["compound"].isin(DRY_COMPOUNDS)
        & ~laps["label"].isin(UNTRUSTED_LABELS),
        "green": (laps["track_status"] == CLEAR_TRACK) & (lap_status == "GREEN"),
        "accurate": laps["is_accurate"],
        "settled": (laps["lap"] >= rules["min_lap"]) & (laps["tyre_age"] >= rules["min_tyre_age"]),
    }
    counts = {"all": len(laps)}
    for name, keep in steps.items():
        laps = laps[keep.loc[laps.index].fillna(False).astype(bool)]
        counts[name] = len(laps)
    median = laps.groupby("driver")["lap_time_s"].transform("median")
    laps = laps[(laps["lap_time_s"] - median).abs() <= rules["max_gap_to_median_s"]]
    counts["near_median"] = len(laps)

    fuel = config["fuel"]
    fuel_per_lap = fuel["consumption_kg_per_lap"] * fuel["sensitivity_s_per_kg"]
    car = conditions.race.id + " " + laps["driver"]
    table = pd.DataFrame(
        {
            "race": conditions.race.id,
            "circuit": conditions.race.circuit,
            "car": car,
            "stint": car + " " + laps["stint"].astype("string"),
            "lap": laps["lap"].astype(float),
            "compound": laps["compound"],
            "age": laps["tyre_age"].astype(float),
            "pace": laps["lap_time_s"] - fuel_per_lap * (frames.race_laps - laps["lap"]),
        }
    )
    return table, counts
