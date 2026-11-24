"""Refuse races that are too incomplete to use."""

from typing import Any

from src.common.config import ConfigSection
from src.common.errors import CalibrationError
from src.data.spec.frames import UNKNOWN, RaceFrames
from src.data.spec.races import Race


def check_race(race: Race, frames: RaceFrames, checks: ConfigSection) -> dict[str, Any]:
    """Summarise a race and refuse one that is too incomplete to use."""
    laps = frames.laps
    summary = {
        "cars": int(laps["driver_number"].nunique()),
        "known_compound_share": round(float((laps["compound"] != UNKNOWN).mean()), 4),
        "missing_lap_time_share": round(float(laps["lap_time_s"].isna().mean()), 4),
        "suspect_label_share": round(float((laps["label"] == "suspect").mean()), 4),
        "labels": {k: int(v) for k, v in laps["label"].value_counts().sort_index().items()},
    }
    if race.role == "frequency_only":
        return summary
    problems = []
    if summary["cars"] < checks["min_cars"]:
        problems.append(f"cars {summary['cars']}")
    if summary["known_compound_share"] < checks["min_known_compound_share"]:
        problems.append(f"known compounds {summary['known_compound_share']}")
    if summary["missing_lap_time_share"] > checks["max_missing_lap_time_share"]:
        problems.append(f"missing lap times {summary['missing_lap_time_share']}")
    if summary["suspect_label_share"] > checks["max_suspect_label_share"]:
        problems.append(f"suspect labels {summary['suspect_label_share']}")
    if problems:
        raise CalibrationError(f"{race.id}: {', '.join(problems)}")
    return summary
