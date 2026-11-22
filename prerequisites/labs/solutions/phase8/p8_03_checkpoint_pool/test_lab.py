"""Checks for lab p8-03. Given code: nothing to edit here."""

import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from pool import RecencyPool  # noqa: E402


def plan_sample(checkpoints, recency_bias=0.7):
    """The real plan's CheckpointPool.sample, quoted (np.random as in the plan)."""
    n = len(checkpoints)
    recent_cutoff = max(1, int(0.8 * n))
    if np.random.random() < recency_bias:
        return np.random.choice(checkpoints[recent_cutoff:])
    return np.random.choice(checkpoints[:recent_cutoff])


def filled(n, **kw):
    p = RecencyPool(**kw)
    for i in range(n):
        p.add(f"ep{i:06d}")
    return p


def test_one_entry_never_raises():
    pool = filled(1)
    rng = np.random.default_rng(0)
    got = {pool.sample(rng) for _ in range(1000)}
    assert got == {"ep000000"}, "With one entry, every sample is that entry."
    assert pool.probabilities() == pytest.approx([1.0])


def test_the_plans_rule_crashes_with_one_entry():
    """Not a test of your code: the plan's own sampler, run on the pool it has for episodes 0-999."""
    np.random.seed(0)
    failures = 0
    for _ in range(1000):
        try:
            plan_sample(["ep000000.pt"])
        except ValueError:
            failures += 1
    print(f"the plan's sample() raised ValueError on {failures} of 1,000 calls with one checkpoint")
    assert 600 < failures < 780


@pytest.mark.parametrize("n,recent", [(2, 1), (3, 1), (4, 1), (5, 1), (6, 2), (7, 2), (12, 3), (50, 10)])
def test_slice_sizes(n, recent):
    r, o = filled(n).slices()
    assert (len(r), len(o)) == (recent, n - recent), f"n = {n}: cut = max(1, int(0.8 n)) = {n - recent}, so {recent} recent."
    assert filled(n).probabilities().sum() == pytest.approx(1.0)


def test_fifty_entries_page_03_numbers():
    p = filled(50).probabilities()
    assert p[-1] == pytest.approx(0.07), "Each of the 10 recent checkpoints: 0.7 / 10."
    assert p[0] == pytest.approx(0.0075), "Each of the 40 older ones: 0.3 / 40."
    assert p[-1] / p[0] == pytest.approx(9.333, abs=1e-3)


def test_empirical_split():
    pool = filled(12)
    rng = np.random.default_rng(1)
    recent = set(pool.slices()[0])
    share = np.mean([pool.sample(rng) in recent for _ in range(20_000)])
    assert share == pytest.approx(0.7, abs=0.01), f"About 70% of samples should come from the recent slice; got {share:.3f}."


def test_eviction():
    pool = filled(51, max_size=50)
    assert len(pool) == 50 and pool.entries[0] == "ep000001", "At 51 entries the oldest goes."


def test_reproducible():
    pool = filled(9)

    def draws(seed):
        rng = np.random.default_rng(seed)
        return [pool.sample(rng) for _ in range(50)]

    np.random.seed(123)
    a = draws(7)
    np.random.seed(456)
    assert a == draws(7), "The same seed must give the same samples: use only the rng you are given."


def test_loader_called_once_per_name():
    calls = []
    pool = filled(5, loader=lambda name: calls.append(name) or f"agent<{name}>")
    rng = np.random.default_rng(2)
    for _ in range(500):
        opp = pool.get(pool.sample(rng))
        assert opp.startswith("agent<")
    assert len(calls) == len(set(calls)) <= 5, f"Each checkpoint should be loaded once, however often it is drawn; the loader ran {len(calls)} times."
