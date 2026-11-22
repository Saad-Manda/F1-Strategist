"""Checks for lab p35-02. Given code: nothing to edit here."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import replacement as rp  # noqa: E402
from replacement import HORIZON, KEEP, REPLACE, START_AGE  # noqa: E402


def test_step_keep():
    cost, next_age = rp.step(3, KEEP)
    assert cost == pytest.approx(6.5), "Keeping a 3-year-old machine costs running_cost(3) = 2 + 1.5 * 3."
    assert next_age == 4, "A kept machine is one year older next year."


def test_step_replace():
    cost, next_age = rp.step(5, REPLACE)
    assert cost == pytest.approx(12.0), "Replacing costs the price of a new machine plus one year of running a NEW machine (age 0)."
    assert next_age == 1, "The new machine has worked one year by the start of next year."
    assert rp.step(0, REPLACE) == rp.step(9, REPLACE), "What a replacement costs does not depend on the age of the machine being thrown away."


def test_terminal_values_are_zero():
    V, _ = rp.backward_induction()
    for age in range(0, START_AGE + HORIZON + 1):
        assert V.get((HORIZON + 1, age)) == 0.0, f"V[({HORIZON + 1}, {age})] should be 0.0: nothing follows the last year."


def test_last_year_by_hand():
    V, policy = rp.backward_induction()
    for age in rp.reachable_ages(HORIZON, START_AGE):
        keep, replace = rp.running_cost(age), 12.0
        assert V[(HORIZON, age)] == pytest.approx(min(keep, replace)), (
            f"In the last year nothing comes after, so the value of age {age} is just the cheaper of keeping ({keep}) and replacing ({replace})."
        )
        assert policy[(HORIZON, age)] == (KEEP if keep <= replace else REPLACE)


def test_one_cell_by_hand():
    V, policy = rp.backward_induction()
    # year 5, age 6: KEEP = 11 + V[(6, 7)] = 11 + 12 = 23; REPLACE = 12 + V[(6, 1)] = 12 + 3.5 = 15.5
    assert V[(5, 6)] == pytest.approx(15.5), "Year 5, age 6: keeping costs 11 + 12, replacing costs 12 + 3.5. The value is the smaller total."
    assert policy[(5, 6)] == REPLACE, "Year 5, age 6: replacing is cheaper once next year's value is counted."


@pytest.mark.parametrize("horizon", range(1, 10))
def test_matches_brute_force(horizon):
    V, _ = rp.backward_induction(horizon=horizon)
    assert V[(1, START_AGE)] == pytest.approx(rp.brute_force_best(horizon=horizon)), (
        f"For a {horizon}-year horizon the value at the start should equal the cheapest of all {2 ** horizon} plans."
    )


def test_other_starting_ages():
    for start_age in (0, 1, 4):
        V, _ = rp.backward_induction(start_age=start_age)
        assert V[(1, start_age)] == pytest.approx(rp.brute_force_best(start_age=start_age)), (
            f"Starting with a machine of age {start_age}, the value should still equal the brute-force best."
        )


def test_replaying_the_policy_pays_exactly_the_value():
    V, policy = rp.backward_induction()
    actions, total = rp.replay_policy(policy)
    assert len(actions) == HORIZON, "One action per year."
    assert total == pytest.approx(V[(1, START_AGE)]), "Following the policy forward should cost exactly V at the start: the table and the plan are the same answer."
    assert actions.count(REPLACE) == 1, "With these numbers the best plan replaces the machine exactly once."


def test_each_state_is_solved_once(monkeypatch):
    calls = {"n": 0}
    real_step = rp.step

    def counting_step(age, action):
        calls["n"] += 1
        return real_step(age, action)

    monkeypatch.setattr(rp, "step", counting_step)
    rp.backward_induction(horizon=12)
    states = sum(len(rp.reachable_ages(year, START_AGE)) for year in range(1, 13))
    assert calls["n"] > 0, "backward_induction should get its costs and next ages from step()."
    assert calls["n"] <= 2 * states, (
        f"A 12-year horizon has {states} reachable (year, age) states and two actions each, so {2 * states} calls to step() are enough. "
        f"You made {calls['n']}. Each state should be solved once and its value reused (brute force would need {12 * 2 ** 12})."
    )


def test_looking_one_year_ahead_is_not_enough():
    V, _ = rp.backward_induction()
    assert rp.myopic_total() > V[(1, START_AGE)] + 1.0, (
        "The plan that only compares this year's two costs should come out clearly dearer than the optimal plan."
    )
