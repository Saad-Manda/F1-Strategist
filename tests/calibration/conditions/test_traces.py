from types import SimpleNamespace

import pandas as pd
import pytest

from src.calibration.conditions.table import RaceConditions, lap_sensors
from src.calibration.conditions.traces import TRACE_DTYPES, build_trace
from src.common.errors import CalibrationError

WEATHER = pd.DataFrame(
    {
        "time_s": [5.0, 15.0, 25.0],
        "rainfall": [False, True, False],
        "air_temp_c": [10.0, 20.0, 30.0],
        "track_temp_c": [10.0, 20.0, 30.0],
    }
)


def conditions(status, rejection=""):
    n = len(status)
    table = pd.DataFrame(
        {
            "status": pd.array(status, dtype="string"),
            "regime": pd.array(["DRY"] * (n - 1) + ["DAMP"], dtype="string"),
            "inter_share": 0.0,
            "wet_share": 0.0,
            "rainfall": [False] * (n - 1) + [True],
            "air_temp_c": 20.0,
            "track_temp_c": 30.0,
        },
        index=pd.RangeIndex(1, n + 1, name="lap"),
    )
    return RaceConditions(SimpleNamespace(id="toy", role="holdout"), table, rejection)


def test_padding_repeats_weather_but_not_the_safety_car():
    # Fails if padding extends a safety car, loses the weather, or is not marked.
    trace = build_trace(conditions(["GREEN", "SC"]), 4, 3)
    assert trace["track_status"].tolist() == ["GREEN", "SC", "GREEN", "GREEN"]
    assert trace["weather_regime"].tolist() == ["DRY", "DAMP", "DAMP", "DAMP"]
    assert trace["padded"].tolist() == [False, False, True, True]


def test_longer_race_is_cut():
    # Fails if a trace is longer than the race distance.
    assert build_trace(conditions(["GREEN"] * 5), 3, 3)["lap"].tolist() == [1, 2, 3]


def test_red_laps_become_sc_and_stay_marked():
    # Fails if the simulator sees RED, or the red flag is lost (D21).
    trace = build_trace(conditions(["GREEN", "RED", "GREEN"]), 3, 3)
    assert trace["track_status"].tolist() == ["GREEN", "SC", "GREEN"]
    assert trace["red_flag"].tolist() == [False, True, False]


def test_short_race_is_refused():
    # Fails if a 3-lap race is padded to full distance.
    with pytest.raises(CalibrationError, match="2 of 6"):
        build_trace(conditions(["GREEN"] * 2), 6, 3)


def test_rejected_weather_is_refused():
    # Fails if a race without weather labels gets a trace.
    with pytest.raises(CalibrationError, match="known tyres"):
        build_trace(conditions(["GREEN"] * 3, "known tyres fall to 0%"), 3, 3)


def test_columns_types_and_role():
    # Fails if a column is missing, renamed or of another type, or the role is lost (D30).
    trace = build_trace(conditions(["GREEN"] * 3), 3, 3)
    assert {c: str(t) for c, t in trace.dtypes.items()} == TRACE_DTYPES
    assert set(trace["role"]) == {"holdout"}


def test_sensors_use_the_samples_inside_the_lap():
    # Fails if neighbouring samples leak in, or rain in part of a lap is lost.
    timeline = pd.DataFrame(
        {"start_s": [0.0, 20.0, 30.0], "end_s": [20.0, 30.0, 40.0]}, index=[1, 2, 3]
    )
    sensors = lap_sensors(timeline, WEATHER)
    assert sensors["rainfall"].tolist() == [True, False, False]
    assert sensors["air_temp_c"].tolist() == [15.0, 30.0, 30.0]


def test_lap_before_the_first_sample_is_refused():
    # Fails if a lap gets a later sample or NaN.
    with pytest.raises(CalibrationError, match="no weather sample"):
        lap_sensors(pd.DataFrame({"start_s": [0.0], "end_s": [4.0]}, index=[1]), WEATHER)


def test_the_padding_limit_itself_is_allowed():
    # Fails if > becomes >=.
    assert len(build_trace(conditions(["GREEN"] * 3), 6, 3)) == 6
