"""Checks for lab p9-cap. Given code: nothing to edit here."""

import copy
import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "labs" / "labkit").exists())))

import toy_pg as pg  # noqa: E402
from labs.labkit import minipg as ref  # noqa: E402

UNIFORM_GAP = 43.45  # a uniformly random legal policy, evaluated exactly


@pytest.fixture(scope="module")
def trained():
    """A reference PPO table after 1,000 races (gap 1.93 s), and one race sampled from it."""
    res = ref.train("ppo", 1000, seed=0)
    race = ref.run_race(res.theta, np.random.default_rng(100))
    return res.theta, race


def least_likely(logits, mask):
    p = pg.masked_probs(logits, mask)
    legal = np.flatnonzero(mask)
    return int(legal[np.argmin(p[legal])]), float(p[legal].min())


# ---------------------------------------------------------------- stage 1: the policy


def test_stage1_probabilities():
    mask = np.array([True, False, True])
    p = pg.masked_probs(np.array([1.0, 50.0, 0.0]), mask)
    assert p[1] == 0.0, "An illegal action must get probability exactly 0, however large its logit."
    assert p.sum() == pytest.approx(1.0)
    assert p[0] == pytest.approx(np.e / (np.e + 1)), "Over the legal actions, the softmax of (1, 0)."
    assert np.all(np.isfinite(pg.masked_probs(np.array([1000.0, 0.0, 999.0]), np.ones(3, bool)))), "Subtract the largest legal logit first."


def test_stage1_log_gradient_matches_finite_differences():
    rng = np.random.default_rng(0)
    mask = np.array([True, False, True])
    for _ in range(10):
        z = rng.normal(0, 2, 3)
        for a in (0, 2):
            g = pg.log_grad(z, mask, a)
            assert g[1] == 0.0, "No gradient flows into an illegal action's logit."
            for j in (0, 2):
                e = np.zeros(3)
                e[j] = 1e-6
                num = (np.log(pg.masked_probs(z + e, mask)[a]) - np.log(pg.masked_probs(z - e, mask)[a])) / 2e-6
                assert g[j] == pytest.approx(num, abs=1e-6), "Your log-gradient disagrees with finite differences."


# ---------------------------------------------------------------- stage 2: REINFORCE


def test_stage2_reinforce_matches_the_reference():
    theta = pg.train_reinforce(300, seed=0)
    mine, theirs = pg.gap(theta), ref.gap(ref.train("reinforce", 300, seed=0).theta)
    assert mine == pytest.approx(theirs, abs=1e-6), f"300 races of your REINFORCE end {mine:.2f} s from the optimum; the reference, same seed, {theirs:.2f} s."


def test_stage2_reinforce_learns_and_a_sign_error_is_loud():
    good = pg.gap(pg.train_reinforce(2000, seed=0))
    flipped = pg.gap(pg.train_reinforce(2000, seed=0, sign=-1.0))
    assert good < UNIFORM_GAP - 20, f"After 2,000 races REINFORCE should be well clear of a random policy ({UNIFORM_GAP} s away); it is {good:.2f} s away."
    assert flipped > good + 10, f"With the sign flipped it should be clearly worse: {flipped:.2f} s against {good:.2f} s."


# ---------------------------------------------------------------- stage 3: GAE and the critic


def test_stage3_gae_page_03_numbers():
    rewards, values = [-3.0, -2.0, -3.0, -2.0], [-10.0, -6.0, -5.0, -1.0]
    assert pg.gae(rewards, values, 0.0)[0] == pytest.approx(1.0)
    assert pg.gae(rewards, values, 0.95)[0] == pytest.approx(0.095125)
    assert pg.gae(rewards, values, 1.0) == pytest.approx(np.cumsum(rewards[::-1])[::-1] - values), "At λ = 1 the advantages are G_t − V(s_t)."


def test_stage3_gae_matches_the_reference():
    rng = np.random.default_rng(4)
    r, v = rng.normal(size=20), rng.normal(size=20)
    assert pg.gae(r, v, 0.9) == pytest.approx(ref.gae(r, v, 0.9))


def test_stage3_critic_update():
    V = {}
    pg.critic_update(V, "s", 10.0, 0.1)
    assert V["s"] == pytest.approx(1.0), "From 0, a tenth of the way towards 10."
    pg.critic_update(V, "s", 10.0, 0.5)
    assert V["s"] == pytest.approx(5.5)


# ---------------------------------------------------------------- stage 4: the destructive update


