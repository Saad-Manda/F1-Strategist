"""Checks for lab p6-06: your three tests, graded mutation-style. Given code: nothing to edit here."""

import os
import sys
from functools import partial

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ledger  # noqa: E402
import mini_race  # noqa: E402


def factory(*bugs):
    return partial(mini_race.Race, bugs=bugs)


CASES = [
    ("E1", ledger.check_time_counted_once),
    ("E2", ledger.check_pass_changes_the_race),
    ("E3", ledger.check_reward_matches_time),
]


@pytest.mark.parametrize("bug,check", CASES, ids=[c[0] for c in CASES])
def test_your_check_passes_the_reference(bug, check):
    try:
        check(factory())
    except AssertionError as err:
        raise AssertionError(f"Your {bug} check fails on the reference race, which has no bugs: it is wrong about correct behaviour. It said: {err}") from None


@pytest.mark.parametrize("bug,check", CASES, ids=[c[0] for c in CASES])
def test_your_check_catches_its_bug(bug, check):
    try:
        check(factory(bug))
    except AssertionError:
        return
    raise AssertionError(f"Your {bug} check passed on a race that has bug {bug}: it does not catch it.")


def test_your_checks_catch_the_plan_as_written():
    """All three bugs at once, as the plan's pseudocode has them."""
    caught = 0
    for _, check in CASES:
        try:
            check(factory("E1", "E2", "E3"))
        except AssertionError:
            caught += 1
    assert caught == 3, f"With all three bugs present, {caught} of your 3 checks fail."


def test_the_plans_own_test_misses_all_three():
    """(given) The plan's test_multi_env_positions_sum_correctly, translated: positions are 1..N."""
    for bugs in ((), ("E1",), ("E2",), ("E3",), ("E1", "E2", "E3")):
        race = factory(*bugs)(passing=True, seed=0)
        for _ in range(10):
            race.step(mini_race.STAY)
        assert sorted(c.position for c in race.cars) == [1, 2, 3], "(given) the plan's test passes"
