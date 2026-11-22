"""Checks for lab p8-cap. Given code: nothing to edit here."""

import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "labs" / "labkit").exists())))

import duel_selfplay as ds  # noqa: E402
from labs.labkit import games, pitgame  # noqa: E402

I8 = pitgame.lap_index(8)


@pytest.fixture(scope="module")
def U_on():
    return ds.matrix(True)


@pytest.fixture(scope="module")
def U_off():
    return ds.matrix(False)


def lap_pairs(pairs):
    return [(ds.LAPS[i], ds.LAPS[j]) for i, j in pairs]


# ---------------------------------------------------------------- stage 1: the payoff


def test_stage1_one_race():
    r = pitgame.race(8, 8, 0, True)
    want = (1.0 if r["finished_ahead"] else -1.0) + 0.05 * (r["rival_time"][-1] - r["agent_time"][-1])
    assert ds.payoff(8, 8, 0, True) == pytest.approx(want), "Win or lose (+1 / -1) plus 0.05 times (leader's final time - follower's)."
    assert -1.2 < ds.payoff(8, 8, 0, True) < -1.0, "Stopping on the same lap as the leader, the follower stays behind (-1) and loses a little margin too: a payoff a little below -1."


@pytest.mark.parametrize("interaction", [True, False])
def test_stage1_the_cache_is_honest(interaction):
    U = ds.matrix(interaction)
    rng = np.random.default_rng(0)
    for _ in range(10):
        i, j = rng.integers(0, ds.N, 2)
        mine = ds.expected_payoff(ds.LAPS[i], ds.LAPS[j], interaction)
        assert mine == pytest.approx(U[i, j], abs=1e-9), (
            f"Your expected_payoff({ds.LAPS[i]}, {ds.LAPS[j]}, {interaction}) is {mine:.4f}; the cached matrix says {U[i, j]:.4f}. "
            "Average payoff over pitgame.SEEDS, all 20 of them.")


# ---------------------------------------------------------------- stage 2: best responses and latest-only


def test_stage2_best_response(U_on):
    rng = np.random.default_rng(1)
    for _ in range(20):
        m = rng.dirichlet(np.ones(ds.N))
        assert ds.best_response(U_on, m, "row") == games.row_best_response(U_on, m), "The follower maximises U @ mix."
        assert ds.best_response(U_on, m, "col") == games.col_best_response(U_on, m), "The leader minimises mix @ U: the payoff is the follower's."


def test_stage2_blocking_off_settles_at_once(U_off):
    seq = lap_pairs(ds.latest_only(U_off, (I8, I8), 10))
    assert len(seq) == 10
    assert seq == [(8, 8)] * 10, f"With blocking off the duel has a pure equilibrium at (8, 8) and latest-only stays there; you got {seq[:4]}..."


def test_stage2_blocking_on_cycles(U_on):
    seq = lap_pairs(ds.latest_only(U_on, (I8, I8), 30))
    assert games.find_period(seq) == 3, f"With blocking on, latest-only should repeat a 3-round cycle; the tail is {seq[-6:]}."
    assert set(seq[-3:]) == {(6, 7), (5, 10), (9, 8)}, f"The cycle should be (6, 7) -> (5, 10) -> (9, 8); got {seq[-3:]}."


# ---------------------------------------------------------------- stage 3: fictitious play


def test_stage3_exploitability_is_zero_only_at_equilibrium(U_off, U_on):
    assert ds.exploitability(U_off, ds.pure(I8), ds.pure(I8)) == pytest.approx(0.0, abs=1e-12), "(8, 8) is the blocking-off equilibrium."
    for i, j in [(I8, I8), (pitgame.lap_index(6), pitgame.lap_index(7))]:
        assert ds.exploitability(U_on, ds.pure(i), ds.pure(j)) == pytest.approx(games.exploitability(U_on, ds.pure(i), ds.pure(j)))


def test_stage3_fictitious_play_converges(U_on):
    f, l, trace = ds.fictitious_play(U_on, 1000, (I8, I8))
    rf, rl, rtrace = games.fictitious_play(U_on, 1000, start=(I8, I8), every=1)
    assert len(trace) == 1000, "One exploitability per round."
    assert np.allclose(f, rf) and np.allclose(l, rl), "Follower first, then the leader against the follower's UPDATED counts."
    assert trace[-1] < 0.01, f"Fictitious play should be within 0.01 of an equilibrium by 1,000 rounds; it is at {trace[-1]:.4f}."
    assert trace[-1] < trace[9] / 10, "…and far closer than after 10 rounds."


def test_stage3_blocking_off_is_pure(U_off):
    f, l, trace = ds.fictitious_play(U_off, 200, (I8, I8))
    assert f[I8] == pytest.approx(1.0) and l[I8] == pytest.approx(1.0), "Blocking off: both always stop on lap 8."


# ---------------------------------------------------------------- stage 4: a pool of best responses


