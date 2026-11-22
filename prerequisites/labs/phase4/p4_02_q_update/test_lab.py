"""Checks for lab p4-02. Given code: nothing to edit here."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import q_update as qu  # noqa: E402
from q_update import A0, A1, S1, S2, S3  # noqa: E402

BOTH = [A0, A1]


def table(values):
    return np.array(values, dtype=float)


def test_target_adds_the_best_next_value():
    Q = table([[0, 0], [-4, -2], [0, 0]])
    assert qu.td_target(Q, -1.0, S2, False, BOTH) == pytest.approx(-3.0), "r + max(Q[s2, a0], Q[s2, a1]) = -1 + max(-4, -2) = -3."


def test_target_at_the_end_is_the_reward_alone():
    Q = table([[0, 0], [0, 0], [50, 70]])
    assert qu.td_target(Q, -3.0, S3, True, BOTH) == pytest.approx(-3.0), (
        "When the transition ends the episode, nothing follows. The target is the reward, even if the table holds numbers for that state."
    )


def test_target_ignores_illegal_actions():
    Q = table([[0, 0], [-6, 99], [0, 0]])
    got = qu.td_target(Q, -1.0, S2, False, [A0])
    assert got == pytest.approx(-7.0), (
        f"Only a0 is legal in the next state, so the target is -1 + Q[s2, a0] = -7. Got {got}: an illegal action's value (99) was used."
    )


def test_target_uses_gamma():
    Q = table([[0, 0], [-4, -2], [0, 0]])
    assert qu.td_target(Q, -1.0, S2, False, BOTH, gamma=0.5) == pytest.approx(-2.0), "gamma multiplies the next value and only that: -1 + 0.5 * (-2)."


def test_update_moves_one_cell_part_of_the_way():
    Q = table([[2.0, 7.0], [-4.0, -2.0], [0.0, 0.0]])
    before = Q.copy()
    delta = qu.q_update(Q, S1, A0, -1.0, S2, False, BOTH, alpha=0.25)
    assert delta == pytest.approx(-5.0), "delta = target - Q[s, a] = (-1 + -2) - 2 = -5."
    assert Q[S1, A0] == pytest.approx(0.75), "The cell moves by alpha * delta: 2 + 0.25 * (-5) = 0.75."
    before[S1, A0] = Q[S1, A0]
    assert np.array_equal(Q, before), "Exactly one cell should change."


def test_alpha_one_jumps_all_the_way():
    Q = table([[2.0, 7.0], [-4.0, -2.0], [0.0, 0.0]])
    qu.q_update(Q, S1, A0, -1.0, S2, False, BOTH, alpha=1.0)
    assert Q[S1, A0] == pytest.approx(-3.0), "With alpha = 1 the cell is replaced by the target."


def test_reproduces_page_02_cell_by_cell():
    Q = np.zeros((3, 2))
    deltas = [qu.q_update(Q, s, a, r, s2, done, BOTH, alpha=0.5) for s, a, r, s2, done in qu.PAGE_TRANSITIONS]
    assert deltas == pytest.approx([-1.0, -1.0, -3.0, -0.5]), f"The four TD errors on page 02 are -1, -1, -3, -0.5. Got {deltas}."
    want = table([[-0.75, -1.5], [-0.5, 0.0], [0.0, 0.0]])
    assert np.allclose(Q, want), f"After page 02's four transitions the table should be\n{want}\nGot\n{Q}"


def test_enough_updates_reach_the_true_values():
    Q = qu.train_on_toy(4000, alpha=0.1, rng=np.random.default_rng(0))
    want = table([[-2.0, -3.0], [-1.0, -2.0]])
    assert np.allclose(Q[:2], want, atol=0.05), (
        f"Backward induction gives Q* = {want.tolist()} for s1 and s2. After 4,000 updates your table has {np.round(Q[:2], 3).tolist()}."
    )
    assert np.all(Q[S3] == 0.0), "No transition starts in the terminal state, so its row should never be written."
