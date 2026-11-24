"""Each test names the code change that would make it fail."""

import numpy as np
import pandas as pd
import pytest

from src.data.cleaning.lap_flags import accurate_laps, lap_track_status
from tests.data.helpers import make_laps, make_status


def test_status_lists_every_code_active_during_the_lap():
    # Fails if only the status at the start or end of the lap is kept.
    status = make_status((0, "1"), (150, "4"), (250, "1"))
    laps = pd.DataFrame({"lap_start_s": [0.0, 100, 200, 300], "lap_end_s": [100.0, 200, 300, 400]})
    assert lap_track_status(laps, status) == ["1", "14", "14", "1"]


def test_status_change_on_the_line_belongs_to_the_next_lap():
    # Fails if the interval comparison includes its end.
    status = make_status((0, "1"), (100, "4"))
    laps = pd.DataFrame({"lap_start_s": [0.0, 100], "lap_end_s": [100.0, 200]})
    assert lap_track_status(laps, status) == ["1", "4"]


def test_status_is_unknown_without_lap_times():
    # Fails if a lap without times is called green.
    laps = pd.DataFrame({"lap_start_s": [np.nan, 0.0], "lap_end_s": [100.0, np.nan]})
    assert lap_track_status(laps, make_status((0, "1"))) == ["", ""]


@pytest.mark.parametrize(
    "change, expected",
    [
        ({}, True),
        ({"sector1_s": 31.0}, False),
        ({"sector2_s": np.nan}, False),
        ({"lap_time_s": np.nan}, False),
        ({"is_in_lap": True}, False),
        ({"is_out_lap": True}, False),
        ({"lap": 1}, False),
    ],
)
def test_accurate_lap_needs_consistent_times_and_no_stop(change, expected):
    # Fails if the matching condition is removed.
    laps = make_laps(1, 2).iloc[[1]].assign(**change)
    assert accurate_laps(laps, 0.01).tolist() == [expected]
