import pandas as pd
import pytest

from src.calibration.conditions.timeline import leader_timeline
from src.common.errors import CalibrationError


def laps(*rows):
    return pd.DataFrame(rows, columns=["driver", "lap", "lap_start_s", "lap_end_s"])


TWO_CARS = laps(
    ("AAA", 1, 10.0, 100.0),
    ("BBB", 1, 11.0, 101.0),
    ("AAA", 2, 100.0, 195.0),
    ("BBB", 2, 101.0, 190.0),
)


def test_leader_is_the_first_car_to_finish_the_lap():
    # Fails if the first listed car or the last finisher is used.
    assert leader_timeline(TWO_CARS, 2)["end_s"].tolist() == [100.0, 190.0]


def test_laps_join_without_gaps():
    # Fails if a lap starts at the new leader's own start instead of the previous leader's end.
    assert leader_timeline(TWO_CARS, 2)["start_s"].tolist() == [10.0, 100.0]


def test_missing_lap_is_refused():
    # Fails if a lap nobody finished is skipped silently.
    with pytest.raises(CalibrationError, match=r"\[3\]"):
        leader_timeline(TWO_CARS, 3)


def test_missing_first_start_is_refused():
    # Fails if a missing start becomes NaN.
    with pytest.raises(CalibrationError, match="start time"):
        leader_timeline(TWO_CARS.assign(lap_start_s=float("nan")), 2)


def test_time_going_backwards_is_refused():
    # Fails if the order check is dropped.
    with pytest.raises(CalibrationError, match="backwards"):
        leader_timeline(laps(("AAA", 1, 10.0, 100.0), ("AAA", 2, 100.0, 90.0)), 2)


def test_lap_starts_when_the_previous_leader_finished():
    # Fails if a lap's own start times are used.
    late = laps(("AAA", 1, 10.0, 100.0), ("AAA", 2, 105.0, 195.0))
    assert leader_timeline(late, 2)["start_s"].tolist() == [10.0, 100.0]
