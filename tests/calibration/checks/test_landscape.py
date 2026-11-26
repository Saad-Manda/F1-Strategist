import copy
import itertools

import pytest

from src.calibration.checks.landscape import Plan, Prices, _timing, landscape, sequences, stop_laps
from src.env.dynamics import Compound, TrackStatus, Weather, compute_lap_time, compute_pit_loss
from tests.calibration.checks.helpers import check_config

S, M, H = Compound.SOFT, Compound.MEDIUM, Compound.HARD
RULES = check_config()["checks"]["landscape"]


def lap_by_lap(plan: Plan, params) -> float:
    """The plan run one lap at a time, as the environment will (C1)."""
    laps = params["total_laps"]
    tyres = list(plan.compounds)
    compound, age, total = tyres.pop(0), 1, 0.0
    for lap in range(1, laps + 1):
        total += compute_lap_time(compound, age, laps - lap, Weather.DRY, TrackStatus.GREEN, params)
        if lap in plan.stops:
            total += compute_pit_loss(TrackStatus.GREEN, params)
            compound, age = tyres.pop(0), 1
        else:
            age += 1
    return total


@pytest.mark.parametrize(
    "plan",
    [Plan((S, M), (3,)), Plan((H, S), (1,)), Plan((M, M, S), (2, 6)), Plan((S, H, S, M), (1, 2, 7)), Plan((M,), ())],
)
def test_prices_match_the_race_model(toy_params, plan):
    # Fails if a stint is priced off by a lap, a tyre age, or the fuel still on board.
    assert Prices(toy_params).time(plan) == pytest.approx(lap_by_lap(plan, toy_params))


def test_plans_follow_the_rules():
    # Fails if a plan stops on the final lap, out of order, or breaks the two-compound rule.
    assert stop_laps(8, 1).ravel().tolist() == list(range(1, 8))
    assert len(stop_laps(8, 2)) == 21
    assert stop_laps(10, 2, step=3).tolist() == [[1, 4], [1, 7], [4, 7]]
    assert len(sequences(1)) == 6 and len(sequences(2)) == 24
    assert all(len(set(c)) > 1 for c in sequences(3))


def test_best_plan_is_the_best_of_all(toy_params):
    # Fails if the search misses a plan, or a 2- or 3-stop plan, or reports the wrong one.
    rules = RULES | {"three_stop_grid_laps": 1}
    found = landscape(toy_params, rules)
    prices = Prices(toy_params)
    every = [
        Plan(c, tuple(int(x) for x in laps))
        for n in (1, 2, 3)
        for c in sequences(n)
        for laps in stop_laps(8, n)
    ]
    best = min(every, key=prices.time)
    reported = Plan(tuple(Compound[c] for c in found["best"]["compounds"]), tuple(found["best"]["stops"]))
    assert found["best"]["time"] == pytest.approx(prices.time(best))
    assert lap_by_lap(reported, toy_params) == pytest.approx(prices.time(best))
    assert min(found["best_by_stops"].values()) == 0.0


def test_three_stops_are_searched(toy_params):
    # Fails if 3-stop plans are left out, which wins when stops are cheap and tyres wear fast.
    toy_params["pit_loss"] = 0.1
    found = landscape(toy_params, RULES | {"three_stop_grid_laps": 1})
    assert len(found["best"]["stops"]) == 3
    assert found["best_by_stops"]["3"] == 0.0


def even_race(params, wear=0.1, laps=20):
    """Same tyre twice over: linear wear, no cliff, no fuel, so moving the stop d laps off the middle costs wear * d^2."""
    params = copy.deepcopy(params)
    params |= {"total_laps": laps, "fuel": {"consumption_kg_per_lap": 0.0, "sensitivity_s_per_kg": 0.0}}
    for c in ("SOFT", "MEDIUM", "HARD"):
        params["compounds"][c] |= {"base_deg": wear, "cliff_severity": 0.0, "warmup_penalty": 0.0}
        params["compound_pace_offset"][c] = 0.0
    return params


def test_timing_by_hand(toy_params):
    # Fails if the shift cost or the window is measured off the wrong stop or the wrong laps.
    found = landscape(even_race(toy_params), RULES)
    assert found["best"]["stops"] == [10]
    assert found["stop_shift_cost"] == pytest.approx(0.1 * 5**2)
    assert found["window_laps"] == 7  # 0.1 * d^2 <= 1 for d in -3..3


def test_shift_takes_the_cheaper_side(toy_params):
    # Fails if the stop is only moved one way, when the other way is cheaper.
    # 21 laps: from a stop on lap 10 the cheaper move is 5 laps later, from lap 11 it is 5 earlier.
    # Either costs 0.1 * 20 s; the other side 0.1 * 30 s.
    prices = Prices(even_race(toy_params, laps=21))
    for stop in (10, 11):
        best = Plan((S, M), (stop,))
        assert _timing(prices, best, prices.time(best), RULES)[0] == pytest.approx(2.0)


def test_tyre_pairs_and_reported_numbers(toy_params):
    # Fails if a pair is priced on its worse order, or the reported gaps have the wrong sign.
    params = even_race(toy_params)
    params["compound_pace_offset"]["HARD"] = 1.0
    found = landscape(params, RULES)
    pairs = found["one_stop_pairs"]
    assert set(pairs) == {"MEDIUM-SOFT", "HARD-SOFT", "HARD-MEDIUM"}
    assert pairs["MEDIUM-SOFT"] == 0.0
    # HARD at 1 s a lap slower is best kept to 5 laps: 0.1 * (15 + 120) + 5 against 0.1 * 110.
    assert pairs["HARD-SOFT"] == pairs["HARD-MEDIUM"] == pytest.approx(7.5)
    # Twenty laps on one tyre lose 0.1 * 210 s; two stints of ten lose 0.1 * 110 s and a stop.
    assert found["no_stop_margin"] == pytest.approx(0.1 * 210 - (0.1 * 110 + toy_params["pit_loss"]))
    assert found["cliff_value"] == 0.0


def test_cliff_value(toy_params):
    # Fails if the cliff's cost to the best plan is lost or has the wrong sign.
    params = even_race(toy_params, laps=40)
    for c in ("SOFT", "MEDIUM", "HARD"):
        params["compounds"][c] |= {"cliff_age": 12, "cliff_severity": 0.5}
    assert landscape(params, RULES)["cliff_value"] > 1.0
