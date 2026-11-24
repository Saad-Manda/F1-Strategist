"""Each test names the code change that would make it fail."""

import pandas as pd
import pytest

from src.common.errors import ContractError
from src.data.cleaning.assemble import build_frames
from tests.data.helpers import make_laps, make_status, make_weather


def build(laps, race_laps=3):
    return build_frames(laps, make_weather(), make_status((0, "1")), race_laps, 0.01)


def test_laps_after_the_finish_are_dropped_and_counted():
    # Fails if a cool-down lap survives.
    frames = build(make_laps(2, 4))
    assert frames.laps["lap"].max() == 3
    assert frames.dropped_laps == 2


def test_missing_column_is_a_contract_error():
    # Fails if a reader can omit a column.
    with pytest.raises(ContractError, match="tyre_age"):
        build(make_laps(1, 3).drop(columns="tyre_age"))


def test_repeated_lap_is_a_contract_error():
    # Fails if a duplicated lap is counted twice.
    laps = make_laps(1, 3)
    with pytest.raises(ContractError, match="repeats"):
        build(pd.concat([laps, laps.iloc[[0]]]))


def test_rows_are_sorted_by_driver_and_lap():
    # Fails if the order depends on the source.
    frames = build(make_laps(2, 3).iloc[::-1])
    assert frames.laps[["driver_number", "lap"]].values.tolist() == [
        [1, 1], [1, 2], [1, 3], [2, 1], [2, 2], [2, 3],
    ]
