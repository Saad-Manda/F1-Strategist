"""Checks for lab p9-03. Given code: nothing to edit here."""

import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gae as g  # noqa: E402

# Page 03's trajectory: four steps, gamma = 1, terminal at the end.
R = [-3.0, -2.0, -3.0, -2.0]
V = [-10.0, -6.0, -5.0, -1.0]
END = [False, False, False, True]
TERM = [False, False, False, True]
NO_FINAL = [0.0] * 4


def page_advantages(lam):
    nv = g.next_values(V, END, TERM, NO_FINAL, last_value=99.0)
    return g.gae(R, V, nv, END, 1.0, lam)[0]


def test_next_values_inside_one_episode():
    nv = g.next_values(V, END, TERM, NO_FINAL, last_value=99.0)
    assert nv[:3] == pytest.approx([-6.0, -5.0, -1.0]), "Inside an episode the next value is the next step's V."
    assert nv[3] == 0.0, "After a terminal step the next value is 0: nothing follows a real ending. (last_value is only for a buffer that stops mid-episode.)"


def test_residuals_match_page_03():
    nv = g.next_values(V, END, TERM, NO_FINAL, last_value=0.0)
    assert g.td_residuals(R, V, nv, 1.0) == pytest.approx([1.0, -1.0, 1.0, -1.0]), "Page 03's δ: 1, −1, 1, −1."


@pytest.mark.parametrize("lam, a0", [(0.0, 1.0), (0.5, 0.625), (0.95, 0.095125), (1.0, 0.0)])
def test_page_03_advantages(lam, a0):
    assert page_advantages(lam)[0] == pytest.approx(a0, abs=1e-9), f"A₀ at λ = {lam} should be {a0} (page 03 and the warm-up)."


def test_lambda_zero_is_the_td_residual():
    rng = np.random.default_rng(0)
    r, v = rng.normal(size=12), rng.normal(size=12)
    ends = np.zeros(12, bool)
    ends[[4, 11]] = True
    nv = g.next_values(v, ends, ends, np.zeros(12), 0.0)
    adv, _ = g.gae(r, v, nv, ends, 0.9, 0.0)
    assert adv == pytest.approx(g.td_residuals(r, v, nv, 0.9)), "At λ = 0 every advantage is just its own δ."


def test_lambda_one_is_monte_carlo():
    rng = np.random.default_rng(1)
    r, v = rng.normal(size=8), rng.normal(size=8)
    ends = np.zeros(8, bool)
    ends[-1] = True
    nv = g.next_values(v, ends, ends, np.zeros(8), 0.0)
    adv, ret = g.gae(r, v, nv, ends, 1.0, 1.0)
    G = np.cumsum(r[::-1])[::-1]
    assert adv == pytest.approx(G - v), "At λ = 1, γ = 1, on a complete episode, A_t = G_t − V(s_t): the δs telescope."
    assert ret == pytest.approx(G), "…and the returns are the Monte Carlo returns themselves."


def test_truncated_is_not_terminated():
    """The same step, once as a real ending and once cut off by a time limit."""
    r, v = [1.0, 1.0], [5.0, 5.0]
    ends = [False, True]
    as_terminal = g.next_values(v, ends, [False, True], [0.0, 7.0], 0.0)
    as_cutoff = g.next_values(v, ends, [False, False], [0.0, 7.0], 0.0)
    assert as_terminal[1] == 0.0, "Terminated: the next value is 0."
    assert as_cutoff[1] == 7.0, (
        "Truncated: the episode would have gone on, so bootstrap from the critic's value of the observation it was cut off at. "
        "Using 0 here tells the critic every time-limited episode ends in disaster: page 05's quiet off-by-one."
    )


def test_nothing_leaks_across_an_episode_boundary():
    r = [1.0, 1.0, 1.0, 100.0, 100.0]
    v = [0.0] * 5
    ends = [False, False, True, False, False]
    nv = g.next_values(v, ends, ends, [0.0] * 5, last_value=0.0)
    adv, _ = g.gae(r, v, nv, ends, 1.0, 1.0)
    assert adv[:3] == pytest.approx([3.0, 2.0, 1.0]), "The first episode's advantages must not include the next episode's rewards of 100."
    assert adv[3:] == pytest.approx([200.0, 100.0])


def test_buffer_that_stops_mid_episode_uses_last_value():
    nv = g.next_values([0.0, 0.0], [False, False], [False, False], [0.0, 0.0], last_value=4.0)
    assert nv[1] == 4.0, "When the buffer stops mid-episode, the last step bootstraps from last_value."


def test_agrees_with_stable_baselines3():
    """The same buffer through SB3's own RolloutBuffer, which is what MaskablePPO.learn() runs."""
    torch = pytest.importorskip("torch")
    from gymnasium import spaces
    from stable_baselines3.common.buffers import RolloutBuffer

    n, gamma, lam = 30, 0.99, 0.95
    rng = np.random.default_rng(2)
    r, v = rng.normal(size=n), rng.normal(size=n)
    ends = np.zeros(n, bool)
    ends[[6, 17, 18]] = True  # three terminations; the buffer then stops mid-episode
    last_value = 0.37
    buf = RolloutBuffer(n, spaces.Box(-1, 1, (1,)), spaces.Discrete(2), device="cpu", gae_lambda=lam, gamma=gamma)
    start = True
    for t in range(n):
        buf.add(np.zeros((1, 1)), np.zeros((1, 1)), np.array([r[t]]), np.array([start]), torch.tensor([v[t]]), torch.tensor([0.0]))
        start = bool(ends[t])
    buf.compute_returns_and_advantage(torch.tensor([last_value]), np.array([False]))

    nv = g.next_values(v, ends, ends, np.zeros(n), last_value)
    adv, ret = g.gae(r, v, nv, ends, gamma, lam)
    assert adv == pytest.approx(buf.advantages.flatten(), abs=1e-5), "Your advantages differ from SB3's on the same buffer."
    assert ret == pytest.approx(buf.returns.flatten(), abs=1e-5), "Returns are advantages plus values, as in SB3."
