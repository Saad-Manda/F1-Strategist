"""Checks for the Phase 3.5 capstone, one group per stage. Given code: nothing to edit here."""

import os
import pathlib
import sys
from itertools import product

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "labs" / "labkit").exists())))

import toy_solver as ts  # noqa: E402
from labs.labkit import toyrace as tr  # noqa: E402
from labs.labkit.toyrace import A, B, DRY, PIT_A, PIT_B, STAY_OUT, WET, RaceModel  # noqa: E402

H = tr.HORIZON


def brute_force(model):
    """Cheapest of all 3 ** horizon plans: dry, green, no rules."""
    best = None
    for plan in product(tr.ALL_ACTIONS, repeat=model.horizon):
        compound, age, total = A, 1, 0.0
        for lap, action in enumerate(plan, 1):
            total += model.cost(lap, compound, age, action)
            compound, age = model.next_tyre(compound, age, action)
        best = total if best is None else min(best, total)
    return best


def mean_and_error(model, policy_fn, n=4000, seed=0, start_weather=DRY):
    rng = np.random.default_rng(seed)
    times = np.array([tr.simulate(model, policy_fn, rng, start_weather)["time"] for _ in range(n)])
    return times.mean(), times.std() / np.sqrt(n)


# ---------------------------------------------------------------- stage 1: deterministic


def test_stage1_terminal_row():
    V, _ = ts.solve_dry_green(RaceModel())
    for c in (A, B):
        for age in range(1, H + 2):
            assert V.get((H + 1, c, age)) == 0.0, f"V[({H + 1}, {c}, {age})] should be 0.0: nothing follows the last lap."


def test_stage1_last_lap_never_pits():
    model = RaceModel()
    V, policy = ts.solve_dry_green(model)
    for c in (A, B):
        for age in range(1, H + 1):
            assert policy[(H, c, age)] == STAY_OUT, "On the last lap a pit stop can only add time."
            assert V[(H, c, age)] == pytest.approx(model.cost(H, c, age, STAY_OUT))


@pytest.mark.parametrize("horizon", [3, 6, 8])
def test_stage1_matches_brute_force(horizon):
    model = RaceModel(horizon=horizon)
    V, _ = ts.solve_dry_green(model)
    assert V[(1, A, 1)] == pytest.approx(brute_force(model)), (
        f"For a {horizon}-lap race the value at the start should equal the cheapest of all {3 ** horizon} plans."
    )


def test_stage1_full_race():
    model = RaceModel()
    V, policy = ts.solve_dry_green(model)
    assert V[(1, A, 1)] == pytest.approx(222.95), f"The best 20-lap race with no rules takes 222.95 s; got {V[(1, A, 1)]:.3f}."
    compound, age, total, stops = A, 1, 0.0, 0
    for lap in range(1, H + 1):
        action = policy[(lap, compound, age)]
        total += model.cost(lap, compound, age, action)
        stops += action != STAY_OUT
        compound, age = model.next_tyre(compound, age, action)
    assert total == pytest.approx(V[(1, A, 1)]), "Following the policy forward should take exactly V at the start."
    assert stops == 2, "With no rules, the best race stops twice."


# ---------------------------------------------------------------- stage 2: the safety car


def test_stage2_no_hazard_gives_stage1_back():
    V, _ = ts.solve_with_safety_car(RaceModel(sc_hazard=0.0))
    assert V[(1, A, 1, 0)] == pytest.approx(222.95), (
        "With a hazard of 0 the safety car never appears, so the answer from a green start should be stage 1's 222.95."
    )


def test_stage2_expected_time_rises():
    V, _ = ts.solve_with_safety_car(RaceModel())
    assert V[(1, A, 1, 0)] == pytest.approx(230.737, abs=2e-3), f"Expected race time with the safety car should be 230.737 s; got {V[(1, A, 1, 0)]:.3f}."


def test_stage2_safety_car_changes_the_decision():
    _, policy = ts.solve_with_safety_car(RaceModel())
    earlier = [
        (lap, c, age)
        for (lap, c, age, sc), action in policy.items()
        if sc == 1 and action != STAY_OUT and policy[(lap, c, age, 0)] == STAY_OUT
    ]
    assert earlier, "There should be states where the best move is to stay out under green and to pit under the safety car: the stop is cheaper then."


def test_stage2_value_matches_simulated_races():
    model = RaceModel()
    V, policy = ts.solve_with_safety_car(model)
    mean, error = mean_and_error(model, lambda lap, c, age, sc, used, w: policy[(lap, c, age, sc)])
    assert abs(mean - V[(1, A, 1, 0)]) < 4 * error, (
        f"4,000 simulated races averaged {mean:.2f} s; your table says {V[(1, A, 1, 0)]:.2f} s. They should agree within {4 * error:.2f}."
    )


# ---------------------------------------------------------------- stage 3: the rules


def test_stage3_policy_only_uses_legal_actions():
    model = RaceModel()
    _, policy = ts.solve_with_rules(model)
    for (lap, c, age, sc, used), action in policy.items():
        assert action in model.legal_actions(lap, c, DRY, used), f"Illegal action {action} chosen at lap {lap}, compound {c}, used_both={used}."


def test_stage3_rules_never_make_the_race_faster():
    model = RaceModel()
    free, _ = ts.solve_with_safety_car(model)
    ruled, _ = ts.solve_with_rules(model)
    assert ruled[(1, A, 1, 0, False)] >= free[(1, A, 1, 0)] - 1e-9, "A rule can only remove options. It can never make the best race faster."
    assert ruled[(1, A, 1, 0, False)] == pytest.approx(231.918, abs=2e-3), f"Expected race time under the rules should be 231.918 s; got {ruled[(1, A, 1, 0, False)]:.3f}."


