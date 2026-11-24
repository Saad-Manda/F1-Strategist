"""Read a race from the FastF1 cache, without touching the network."""

from pathlib import Path

import fastf1
import pandas as pd
from fastf1.exceptions import DataNotLoadedError

from src.common.errors import CalibrationError
from src.data.cleaning.assemble import build_frames
from src.data.spec.frames import COMPOUNDS, UNKNOWN, RaceFrames
from src.data.spec.races import Race


def read_race(race: Race, raw_dir: Path, sector_sum_tolerance_s: float) -> RaceFrames:
    """Load one cached race in the common format."""
    fastf1.set_log_level("ERROR")
    fastf1.Cache.enable_cache(str(raw_dir))
    # The archive needs a paid login (E1), so a missing file must fail here, not download.
    fastf1.Cache.offline_mode(True)
    session = _load_session(race)
    laps = _laps(session.laps)
    return build_frames(
        laps=laps,
        weather=_weather(session.weather_data),
        track_status=pd.DataFrame(
            {
                "time_s": session.track_status["Time"].dt.total_seconds(),
                "code": session.track_status["Status"].astype(str),
            }
        ),
        race_laps=int(laps["lap"].max()),
        sector_sum_tolerance_s=sector_sum_tolerance_s,
    )


def _load_session(race: Race) -> fastf1.core.Session:
    try:
        session = fastf1.get_session(race.year, race.event, "R")
    except ValueError as error:
        raise CalibrationError(f"{race.id}: no cached schedule for {race.year}") from error
    # FastF1 picks the closest name, so a typo would silently load another race.
    if session.event["EventName"] != race.event:
        raise CalibrationError(f"{race.id}: FastF1 matched '{session.event['EventName']}'")
    session.load(laps=True, telemetry=False, weather=True, messages=False)
    try:
        incomplete = session.laps.empty or session.weather_data.empty
    except DataNotLoadedError as error:
        raise CalibrationError(f"{race.id}: not in the FastF1 cache") from error
    if incomplete:
        raise CalibrationError(f"{race.id}: the FastF1 cache has no laps or no weather")
    return session


def _laps(raw: pd.DataFrame) -> pd.DataFrame:
    compound = raw["Compound"].astype("string").str.upper()
    known = compound.isin(COMPOUNDS)
    lap = raw["LapNumber"].astype(int)
    return pd.DataFrame(
        {
            "driver": raw["Driver"],
            "driver_number": raw["DriverNumber"].astype(int),
            "lap": lap,
            "lap_time_s": raw["LapTime"].dt.total_seconds(),
            "lap_start_s": raw["LapStartTime"].dt.total_seconds(),
            "lap_end_s": raw["Time"].dt.total_seconds(),
            "sector1_s": raw["Sector1Time"].dt.total_seconds(),
            "sector2_s": raw["Sector2Time"].dt.total_seconds(),
            "sector3_s": raw["Sector3Time"].dt.total_seconds(),
            "stint": raw["Stint"],
            "compound": compound.where(known, UNKNOWN),
            "tyre_age": raw["TyreLife"].where(known),
            "label": known.map({True: "raw", False: "missing"}),
            "is_in_lap": raw["PitInTime"].notna(),
            "is_out_lap": raw["PitOutTime"].notna() & (lap > 1),
        }
    )


def _weather(raw: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time_s": raw["Time"].dt.total_seconds(),
            "air_temp_c": raw["AirTemp"],
            "track_temp_c": raw["TrackTemp"],
            "humidity_pct": raw["Humidity"],
            "wind_speed_ms": raw["WindSpeed"],
            "rainfall": raw["Rainfall"].astype(bool),
        }
    )
