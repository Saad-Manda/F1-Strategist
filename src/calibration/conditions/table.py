"""Everything about the conditions of one race, one row per lap of the leader."""

from dataclasses import dataclass

import pandas as pd

from src.calibration.conditions.regimes import lap_regimes, tyre_shares, weather_rejection
from src.calibration.conditions.status import lap_status
from src.calibration.conditions.timeline import leader_timeline
from src.common.config import ConfigSection
from src.common.errors import CalibrationError
from src.data.spec.frames import RaceFrames
from src.data.spec.races import Race


@dataclass(frozen=True)
class RaceConditions:
    """Conditions of one race. `regime` is empty when the weather was rejected."""

    race: Race
    table: pd.DataFrame
    weather_rejection: str


def race_conditions(race: Race, frames: RaceFrames, rules: ConfigSection) -> RaceConditions:
    """Build the per-lap table: timeline, status, regime, tyre shares, sensors."""
    try:
        timeline = leader_timeline(frames.laps, frames.race_laps)
    except CalibrationError as error:
        raise CalibrationError(f"{race.id}: {error}") from error
    shares = tyre_shares(frames.laps)
    rejection = weather_rejection(shares, rules["min_known_tyre_share"])
    table = timeline.join(lap_status(timeline, frames.track_status))
    if rejection:
        table["regime"] = pd.Series(pd.NA, index=table.index, dtype="string")
    else:
        table["regime"] = lap_regimes(shares, rules)
    table = table.join(shares).join(lap_sensors(timeline, frames.weather))
    return RaceConditions(race=race, table=table, weather_rejection=rejection)


def lap_sensors(timeline: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Rainfall and temperatures during each lap; a lap without a sample uses the last one."""
    rows = []
    for start, end in zip(timeline["start_s"], timeline["end_s"]):
        inside = weather[(weather["time_s"] >= start) & (weather["time_s"] < end)]
        if inside.empty:
            inside = weather[weather["time_s"] < end].tail(1)
        if inside.empty:
            raise CalibrationError(f"no weather sample before {end:.0f} s")
        rows.append(
            {
                "rainfall": bool(inside["rainfall"].any()),
                "air_temp_c": inside["air_temp_c"].mean(),
                "track_temp_c": inside["track_temp_c"].mean(),
            }
        )
    return pd.DataFrame(rows, index=timeline.index)
