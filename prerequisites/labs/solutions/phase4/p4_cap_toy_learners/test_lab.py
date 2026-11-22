"""Checks for the Phase 4 capstone, one group per stage. Given code: nothing to edit here."""

import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "labs" / "labkit").exists())))

import toy_learners as tl  # noqa: E402
from labs.labkit import toyrace as tr  # noqa: E402
from labs.labkit.toyrace import A, B, PIT_A, PIT_B, STAY_OUT  # noqa: E402

QUIET = tr.RaceModel(sc_hazard=0.0)  # no safety car: every race is the same race
S = (5, A, 5, 0, False)
S2 = (6, A, 6, 0, False)


# ---------------------------------------------------------------- stage 1: choosing


def test_stage1_greedy_choice_respects_the_mask():
    rng = np.random.default_rng(0)
    values = np.array([-5.0, 9.0, -2.0])
    picks = {tl.explore_or_exploit(values, [0, 2], 0.0, rng) for _ in range(100)}
    assert picks == {2}, f"With epsilon = 0 and only actions 0 and 2 legal, the choice is always action 2 (value -2). Got {picks}. Action 1 is the highest but is not legal."


def test_stage1_ties_go_to_the_lowest_action():
    rng = np.random.default_rng(0)
    assert tl.explore_or_exploit(np.zeros(3), [0, 1, 2], 0.0, rng) == 0, "When legal actions are equally good, return the lowest-numbered one."
    assert tl.explore_or_exploit(np.zeros(3), [1, 2], 0.0, rng) == 1


def test_stage1_exploration_is_uniform_over_legal_actions():
    rng = np.random.default_rng(0)
    values = np.array([0.0, 100.0, -100.0])
    picks = [tl.explore_or_exploit(values, [0, 2], 1.0, rng) for _ in range(2000)]
    assert 1 not in picks, "Exploration must stay inside the legal actions."
    assert abs(picks.count(0) / 2000 - 0.5) < 0.05, "With epsilon = 1 each legal action should be chosen about equally often, whatever its value."


def test_stage1_decay():
    assert tl.decayed_epsilon(0, 1.0, 0.05, 1000) == pytest.approx(1.0)
    assert tl.decayed_epsilon(500, 1.0, 0.05, 1000) == pytest.approx(0.525), "Halfway through the decay, epsilon is halfway between start and end."
    assert tl.decayed_epsilon(5000, 1.0, 0.05, 1000) == pytest.approx(0.05), "After decay_steps, epsilon stays at its floor."


def test_stage1_act_and_greedy_flag():
    learner = tl.TableLearner(seed=0)
    learner.table[S][:] = [-3.0, -1.0, -2.0]
    assert learner.epsilon == 1.0
    picks = {learner.act(S, [0, 1, 2], greedy=True) for _ in range(200)}
    assert picks == {1}, f"With greedy=True the choice must never be random, even while epsilon is 1. Got {picks}."
    picks = {learner.act(S, [0, 1, 2]) for _ in range(200)}
    assert picks == {0, 1, 2}, "Without greedy, a learner at epsilon = 1 should be exploring."


# ---------------------------------------------------------------- stage 2: off-policy


def test_stage2_update_uses_the_best_legal_next_value():
    learner = tl.OffPolicyLearner(alpha=0.5)
    learner.table[S][STAY_OUT] = -10.0
    learner.table[S2][:] = [-6.0, 50.0, -4.0]
    learner.learn(S, STAY_OUT, -1.0, S2, False, [STAY_OUT, PIT_B])
    assert learner.table[S][STAY_OUT] == pytest.approx(-7.5), (
        "Legal next actions are 0 and 2, worth -6 and -4. Target = -1 + (-4) = -5; the cell moves from -10 to -7.5. "
        f"Got {learner.table[S][STAY_OUT]:.2f}. (A value near 19.5 means the illegal action's 50 was used.)"
    )


def test_stage2_terminal_update():
    learner = tl.OffPolicyLearner(alpha=0.5)
    learner.table[S2][:] = [40.0, 50.0, 60.0]
    learner.learn(S, PIT_B, -3.0, S2, True, [STAY_OUT])
    assert learner.table[S][PIT_B] == pytest.approx(-1.5), "On the last lap the target is the reward alone: 0 + 0.5 * (-3 - 0) = -1.5."


def test_stage2_counts_steps_and_decays():
    learner = tl.OffPolicyLearner(decay_steps=10)
    for _ in range(5):
        learner.learn(S, STAY_OUT, -1.0, S2, False, [STAY_OUT])
    assert learner.steps == 5, "learn() should finish with self.count_step()."
    assert learner.epsilon == pytest.approx(0.525)


# ---------------------------------------------------------------- stage 3: on-policy


