"""The laps the tyre model is fitted on: normal racing laps of fully dry races."""

import pandas as pd

from src.calibration.conditions.regimes import UNTRUSTED_LABELS
from src.calibration.fitting_races import FittingRace
from src.common.config import ConfigSection
from src.common.errors import CalibrationError

DRY_COMPOUNDS = ("SOFT", "MEDIUM", "HARD")
CLEAR_TRACK = "1"


def collect_clean_laps(
    races: list[FittingRace], config: ConfigSection
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean laps of the tyre seasons, and their counts per step.

    Only fully dry races are used, because a drying track looks like tyre wear (D32).
    """
    laps, counts = {}, {}
    for season in config["tyres"]["fit_seasons"]:
        dry = [r for r in races if r.race.year == season and r.race.role == "fit" and r.fully_dry]
        if not dry:
            raise CalibrationError(f"no dry race to fit tyres on in {season}")
        for race in dry:
            laps[race.race.id], counts[race.race.id] = clean_laps(race, config)
    return pd.concat(laps.values(), ignore_index=True), pd.DataFrame(counts).T


def clean_laps(race: FittingRace, config: ConfigSection) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clean laps of one race with fuel removed, and how many laps are left after each step."""
    rules = config["tyres"]
    laps = race.frames.laps
    lap_status = laps["lap"].map(race.conditions.table["status"])
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
    car = race.race.id + " " + laps["driver"]
    table = pd.DataFrame(
        {
            "race": race.race.id,
            "circuit": race.race.circuit,
            "car": car,
            "stint": car + " " + laps["stint"].astype("string"),
            "lap": laps["lap"].astype(float),
            "compound": laps["compound"],
            "age": laps["tyre_age"].astype(float),
            "pace": laps["lap_time_s"] - fuel_per_lap * (race.frames.race_laps - laps["lap"]),
        }
    )
    return table, counts
