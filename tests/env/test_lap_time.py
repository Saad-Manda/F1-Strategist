import numpy as np
import pytest

from src.env import dynamics as d
from src.env.dynamics import Compound, TrackStatus, Weather

S, M, H, I, W = Compound
DRY, DAMP, WET = Weather
GREEN, SC, VSC = TrackStatus


@pytest.mark.parametrize(
    "age, expected",
    [
        (1, 0.2),  # fails if wear starts at zero
        (3, 0.6),  # fails if the cliff starts too early
        (4, 0.8 + 1.0),  # fails if the cliff starts too late
        (5, 1.0 + 4.0),  # fails if the cliff is linear
        (8, 1.6 + 4.0),  # fails if the cliff has no cap
    ],
)
def test_medium_degradation(toy_params, age, expected):
    assert d.tyre_degradation(M, age, toy_params) == pytest.approx(expected)


def test_cliff_severity_scales_the_cliff(toy_params):
    # Fails if severity is ignored, or squared with the laps.
    toy_params["compounds"]["MEDIUM"]["cliff_severity"] = 0.5
    assert d.tyre_degradation(M, 5, toy_params) == pytest.approx(1.0 + 2.0)


@pytest.mark.parametrize("age, expected", [(1, 2.0), (2, 0.6), (3, 0.0)])
def test_medium_warmup(toy_params, age, expected):
    # Fails if a warm-up lap is missing, doubled or never ends.
    assert d.out_lap_warmup(M, age, toy_params) == pytest.approx(expected)


def test_fuel_is_linear_and_zero_on_the_last_lap(toy_params):
    # Fails if the lap being run is counted, or a factor is dropped.
    assert [d.fuel_effect(n, toy_params) for n in (0, 1, 7)] == pytest.approx([0.0, 0.1, 0.7])


@pytest.mark.parametrize(
    "compound, age, after, weather, expected",
    [
        (M, 1, 7, DRY, 90.0 + 0.0 + 0.2 + 2.0 + 0.7),  # fails if a term is lost or doubled
        (S, 3, 0, DRY, 90.0 - 1.0 + 0.9 + 1.0),  # fails if the offset sign is wrong
        (H, 2, 4, DAMP, 90.0 + 1.0 + 0.2 + 0.9 + 0.4 + 6.0),  # fails without the weather penalty
        (I, 4, 2, DRY, 90.0 + 5.0 + 0.8 + 0.2 + 4.0),  # fails if the penalty table is transposed
        (W, 3, 1, WET, 90.0 + 8.0 + 0.3 + 0.1),
    ],
)
def test_green_lap_by_hand(toy_params, compound, age, after, weather, expected):
    lap = d.compute_lap_time(compound, age, after, weather, GREEN, toy_params)
    assert lap == pytest.approx(expected)


@pytest.mark.parametrize("status, expected", [(SC, 130.0), (VSC, 120.0)])
def test_flag_lap_does_not_depend_on_the_car(toy_params, status, expected):
    # Fails if SC and VSC are swapped, or the tyre still matters.
    laps = {
        d.compute_lap_time(c, age, after, w, status, toy_params)
        for c in Compound
        for w in Weather
        for age in (1, 8)
        for after in (0, 7)
    }
    assert laps == {expected}


@pytest.mark.parametrize("status", TrackStatus)
def test_noise_is_added_in_seconds(toy_params, status):
    # Fails if noise is lost under a flag, scaled or floored.
    for noise in (1.5, -60.0):
        noisy = d.compute_lap_time(M, 3, 2, DRY, status, toy_params, noise)
        assert noisy - d.compute_lap_time(M, 3, 2, DRY, status, toy_params) == pytest.approx(noise)


@pytest.mark.parametrize("status", TrackStatus)
def test_components_sum_to_the_lap_time(toy_params, status):
    # Fails if the lap time is computed somewhere else.
    args = (S, 2, 3, DAMP, status, toy_params, 0.25)
    parts = d.lap_time_components(*args)
    assert sum(parts.values()) == pytest.approx(d.compute_lap_time(*args))
    assert parts["noise"] == 0.25


def test_pit_loss(toy_params):
    # Fails if the discounts are swapped or not applied.
    losses = [d.compute_pit_loss(status, toy_params) for status in TrackStatus]
    assert losses == pytest.approx([20.0, 8.0, 12.0])


def test_table_equals_the_function_everywhere(toy_params):
    # Fails if an axis is swapped or an age is off by one.
    table = d.lap_time_table(toy_params)
    assert table.shape == (3, 3, 5, 8, 8)
    for s, w, c, age, after in np.ndindex(table.shape):
        assert table[s, w, c, age, after] == d.compute_lap_time(
            Compound(c), age + 1, after, Weather(w), TrackStatus(s), toy_params
        )


def test_missing_parameter_is_an_error(toy_params):
    # Fails if a default hides a missing number.
    del toy_params["warmup_second_lap_share"]
    with pytest.raises(KeyError):
        d.out_lap_warmup(M, 2, toy_params)
