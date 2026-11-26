"""Each test names the code change that would make it fail."""

import pandas as pd

from src.data.sources.fastf1 import _laps


def raw_laps(**columns):
    seconds = {
        "LapTime": 90.5, "LapStartTime": 100.0, "Time": 190.5, "Sector1Time": 30.0,
        "Sector2Time": 30.0, "Sector3Time": 30.5, "PitInTime": None, "PitOutTime": None,
    }
    plain = {
        "Driver": "VER", "DriverNumber": "1", "LapNumber": 2.0, "Stint": 1.0,
        "Compound": "SOFT", "TyreLife": 2.0,
    }
    row = {**seconds, **plain, **columns}
    frame = pd.DataFrame({key: [value] for key, value in row.items()})
    for key in seconds:
        frame[key] = pd.to_timedelta(frame[key].astype(float), unit="s")
    return frame


def test_times_become_seconds():
    # Fails if a time is left as a timedelta or start and end are swapped.
    lap = _laps(raw_laps()).iloc[0]
    assert lap["lap_time_s"] == 90.5
    assert (lap["lap_start_s"], lap["lap_end_s"]) == (100.0, 190.5)


def test_leaving_the_pits_on_lap_one_is_not_an_out_lap():
    # Fails if a pit lane start counts as a tyre stop.
    assert not _laps(raw_laps(LapNumber=1.0, PitOutTime=50.0))["is_out_lap"].iloc[0]
    assert _laps(raw_laps(LapNumber=2.0, PitOutTime=50.0))["is_out_lap"].iloc[0]


def test_pit_entry_marks_the_in_lap():
    # Fails if the in-lap is read from the wrong column.
    lap = _laps(raw_laps(PitInTime=180.0)).iloc[0]
    assert lap["is_in_lap"] and not lap["is_out_lap"]


def test_invalid_compound_is_missing_and_has_no_age():
    # Fails if an unlabelled lap keeps a tyre age (2022 Austria).
    for value in (None, "None", "TEST_UNKNOWN"):
        lap = _laps(raw_laps(Compound=value)).iloc[0]
        assert lap["compound"] == "UNKNOWN"
        assert lap["label"] == "missing"
        assert pd.isna(lap["tyre_age"])


def test_compound_is_upper_case():
    # Fails if "Soft" is treated as unknown.
    assert _laps(raw_laps(Compound="Soft"))["compound"].iloc[0] == "SOFT"
