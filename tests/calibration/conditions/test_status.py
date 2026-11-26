import pandas as pd
import pytest

from src.calibration.conditions.status import lap_status
from src.common.errors import CalibrationError


def status(*messages):
    ends = pd.Series([100.0] * 8, index=range(1, 9)).cumsum()
    timeline = pd.DataFrame({"start_s": ends.shift(1, fill_value=0.0), "end_s": ends})
    table = pd.DataFrame(messages, columns=["time_s", "code"])
    return lap_status(timeline, table).tolist()


@pytest.mark.parametrize(
    "code, begin, end, expected",
    [
        ("4", 190.0, 210.0, "SC"),  # fails if a late safety car is missed
        ("4", 110.0, 195.0, "GREEN"),  # fails if a safety car that has gone still counts
        ("4", 200.0, 210.0, "SC"),  # fails if a flag shown at the line is missed
        ("6", 190.0, 210.0, "VSC"),  # fails if VSC is named SC
        ("7", 190.0, 210.0, "VSC"),  # fails if VSC ending is ignored
        ("2", 190.0, 210.0, "GREEN"),  # fails if yellow counts as neutralised
        ("5", 110.0, 111.0, "RED"),  # fails if red needs to be active at the line
    ],
)
def test_second_lap(code, begin, end, expected):
    assert status((0.0, "1"), (begin, code), (end, "1"))[1] == expected


def test_status_before_the_first_message_is_refused():
    # Fails if a lap takes a later status.
    with pytest.raises(CalibrationError, match="no track status"):
        status((150.0, "1"))


def test_last_status_stays_until_the_end():
    # Fails if the last message has no duration.
    assert status((0.0, "1"), (600.0, "4"))[6:] == ["SC", "SC"]


def test_the_lap_after_a_red_flag_is_red_too():
    # Fails if the restart lap counts as racing, or the laps after it stay RED.
    result = status((0.0, "1"), (110.0, "5"), (190.0, "1"))
    assert result == ["GREEN", "RED", "RED"] + ["GREEN"] * 5


def test_red_flag_without_an_end_lasts_until_the_finish():
    # Fails if the last message has no duration.
    assert status((0.0, "1"), (450.0, "5"))[4:] == ["RED"] * 4
