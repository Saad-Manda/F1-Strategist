"""The toy circuit is the base of many later tests, so its own numbers are checked."""

import pytest


@pytest.mark.parametrize("chain", ["status_transition", "weather_transition"])
def test_toy_chains_are_square_and_stochastic(toy_params, chain):
    # Fails if a toy probability is mistyped.
    rows = toy_params[chain]
    for row in rows.values():
        assert set(row) == set(rows)
        assert sum(row.values()) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "start, chain",
    [("status_start", "status_transition"), ("weather_start", "weather_transition")],
)
def test_toy_starts_are_distributions(toy_params, start, chain):
    # Fails if a start probability is mistyped or a state is missing.
    assert set(toy_params[start]) == set(toy_params[chain])
    assert sum(toy_params[start].values()) == pytest.approx(1.0)