def test_stage3_target_uses_the_action_chosen_next():
    learner = tl.OnPolicyLearner(alpha=0.5, eps_start=1.0)
    learner.table[S][STAY_OUT] = -10.0
    learner.table[S2][:] = [-6.0, 0.0, -40.0]
    seen = set()
    for _ in range(60):
        learner.table[S][STAY_OUT] = -10.0
        learner.learn(S, STAY_OUT, -1.0, S2, False, [STAY_OUT, PIT_B])
        chosen = learner.pending
        assert chosen in (STAY_OUT, PIT_B), "learn() should store the action it chose for the next state in self.pending."
        want = -10.0 + 0.5 * (-1.0 + learner.table[S2][chosen] + 10.0)
        assert learner.table[S][STAY_OUT] == pytest.approx(want), "The target should use the value of the action stored in self.pending, not the best one."
        seen.add(chosen)
    assert seen == {STAY_OUT, PIT_B}, "At epsilon = 1 the pre-chosen action should vary: it comes from the same ε-greedy policy."


def test_stage3_pending_action_is_handed_out_once():
    learner = tl.OnPolicyLearner(eps_start=0.0, eps_end=0.0)
    learner.table[S2][:] = [-6.0, -9.0, -4.0]
    learner.learn(S, STAY_OUT, -1.0, S2, False, [STAY_OUT, PIT_B])
    assert learner.pending == PIT_B
    learner.table[S2][:] = [0.0, -9.0, -4.0]  # the table now prefers STAY_OUT, but the commitment stands
    assert learner.act(S2, [STAY_OUT, PIT_B]) == PIT_B, "act() should return the action learn() committed to."
    assert learner.pending is None, "Once handed out, the pending action is cleared."
    assert learner.act(S2, [STAY_OUT, PIT_B]) == STAY_OUT, "With nothing pending, act() chooses fresh from the table."


def test_stage3_terminal_update_commits_to_nothing():
    learner = tl.OnPolicyLearner(alpha=0.5)
    learner.learn(S, PIT_B, -3.0, S2, True, [STAY_OUT])
    assert learner.table[S][PIT_B] == pytest.approx(-1.5)
    assert learner.pending is None, "After the last lap there is no next action to choose."


def test_stage3_greedy_ignores_a_pending_action():
    learner = tl.OnPolicyLearner(eps_start=1.0)
    learner.table[S2][:] = [-6.0, -9.0, -4.0]
    learner.pending = STAY_OUT
    assert learner.act(S2, [STAY_OUT, PIT_B], greedy=True) == PIT_B, "An evaluation call (greedy=True) should read the table, not a leftover commitment."


# ---------------------------------------------------------------- stage 4: the leak


def test_stage4_reset_forgets_the_commitment():
    learner = tl.OnPolicyLearner(eps_start=0.0, eps_end=0.0)
    learner.table[S2][:] = [-6.0, -9.0, -4.0]
    learner.learn(S, STAY_OUT, -1.0, S2, False, [STAY_OUT, PIT_B])  # the race is stopped right after this lap
    learner.reset()
    start = (1, A, 1, 0, False)
    learner.table[start][:] = [-1.0, -5.0, -5.0]
    assert learner.act(start, [STAY_OUT, PIT_B]) == STAY_OUT, (
        "A race was red-flagged with an action still pending. After reset(), the next race's first move must come from the table for ITS state. "
        "Yours returned the leftover action."
    )


# ---------------------------------------------------------------- stage 5: one race


class Scripted(tl.TableLearner):
    """Stays out every lap except one, and records what it is told."""

    def __init__(self, pit_lap):
        super().__init__()
        self.pit_lap, self.resets, self.seen = pit_lap, 0, []

    def reset(self):
        self.resets += 1

    def act(self, state, legal, greedy=False):
        return PIT_B if state[0] == self.pit_lap else STAY_OUT

    def learn(self, *transition):
        self.seen.append(transition)


def test_stage5_race_time_and_actions():
    learner = Scripted(pit_lap=8)
    race = tl.run_race(learner, QUIET, np.random.default_rng(0), train=False)
    assert race["time"] == pytest.approx(224.49), f"A one-stop race pitting for B on lap 8 takes 224.49 s. Got {race['time']:.2f}."
    assert race["actions"] == [STAY_OUT] * 7 + [PIT_B] + [STAY_OUT] * 12
    assert learner.resets == 1, "run_race should call learner.reset() once, before the first lap."
    assert learner.seen == [], "With train=False the learner must not be taught anything."