def test_stage4_pool_mix():
    assert ds.pool_mix([3], 0.7)[3] == pytest.approx(1.0), "A one-entry pool is that entry for sure: the n = 1 case the plan crashes on."
    m = ds.pool_mix(list(range(10)), 0.7)
    assert m[8] == pytest.approx(0.35) and m[0] == pytest.approx(0.3 / 8), "n = 10: cut 8; laps 8 and 9 share 0.7, the other eight share 0.3."
    m = ds.pool_mix([2, 2, 5, 2], None)
    assert m[2] == pytest.approx(0.75) and m[5] == pytest.approx(0.25), "Uniform: a lap's probability is its share of the entries."
    assert ds.pool_mix([1, 4, 4, 4, 9], 0.7).sum() == pytest.approx(1.0)


def test_stage4_a_uniform_pool_that_never_forgets_is_fictitious_play(U_on):
    pool = ds.pool_play(U_on, 1000, (I8, I8), None, None)
    _, _, fp = games.fictitious_play(U_on, 1000, start=(I8, I8), every=1)
    assert len(pool) == 1000
    assert np.allclose(pool, [x for _, x in fp], atol=1e-9), (
        "A pool of best responses, sampled uniformly and never trimmed, is the same thing as fictitious play: "
        "the pool's mixture IS the frequency of past play. Check the order (follower appends first).")


def test_stage4_latest_only_is_a_pool_of_one(U_on):
    seq = ds.latest_only(U_on, (I8, I8), 30)
    pool = ds.pool_play(U_on, 30, (I8, I8), None, 1)
    want = [ds.exploitability(U_on, ds.pure(i), ds.pure(j)) for i, j in seq]
    assert np.allclose(pool, want), "max_size 1 keeps only the latest snapshot: pool_play must reproduce latest_only."


# ---------------------------------------------------------------- stage 5: the plan's rule


def test_stage5_the_plans_pool_does_not_converge(U_on):
    plan = np.mean(ds.pool_play(U_on, 1000, (I8, I8), 0.7, 50)[-200:])
    fp = ds.fictitious_play(U_on, 1000, (I8, I8))[2][-1]
    cycle = np.mean([ds.exploitability(U_on, ds.pure(i), ds.pure(j)) for i, j in ds.latest_only(U_on, (I8, I8), 30)[-3:]])
    assert fp < 0.01
    assert plan > 0.2, f"The plan's rule (70% from the newest 20%, at most 50 entries) should NOT settle: mean exploitability over the last 200 rounds measured 0.38; got {plan:.3f}."
    assert plan < cycle, f"…but it should beat latest-only's cycle ({cycle:.2f}); got {plan:.3f}."


# ---------------------------------------------------------------- stage 6: the histogram


def test_stage6_matches_the_definition():
    rng = np.random.default_rng(2)
    f, l = rng.dirichlet(np.ones(ds.N)), rng.dirichlet(np.ones(ds.N))
    mine, ref = ds.delta_distribution(f, l), pitgame.delta_distribution(f, l)
    assert list(mine) == list(ref), "Keys: every delta with probability > 0, sorted."
    assert np.allclose(list(mine.values()), list(ref.values()))


def test_stage6_blocking_off_has_no_shape(U_off):
    f, l, _ = ds.fictitious_play(U_off, 200, (I8, I8))
    assert ds.delta_distribution(f, l) == pytest.approx({0: 1.0}), "Blocking off: both stop on lap 8, every delta is 0."


def test_stage6_blocking_on_is_two_sided(U_on):
    f, l, _ = ds.fictitious_play(U_on, 10_000, (I8, I8))
    d = ds.delta_distribution(f, l)
    p0 = d.get(0, 0.0)
    neg = sum(v for k, v in d.items() if k < 0)
    pos = sum(v for k, v in d.items() if k > 0)
    assert p0 <= 0.15, f"At the blocking-on equilibrium, same-lap stops are rare (measured 0.11); got {p0:.3f}."
    assert neg > 0.5 and pos > 0.2, f"Mass on both sides: undercut (follower first, measured 0.61) and overcut (0.28); got {neg:.2f} and {pos:.2f}."


# ---------------------------------------------------------------- stage 7: your null on your result


def test_stage7_shuffle_p():
    a = np.arange(400) % 9
    assert ds.shuffle_p(a, a.copy(), 200, np.random.default_rng(0)) == pytest.approx(1 / 201), "Identical lists are as far out as it gets: p = 1 / (n + 1)."
    rng = np.random.default_rng(1)
    p = ds.shuffle_p(rng.integers(0, 9, 2000), rng.integers(0, 9, 2000), 200, np.random.default_rng(0))
    assert p > 0.05, "Two independent lists should not be rejected."


def test_stage7_the_null_cannot_see_the_equilibrium(U_on):
    f, l, _ = ds.fictitious_play(U_on, 10_000, (I8, I8))
    fa, la = ds.sample_stops(f, l, 2000, np.random.default_rng(3))
    p = ds.shuffle_p(fa, la, 500, np.random.default_rng(0))
    assert p > 0.05, (
        f"Stops drawn independently from the equilibrium mixtures have no in-race link, so the shuffle should not reject; got p = {p:.3f}. "
        "The histogram's shape is strategic all the same: the test answers a different question.")
