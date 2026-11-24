"""Each test names the code change that would make it fail."""

import json

import pandas as pd
import pytest

from src.common.errors import CalibrationError
from src.data.spec.races import Race
from src.data.sources.openf1 import read_race, track_status

START = pd.Timestamp("2024-07-07T14:00:00", tz="UTC")


def message(second, text="", category="Flag", flag=None, sector=None):
    date = (START + pd.Timedelta(f"{second}s")).isoformat()
    return {"date": date, "message": text, "category": category, "flag": flag, "sector": sector}


def safety_car(second, text):
    return message(second, text, category="SafetyCar")


def codes(*messages):
    table = track_status(list(messages), START)
    return list(zip(table["time_s"], table["code"]))


def test_vsc_upgraded_to_safety_car():
    # Fails if a safety car after a VSC is missed, or "in this lap" ends it early.
    assert codes(
        safety_car(10, "VIRTUAL SAFETY CAR DEPLOYED"),
        safety_car(20, "SAFETY CAR DEPLOYED"),
        safety_car(90, "SAFETY CAR IN THIS LAP"),
        message(100, "TRACK CLEAR", flag="CLEAR"),
    ) == [(0, "1"), (10, "6"), (20, "4"), (100, "1")]


def test_vsc_ending_is_its_own_status():
    # Fails if the VSC is treated as over before the track is clear.
    assert codes(
        safety_car(10, "VIRTUAL SAFETY CAR DEPLOYED"),
        safety_car(50, "VIRTUAL SAFETY CAR ENDING"),
        message(60, "TRACK CLEAR", flag="CLEAR"),
    ) == [(0, "1"), (10, "6"), (50, "7"), (60, "1")]


def test_yellow_lasts_until_the_last_sector_clears():
    # Fails if one clear sector ends every yellow.
    assert codes(
        message(10, flag="YELLOW", sector=3),
        message(12, flag="DOUBLE YELLOW", sector=4),
        message(20, flag="CLEAR", sector=3),
        message(30, flag="CLEAR", sector=4),
    ) == [(0, "1"), (10, "2"), (30, "1")]


def test_safety_car_outranks_yellow():
    # Fails if a sector flag replaces the safety car.
    assert codes(
        safety_car(10, "SAFETY CAR DEPLOYED"),
        message(15, flag="YELLOW", sector=3),
        message(40, "TRACK CLEAR", flag="CLEAR"),
    ) == [(0, "1"), (10, "4"), (40, "1")]


def test_red_flag_ends_at_the_restart():
    # Fails if a red flag lasts to the end of the race.
    assert codes(
        message(10, "RED FLAG", flag="RED"),
        message(900, "SESSION STARTED", category="SessionStatus"),
    ) == [(0, "1"), (10, "5"), (900, "1")]


def test_stewards_notes_do_not_deploy_the_safety_car():
    # Fails if the text is searched instead of the category and exact message.
    note = "FIA STEWARDS: SAFETY CAR DEPLOYED INFRINGEMENT"
    assert codes(message(10, note, category="Other")) == [(0, "1")]
    assert codes(message(10, "SAFETY CAR DEPLOYED", category="Other")) == [(0, "1")]


RACE = Race("2024_toy", "toy", 2024, "openf1", "fit", session_key=1)


@pytest.fixture
def raw_dir(tmp_path):
    """One car, three racing laps plus a cool-down lap, with a stop before lap 3."""
    folder = tmp_path / "openf1" / "2024" / "1_Toy"
    folder.mkdir(parents=True)

    def lap(number, second, **extra):
        return {
            "driver_number": 7, "lap_number": number, "lap_duration": 90.0,
            "date_start": (START + pd.Timedelta(f"{second}s")).isoformat(),
            "duration_sector_1": 30.0, "duration_sector_2": 30.0, "duration_sector_3": 30.0,
            "is_pit_out_lap": False, **extra,
        }

    files = {
        "race_control": [
            message(0, "GREEN LIGHT - PIT EXIT OPEN", flag="GREEN"),
            message(100, "SESSION STARTED", category="SessionStatus"),
        ],
        "laps": [
            lap(1, 5000), lap(2, 190), lap(3, 280, is_pit_out_lap=True), lap(4, 400),
        ],
        "stints": [
            {"driver_number": 7, "stint_number": 1, "lap_start": 1, "lap_end": 1, "compound": "SOFT", "tyre_age_at_start": 0},
            {"driver_number": 7, "stint_number": 2, "lap_start": 2, "lap_end": 4, "compound": "HARD", "tyre_age_at_start": 0},
        ],
        "drivers": [{"driver_number": 7, "name_acronym": "TOY"}],
        "weather": [{
            "date": START.isoformat(), "air_temperature": 20.0, "track_temperature": 30.0,
            "humidity": 50.0, "wind_speed": 1.0, "rainfall": 1,
        }],
        "session_result": [{"driver_number": 7, "number_of_laps": 3}],
    }
    for name, rows in files.items():
        (folder / f"{name}.json").write_text(json.dumps(rows), encoding="utf-8")
    return tmp_path


def test_reads_a_race_into_the_common_format(raw_dir):
    # Fails if the stint shift, race distance, in-lap, or rainfall is lost.
    frames = read_race(RACE, raw_dir, 0.01)
    laps = frames.laps
    assert laps["lap"].tolist() == [1, 2, 3]
    assert laps["compound"].tolist() == ["SOFT", "SOFT", "HARD"]
    assert laps["label"].tolist() == ["raw", "shifted", "raw"]
    assert laps["is_in_lap"].tolist() == [False, True, False]
    assert laps["is_out_lap"].tolist() == [False, False, True]
    assert frames.dropped_laps == 1
    assert frames.weather["rainfall"].tolist() == [True]


def test_first_lap_starts_with_the_session(raw_dir):
    # Fails if OpenF1's own lap 1 start (here 5000 s) is trusted.
    laps = read_race(RACE, raw_dir, 0.01).laps
    assert laps["lap_start_s"].tolist() == [100.0, 190.0, 280.0]
    assert laps["lap_end_s"].tolist() == [190.0, 280.0, 400.0]


def test_missing_folder_is_an_error(tmp_path):
    # Fails if an absent race reads as empty.
    with pytest.raises(CalibrationError, match="found 0"):
        read_race(RACE, tmp_path, 0.01)


def test_missing_file_is_an_error(raw_dir):
    # Fails if a required endpoint is optional.
    next(raw_dir.rglob("stints.json")).unlink()
    with pytest.raises(CalibrationError, match="stints.json"):
        read_race(RACE, raw_dir, 0.01)