def test_stage4_one_big_step_wrecks_a_good_policy(trained):
    theta, race = trained
    before = pg.gap(theta)
    wrecked = copy.deepcopy(theta)
    for key, mask in zip(race.keys, race.masks):
        a, _ = least_likely(wrecked[key], mask)
        wrecked[key] = pg.destructive_step(wrecked[key], mask, a, advantage=8.0, step=2.0)
    after = pg.gap(wrecked)
    print(f"one unclipped step on one race's laps: gap {before:.2f} -> {after:.2f} s")
    assert after > before + 10, f"One big step towards one race's least likely actions should cost more than 10 s (measured 1.9 -> 21); got {before:.2f} -> {after:.2f}."


# ---------------------------------------------------------------- stage 5: the clip


def test_stage5_gradient_is_zero_where_the_clip_binds():
    mask = np.ones(3, bool)
    z = np.array([0.0, 0.0, 0.0])  # pi(0) = 1/3
    third = 1 / 3
    assert np.array_equal(pg.clipped_step(z, mask, 0, +1.0, third / 1.3, 0.2, 0.1), z), "A > 0 and ratio 1.3 ≥ 1.2: the clip binds, nothing moves."
    assert np.array_equal(pg.clipped_step(z, mask, 0, -1.0, third / 0.7, 0.2, 0.1), z), "A < 0 and ratio 0.7 ≤ 0.8: the clip binds, nothing moves."
    assert not np.array_equal(pg.clipped_step(z, mask, 0, -1.0, third / 1.3, 0.2, 0.1), z), (
        "A < 0 with ratio 1.3: the unclipped term is the smaller one, so the step must still be taken (page 04's second table)."
    )
    moved = pg.clipped_step(z, mask, 0, +1.0, third, 0.2, 0.1)
    assert moved == pytest.approx(z + 0.1 * 1.0 * pg.log_grad(z, mask, 0)), "Ratio 1: the step is step × ratio × A × log-gradient."
    assert not np.array_equal(pg.clipped_step(z, mask, 0, +1.0, third / 1.3, 0.2, 0.1, clip=False), z), "With clip=False it never stops."


def test_stage5_clipped_steps_leave_the_policy_alone_but_can_overshoot(trained):
    theta, race = trained
    before = pg.gap(theta)
    safe = copy.deepcopy(theta)
    largest = 0.0
    for key, mask in zip(race.keys, race.masks):
        a, p_old = least_likely(safe[key], mask)
        for _ in range(20):
            safe[key] = pg.clipped_step(safe[key], mask, a, 8.0, p_old, 0.2, 0.1)
        largest = max(largest, pg.masked_probs(safe[key], mask)[a] / p_old)
    after = pg.gap(safe)
    print(f"twenty clipped steps: gap {before:.2f} -> {after:.2f} s; largest ratio reached {largest:.2f} (the clip is at 1.2)")
    assert after < before + 0.5, f"Twenty clipped steps on the same scenario should leave the gap where it was; got {before:.2f} -> {after:.2f}."
    assert largest > 1.2, "The clip stops the pushing, not the first step: some ratio should end past 1.2 (measured 4.95). This is the overshoot page 04 now describes."


# ---------------------------------------------------------------- stage 6: a small PPO


def test_stage6_ppo_matches_the_reference():
    mine, theirs = pg.gap(pg.train_ppo(200, seed=0)), ref.gap(ref.train("ppo", 200, seed=0).theta)
    assert mine == pytest.approx(theirs, abs=1e-6), f"200 races of your PPO end {mine:.2f} s away; the reference, same seed, {theirs:.2f} s. Check the order of the steps in ppo_update."


def test_stage6_ppo_gets_close():
    seed = 0
    g = pg.gap(pg.train_ppo(2000, seed=seed))
    assert g < 3.0, f"After 2,000 races, seed {seed}, your PPO should be within 3 s of the optimum (measured 1.9); it is {g:.2f} s away."


# ---------------------------------------------------------------- stage 7: ten epochs per batch


def test_stage7_at_ten_epochs_the_clip_earns_its_keep():
    clipped = [pg.gap(pg.train_ppo(1000, seed=0, epochs=10))]
    unclipped = [pg.gap(pg.train_ppo(1000, seed=0, epochs=10, clip=False))]
    print(f"10 epochs, 1,000 races: with the clip {np.round(clipped, 2)}, without {np.round(unclipped, 2)}")
    assert max(clipped) < 3.0, f"With the clip, ten epochs per batch should still end within 3 s (measured 1.7); got {np.round(clipped, 2)}."
    assert np.mean(unclipped) > np.mean(clipped) + 2.0, f"Without the clip, reusing each batch ten times should cost (measured 7.2 s, against 1.7 with the clip); got {np.round(unclipped, 2)}."
