"""Read a race from the OpenF1 JSON files."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.errors import CalibrationError
from src.data.cleaning.assemble import build_frames
from src.data.cleaning.tyre_labels import Stint, label_laps
from src.data.spec.frames import RaceFrames
from src.data.spec.races import Race


def read_race(race: Race, raw_dir: Path, sector_sum_tolerance_s: float) -> RaceFrames:
    """Load one downloaded race in the common format."""
    folder = _race_folder(race, raw_dir)
    messages = _read(folder, "race_control")
    weather = pd.DataFrame(_read(folder, "weather"))
    feed_start = _utc([weather["date"].min(), *(m["date"] for m in messages)]).min()
    results = pd.DataFrame(_read(folder, "session_result"))
    race_laps = int(results["number_of_laps"].max())

    status = track_status(messages, feed_start)
    laps = _laps(race, folder, messages, feed_start, race_laps)
    return build_frames(
        laps=laps,
        weather=pd.DataFrame(
            {
                "time_s": _seconds(weather["date"], feed_start),
                "air_temp_c": weather["air_temperature"],
                "track_temp_c": weather["track_temperature"],
                "humidity_pct": weather["humidity"],
                "wind_speed_ms": weather["wind_speed"],
                "rainfall": weather["rainfall"] > 0,
            }
        ),
        track_status=status,
        race_laps=race_laps,
        sector_sum_tolerance_s=sector_sum_tolerance_s,
    )


def track_status(messages: list[dict[str, Any]], feed_start: pd.Timestamp) -> pd.DataFrame:
    """Rebuild FastF1's track status codes from race control messages."""
    changes = [(0.0, "1")]
    neutral = "1"  # the safety car, VSC or red flag now in force, or "1" for none
    yellow_sectors: set[int] = set()
    starts_behind_safety_car = False
    for message in sorted(messages, key=lambda m: m["date"]):
        text, flag = message["message"], message["flag"]
        sector = message["sector"]
        if flag == "RED":
            neutral = "5"
        elif message["category"] == "SafetyCar" and text == "SAFETY CAR DEPLOYED":
            neutral = "4"
        elif message["category"] == "SafetyCar" and text == "VIRTUAL SAFETY CAR DEPLOYED":
            neutral = "6"
        elif message["category"] == "SafetyCar" and text == "VIRTUAL SAFETY CAR ENDING":
            neutral = "7"
        elif text == "TRACK CLEAR":
            neutral = "1"
            yellow_sectors.clear()
        elif text == "RACE WILL START BEHIND THE SAFETY CAR":
            starts_behind_safety_car = True
        elif text == "SESSION STARTED":
            if starts_behind_safety_car:
                neutral = "4"
                starts_behind_safety_car = False
            elif neutral == "5":
                neutral = "1"
        elif text == "ROLLING START" and neutral == "4":
            neutral = "1"
        elif flag in ("YELLOW", "DOUBLE YELLOW") and sector is not None:
            yellow_sectors.add(sector)
        elif flag == "CLEAR" and sector is not None:
            yellow_sectors.discard(sector)
        code = neutral if neutral != "1" else ("2" if yellow_sectors else "1")
        if code != changes[-1][1]:
            time_s = (_utc([message["date"]])[0] - feed_start).total_seconds()
            changes.append((time_s, code))
    return pd.DataFrame(changes, columns=["time_s", "code"])


def _laps(
    race: Race,
    folder: Path,
    messages: list[dict[str, Any]],
    feed_start: pd.Timestamp,
    race_laps: int,
) -> pd.DataFrame:
    raw = pd.DataFrame(_read(folder, "laps")).sort_values(["driver_number", "lap_number"])
    stints = _read(folder, "stints")
    names = {d["driver_number"]: d["name_acronym"] for d in _read(folder, "drivers")}
    pits = _read(folder, "pit") if (folder / "pit.json").exists() else []
    pit_laps = {(p["driver_number"], p["lap_number"]) for p in pits}

    laps = pd.DataFrame(
        {
            "driver": raw["driver_number"].map(names),
            "driver_number": raw["driver_number"],
            "lap": raw["lap_number"],
            "lap_time_s": raw["lap_duration"].astype(float),
            "lap_start_s": _seconds(raw["date_start"], feed_start),
            "sector1_s": raw["duration_sector_1"].astype(float),
            "sector2_s": raw["duration_sector_2"].astype(float),
            "sector3_s": raw["duration_sector_3"].astype(float),
            "is_out_lap": raw["is_pit_out_lap"].fillna(False).astype(bool) & (raw["lap_number"] > 1),
        }
    )
    by_driver = laps.groupby("driver_number")
    next_start = by_driver["lap_start_s"].shift(-1)
    next_is_out = by_driver["is_out_lap"].shift(-1, fill_value=False)
    race_start = _race_start(race, messages, feed_start)
    # OpenF1 gives no lap 1 start, or the restart time after a lap 1 red flag (2024 Monaco).
    laps["lap_start_s"] = laps["lap_start_s"].mask(laps["lap"] == 1, race_start)
    laps["lap_end_s"] = next_start.fillna(laps["lap_start_s"] + laps["lap_time_s"])
    keys = list(zip(laps["driver_number"], laps["lap"]))
    laps["is_in_lap"] = next_is_out.astype(bool) | pd.Series([k in pit_laps for k in keys], index=laps.index)

    labels = []
    for number, group in laps.groupby("driver_number"):
        own = [s for s in stints if s["driver_number"] == number]
        table = label_laps(
            stints=_stints(own),
            pit_out_laps=group.loc[group["is_out_lap"], "lap"].tolist(),
            laps=group["lap"].tolist(),
            opening_compound="opening_compound" in race.repairs,
        )
        labels.append(table.assign(driver_number=number))
    return laps.merge(pd.concat(labels), on=["driver_number", "lap"], how="left", validate="1:1")


def _stints(raw: list[dict[str, Any]]) -> list[Stint]:
    complete = [s for s in raw if s["lap_start"] is not None and s["lap_end"] is not None]
    return [
        Stint(s["lap_start"], s["lap_end"], str(s["compound"]), s["tyre_age_at_start"] or 0)
        for s in sorted(complete, key=lambda s: s["stint_number"])
    ]


def _race_start(
    race: Race, messages: list[dict[str, Any]], feed_start: pd.Timestamp
) -> float:
    starts = [m["date"] for m in messages if m["message"] == "SESSION STARTED"]
    if not starts:
        raise CalibrationError(f"{race.id}: race control has no SESSION STARTED message")
    return (_utc(starts).min() - feed_start).total_seconds()


def _race_folder(race: Race, raw_dir: Path) -> Path:
    folders = list((raw_dir / "openf1" / str(race.year)).glob(f"{race.session_key}_*"))
    if len(folders) != 1:
        raise CalibrationError(f"{race.id}: expected one OpenF1 folder, found {len(folders)}")
    return folders[0]


def _read(folder: Path, endpoint: str) -> list[dict[str, Any]]:
    file = folder / f"{endpoint}.json"
    if not file.exists():
        raise CalibrationError(f"{file}: OpenF1 file not found")
    return json.loads(file.read_text(encoding="utf-8"))


def _utc(values: Any) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(list(values), utc=True, format="ISO8601"))


def _seconds(dates: pd.Series, feed_start: pd.Timestamp) -> pd.Series:
    times = pd.to_datetime(dates, utc=True, format="ISO8601")
    return (times - feed_start).dt.total_seconds()
