"""Checks for lab p35-03. Given code: nothing to edit here."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import faulty_machine as fm  # noqa: E402
from faulty_machine import FAULTY, HEALTHY, HORIZON, KEEP, REPLACE, START_AGE  # noqa: E402

NO_FAULTS_ANSWER = 38.5  # lab p35-02's exact answer for the same workshop


def test_prediction_is_committed():
    if fm.MY_PREDICTION is None:
        raise NotImplementedError("TODO p35-03: set MY_PREDICTION in faulty_machine.py before anything else")
    assert fm.MY_PREDICTION in {"higher", "lower", "same"}, 'MY_PREDICTION should be "higher", "lower" or "same".'


def test_fault_prob():
    assert fm.fault_prob(1) == pytest.approx(0.08)
    assert fm.fault_prob(5) == pytest.approx(0.40), "The chance of a fault grows by FAULT_RATE for every year of age."
    assert fm.fault_prob(40) == 1.0, "A probability can never be more than 1."


def test_step_keep_healthy():
    cost, next_age, p = fm.step(3, HEALTHY, KEEP)
    assert cost == pytest.approx(6.5), "A healthy machine costs just its running cost."
    assert next_age == 4
    assert p == pytest.approx(0.32), "The chance of a fault next year uses the age the machine will have NEXT year (4), not its age now."


def test_step_keep_faulty():
    cost, next_age, p = fm.step(3, FAULTY, KEEP)
    assert cost == pytest.approx(12.5), "Running a faulty machine costs FAULT_COST on top of the running cost."
    assert next_age == 4
    assert p == 1.0, "A fault never repairs itself: a faulty machine that is kept is certainly faulty next year."


def test_step_replace():
    for faulty in (HEALTHY, FAULTY):
        cost, next_age, p = fm.step(5, faulty, REPLACE)
        assert cost == pytest.approx(12.0), "A replacement costs the same whether or not the old machine was faulty: the fault leaves with it."
        assert next_age == 1
        assert p == pytest.approx(0.08), "A new machine can be faulty next year too, with the probability for age 1."


def test_expected_value_is_a_weighted_average():
    V = {(4, 2, HEALTHY): 10.0, (4, 2, FAULTY): 30.0}
    assert fm.expected_value(V, 4, 2, 0.0) == pytest.approx(10.0), "With no chance of a fault, the expectation is just the healthy value."
    assert fm.expected_value(V, 4, 2, 1.0) == pytest.approx(30.0), "With a certain fault, the expectation is just the faulty value."
    assert fm.expected_value(V, 4, 2, 0.25) == pytest.approx(15.0), "0.25 * 30 + 0.75 * 10 = 15."


def test_terminal_values_are_zero():
    V, _ = fm.solve()
    for age in range(0, START_AGE + HORIZON + 1):
        for f in (HEALTHY, FAULTY):
            assert V.get((HORIZON + 1, age, f)) == 0.0, "Nothing follows the last year, in either condition."


def test_one_cell_by_hand():
    V, policy = fm.solve()
    # year 5, age 1, healthy, KEEP: 3.5 now. Next year the machine is 2 years old and faulty with p = 0.16.
    # V[(6, 2, FAULTY)] = 5 + 6 = 11, V[(6, 2, HEALTHY)] = 5.  Expectation = 0.16 * 11 + 0.84 * 5 = 5.96.
    assert V[(5, 1, HEALTHY)] == pytest.approx(9.46), (
        "Year 5, age 1, healthy: keeping costs 3.5 now plus an expected 0.16 * 11 + 0.84 * 5 = 5.96 next year."
    )
    assert policy[(5, 1, HEALTHY)] == KEEP


def test_no_risk_gives_back_the_deterministic_answer(monkeypatch):
    monkeypatch.setattr(fm, "FAULT_RATE", 0.0)
    V, _ = fm.solve()
    assert V[(1, START_AGE, HEALTHY)] == pytest.approx(NO_FAULTS_ANSWER), (
        "With FAULT_RATE = 0 nothing random is left, so the answer should be lab p35-02's 38.5 exactly. "
        "If it is not, the expectation is changing something it should leave alone."
    )


def test_risk_makes_the_expected_cost_higher():
    V, _ = fm.solve()
    start = V[(1, START_AGE, HEALTHY)]
    assert start > NO_FAULTS_ANSWER + 1.0, (
        f"A fault can only ever add cost, so the expected total ({start:.2f}) should be clearly above the no-fault answer (38.5)."
    )
    assert start == pytest.approx(41.0147, abs=1e-3), f"The expected total from the start should be 41.01, got {start:.4f}."


def test_a_faulty_machine_is_worth_less_and_replaced_sooner():
    V, policy = fm.solve()
    for (year, age, f), value in V.items():
        if f == HEALTHY and (year, age, FAULTY) in V:
            assert V[(year, age, FAULTY)] >= value - 1e-9, f"Being faulty can never be cheaper than being healthy (year {year}, age {age})."
    assert policy[(3, 2, HEALTHY)] == KEEP and policy[(3, 2, FAULTY)] == REPLACE, (
        "In year 3 a healthy 2-year-old machine should be kept and a faulty one replaced: the policy has to depend on the condition."
    )


def test_value_matches_what_actually_happens():
    V, policy = fm.solve()
    rng = np.random.default_rng(0)
    totals = np.array([fm.simulate(policy, rng) for _ in range(20_000)])
    standard_error = totals.std() / np.sqrt(len(totals))
    assert abs(totals.mean() - V[(1, START_AGE, HEALTHY)]) < 4 * standard_error, (
        f"Living through the six years 20,000 times cost {totals.mean():.3f} on average; your table says "
        f"{V[(1, START_AGE, HEALTHY)]:.3f}. Those should agree to within sampling error ({4 * standard_error:.3f})."
    )
    assert totals.std() > 1.0, "Individual histories should differ from one another: some get a fault and some do not."