def test_stage5_transitions_passed_to_learn():
    learner = Scripted(pit_lap=8)
    tl.run_race(learner, QUIET, np.random.default_rng(0), train=True, offset=10.0)
    assert len(learner.seen) == 20, "One call to learn() per lap."
    state, action, reward, next_state, done, legal_next = learner.seen[7]  # lap 8, the pit lap
    assert state == (8, A, 8, 0, False) and action == PIT_B
    assert next_state == (9, B, 1, 0, True), f"After pitting for B on lap 8, lap 9 starts on a new B with both compounds used. Got {next_state}."
    assert reward == pytest.approx(-(QUIET.cost(8, A, 8, PIT_B) - 10.0)), "The reward is minus (lap time minus offset)."
    assert not done and sorted(legal_next) == [STAY_OUT, PIT_A]
    assert learner.seen[-1][4] is True or learner.seen[-1][4] == True, "The last lap's transition is the one with done = True."  # noqa: E712
    assert [t[4] for t in learner.seen[:-1]] == [False] * 19


def test_stage5_offset_never_changes_the_reported_time():
    a = tl.run_race(Scripted(8), QUIET, np.random.default_rng(0), train=True, offset=0.0)["time"]
    b = tl.run_race(Scripted(8), QUIET, np.random.default_rng(0), train=True, offset=10.0)["time"]
    assert a == b == pytest.approx(224.49), "Centring changes what the learner is told. The reported race time is always the true one."


def test_stage5_safety_car_follows_the_model():
    model = tr.RaceModel(sc_hazard=1.0, sc_continue=1.0)
    learner = Scripted(pit_lap=99)
    tl.run_race(learner, model, np.random.default_rng(0), train=True)
    assert learner.seen[0][0][3] == 0, "Lap 1 is always under a green flag."
    assert all(t[0][3] == 1 for t in learner.seen[1:]), "With a hazard of 1, every lap after the first is under the safety car: next_sc must come from model.sc_prob."


# ---------------------------------------------------------------- stage 6: does it learn?

EPISODES = 5000


@pytest.fixture(scope="module")
def trained():
    """Three centred and three uncentred off-policy learners, and one on-policy learner."""
    centred, uncentred = [], []
    for seed in range(3):
        learner = tl.OffPolicyLearner(seed=seed)
        tl.train(learner, QUIET, EPISODES, seed=seed, offset=tl.BASE_LAP)
        centred.append(learner)
        learner = tl.OffPolicyLearner(seed=seed)
        tl.train(learner, QUIET, EPISODES, seed=seed, offset=0.0)
        uncentred.append(learner)
    on_policy = tl.OnPolicyLearner(seed=0)
    tl.train(on_policy, QUIET, EPISODES, seed=0, offset=tl.BASE_LAP)
    return centred, uncentred, on_policy


def test_stage6_off_policy_learner_closes_the_gap(trained):
    centred, _, _ = trained
    gaps = [tl.gap_to_optimum(learner, QUIET) for learner in centred]
    assert all(g >= -1e-9 for g in gaps), "No policy can beat the exact optimum."
    assert np.mean(gaps) < 5.0, (
        f"After {EPISODES} races with centred rewards, the off-policy learner should be within a few seconds of the exact optimum "
        f"(224.49 s). Gaps over three seeds: {np.round(gaps, 2)}."
    )


def test_stage6_centring_matters(trained):
    centred, uncentred, _ = trained
    with_centring = np.mean([tl.gap_to_optimum(learner, QUIET) for learner in centred])
    without = np.mean([tl.gap_to_optimum(learner, QUIET) for learner in uncentred])
    assert without > with_centring + 2.0, (
        f"Trained on the raw lap time, the same learner should finish clearly further from the optimum. "
        f"Mean gap with centring {with_centring:.2f} s, without {without:.2f} s."
    )


def test_stage6_on_policy_learner_learns_too(trained):
    _, _, on_policy = trained
    gap = tl.gap_to_optimum(on_policy, QUIET)
    assert 0 <= gap + 1e-9 and gap < 8.0, f"The on-policy learner should end within a few seconds of the optimum; got {gap:.2f} s."
    assert on_policy.pending is None, "Every training race ran to its last lap, so nothing should be left pending."


def test_stage6_evaluating_with_exploration_on_costs_time(trained):
    centred, _, _ = trained
    learner = centred[0]
    assert learner.epsilon == pytest.approx(0.05), "After training, epsilon should be at its floor."
    rng = np.random.default_rng(1)
    greedy = [tl.run_race(learner, QUIET, rng, train=False, greedy=True)["time"] for _ in range(3)]
    assert max(greedy) == min(greedy), "Greedy races in a world with no randomness should all be the same race."
    noisy = np.mean([tl.run_race(learner, QUIET, rng, train=False, greedy=False)["time"] for _ in range(1000)])
    assert noisy > greedy[0] + 0.5, (
        f"With exploration left on at 5%, an 'evaluated' race should average clearly slower than the learner's real policy. "
        f"Greedy {greedy[0]:.2f} s, with exploration {noisy:.2f} s."
    )