def test_stage3_forced_stop_at_the_end():
    _, policy = ts.solve_with_rules(RaceModel())
    for sc in (0, 1):
        assert policy[(H, A, H, sc, False)] == PIT_B, "On the last lap, still on the starting compound, the only legal move is to fit the other one."


def test_stage3_every_race_uses_both_compounds():
    model = RaceModel()
    _, policy = ts.solve_with_rules(model)
    rng = np.random.default_rng(1)
    for _ in range(300):
        race = tr.simulate(model, lambda lap, c, age, sc, used, w: policy[(lap, c, age, sc, used)], rng)
        assert race["used_both"], "A race driven by your policy finished without using both compounds."


# ---------------------------------------------------------------- stage 4: the weather


def test_stage4_expect_next_weights_four_outcomes():
    model = RaceModel(weather="markov")  # from green: P(sc) = 0.06; from DRY: P(WET) = 0.1
    V = {(6, B, 1, 0, True, DRY): 100.0, (6, B, 1, 0, True, WET): 200.0, (6, B, 1, 1, True, DRY): 300.0, (6, B, 1, 1, True, WET): 400.0}
    got = ts.expect_next(model, V, 5, B, 1, True, 0, DRY)
    want = 0.94 * 0.9 * 100 + 0.94 * 0.1 * 200 + 0.06 * 0.9 * 300 + 0.06 * 0.1 * 400
    assert got == pytest.approx(want), f"Each of the four next states is weighted by P(sc') * P(weather'). Expected {want:.2f}, got {got:.2f}."


def test_stage4_unchanging_weather_gives_stage3_back():
    V, _ = ts.solve_full(RaceModel())
    assert V[(1, A, 1, 0, False, DRY)] == pytest.approx(231.918, abs=2e-3), (
        "When the weather never changes, a dry start is stage 3's race exactly: 231.918 s."
    )
    assert V[(1, A, 1, 0, False, WET)] == pytest.approx(367.847, abs=2e-3), "A race that is wet throughout should take 367.847 s."


def test_stage4_markov_weather():
    V, _ = ts.solve_full(RaceModel(weather="markov"))
    dry, wet = V[(1, A, 1, 0, False, DRY)], V[(1, A, 1, 0, False, WET)]
    assert dry == pytest.approx(254.558, abs=2e-3), f"Expected time from a dry start with changing weather should be 254.558 s; got {dry:.3f}."
    assert wet == pytest.approx(268.984, abs=2e-3), f"From a wet start it should be 268.984 s; got {wet:.3f}."
    assert wet > dry, "Starting in the wet should cost more than starting in the dry."


def test_stage4_known_weather_trace():
    V, _ = ts.solve_full(RaceModel(weather_trace=[DRY] * H))
    assert V[(1, A, 1, 0, False, DRY)] == pytest.approx(231.918, abs=2e-3), "A known trace that is dry on every lap is stage 3's race again."


def test_stage4_value_matches_simulated_races():
    model = RaceModel(weather="markov")
    V, policy = ts.solve_full(model)
    mean, error = mean_and_error(model, lambda *state: policy[state])
    assert abs(mean - V[(1, A, 1, 0, False, DRY)]) < 4 * error, (
        f"4,000 simulated races averaged {mean:.2f} s; your table says {V[(1, A, 1, 0, False, DRY)]:.2f} s. They should agree within {4 * error:.2f}."
    )


# ---------------------------------------------------------------- stage 5: the sanity check


def test_stage5_baseline():
    assert ts.best_one_stop_time(RaceModel()) == pytest.approx(224.49), "The best simple one-stop race (A, then B) takes 224.49 s."
    assert ts.best_one_stop_time(RaceModel(horizon=6)) == pytest.approx(67.2), "For a 6-lap race the best simple one-stop takes 67.20 s."


def test_stage5_looks_absurd():
    assert ts.looks_absurd(180.0, 220.0) is True, "Beating a 220 s baseline by 40 s is more than 15% of it."
    assert ts.looks_absurd(215.0, 220.0) is False, "Beating it by 5 s is plausible."
    assert ts.looks_absurd(230.0, 220.0) is False, "A solver that is slower than the baseline is not 'too good'."
    assert ts.looks_absurd(215.0, 220.0, margin=0.01) is True, "The margin argument should be used."


def test_stage5_correct_model_passes_the_sanity_check():
    model = RaceModel(sc_hazard=0.0)  # no safety car, so the comparison with the baseline is like for like
    V, _ = ts.solve_full(model)
    solved, baseline = V[(1, A, 1, 0, False, DRY)], ts.best_one_stop_time(model)
    assert solved <= baseline + 1e-9, "An exact solver searches every plan, so no simple plan can beat it."
    assert not ts.looks_absurd(solved, baseline)


def test_stage5_planted_bug_is_caught():
    broken = RaceModel(sc_hazard=0.0, pit_loss=-4.0)  # the planted bug: a pit stop GAINS four seconds
    V, policy = ts.solve_full(broken)
    solved, baseline = V[(1, A, 1, 0, False, DRY)], ts.best_one_stop_time(broken)
    assert ts.looks_absurd(solved, baseline), (
        f"With the sign of the pit loss flipped the solver reports {solved:.1f} s against a baseline of {baseline:.1f} s. The check should flag that."
    )
    race = tr.simulate(broken, lambda *state: policy[state], np.random.default_rng(0))
    assert sum(a != STAY_OUT for a in race["actions"]) >= 15, "The 'optimal' policy of the broken model should be pitting on almost every lap."
