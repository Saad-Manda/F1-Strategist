"""Phase 4 capstone: two table learners on the toy race, measured against the exact optimum.

The brief is page 07 of the Phase 4 set ("Build It Yourself"). There you build an off-policy
and an on-policy learner on a two-state toy. Here you build the same pair for the race of the
earlier capstones, where the Phase 3.5 solver gives the exact answer to measure them against.

    python -m labs check p4-cap 1      check one stage
    python -m labs check p4-cap        check everything
    python -m labs hint  p4-cap        if you are stuck

THE RACE
--------
`model` is a labs.labkit.toyrace.RaceModel: 20 laps, compounds A = 0 and B = 1, actions
STAY_OUT = 0, PIT_A = 1, PIT_B = 2. The learners never read the model's formulas. They only
see transitions, one lap at a time, produced by run_race() (stage 5).

A STATE is the tuple (lap, compound, age, sc, used_both). It is already a small set of whole
numbers, so it can be a table key as it stands, with no binning.

A learner's table maps a state to an array of three numbers, one per action:
    self.table[state][action]
It is a defaultdict, so a state that has never been seen reads as [0.0, 0.0, 0.0].

`legal` is always a list of the legal action numbers, for example [0, 2].

Names here are deliberately not the real project's names.
"""

from collections import defaultdict

import numpy as np

from labs.labkit.toyrace import A, DRY, STAY_OUT  # noqa: F401

N_ACTIONS = 3
BASE_LAP = 10.0  # a typical lap time; subtracting it from every lap is "reward centring"

# ============================================================================ Stage 1


def explore_or_exploit(values, legal, epsilon, rng):
    """One ε-greedy choice. `values` is an array of N_ACTIONS numbers. Returns an int.

    Draw rng.random(). Below epsilon: return a legal action chosen uniformly with rng.choice.
    Otherwise: return the legal action with the highest value. If several are equally good,
    return the one with the lowest number. Never return an action that is not in `legal`.
    """
    # TODO: explore with rng.choice(legal) when rng.random() < epsilon; otherwise the best legal action, lowest number on ties
    raise NotImplementedError("TODO p4-cap: explore with rng.choice(legal) when rng.random() < epsilon; otherwise the best legal action, lowest number on ties")


def decayed_epsilon(step, start, end, decay_steps):
    """Linear decay from `start` to `end` over `decay_steps` steps, then flat at `end`."""
    # TODO: start - step * (start - end) / decay_steps, never below end
    raise NotImplementedError("TODO p4-cap: start - step * (start - end) / decay_steps, never below end")


class TableLearner:
    """What the two learners share. Given, except for act()."""

    def __init__(self, alpha=0.1, eps_start=1.0, eps_end=0.05, decay_steps=60_000, seed=0):
        self.alpha = alpha
        self.eps_start, self.eps_end, self.decay_steps = eps_start, eps_end, decay_steps
        self.epsilon = eps_start
        self.steps = 0
        self.rng = np.random.default_rng(seed)
        self.table = defaultdict(lambda: np.zeros(N_ACTIONS))

    def reset(self):
        """Called at the start of every race. Nothing to forget here; see stage 4."""

    def count_step(self):
        """Call once at the end of every learn(): advances the step counter and decays epsilon."""
        self.steps += 1
        self.epsilon = decayed_epsilon(self.steps, self.eps_start, self.eps_end, self.decay_steps)

    def act(self, state, legal, greedy=False):
        """Choose an action for `state`.

        Normally: explore_or_exploit on self.table[state] with self.epsilon and self.rng.
        With greedy=True: the same call with an epsilon of 0, so the choice is never random.
        """
        # TODO: explore_or_exploit(self.table[state], legal, 0.0 if greedy else self.epsilon, self.rng)
        raise NotImplementedError("TODO p4-cap: explore_or_exploit(self.table[state], legal, 0.0 if greedy else self.epsilon, self.rng)")


# ============================================================================ Stage 2


class OffPolicyLearner(TableLearner):
    def learn(self, state, action, reward, next_state, done, legal_next):
        """Page 02's update.

        target = reward                                             if done
        target = reward + the largest self.table[next_state][a] over a in legal_next   otherwise
        Move self.table[state][action] by self.alpha times (target - its current value).
        Finish with self.count_step().
        """
        # TODO: build the target with a max over legal_next (or the reward alone when done), nudge the cell by alpha * (target - cell), then self.count_step()
        raise NotImplementedError("TODO p4-cap: build the target with a max over legal_next (or the reward alone when done), nudge the cell by alpha * (target - cell), then self.count_step()")


# ============================================================================ Stage 3


class OnPolicyLearner(TableLearner):
    """Page 04's update. Its target needs the action that will really be taken next.

    The training loop asks for that action only after learn() has returned. So learn() chooses
    it early, keeps it in self.pending, and act() hands it out the next time it is called.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending = None

    def act(self, state, legal, greedy=False):
        """If greedy: ignore self.pending and return super().act(state, legal, greedy=True).
        Otherwise, if an action is pending: return it and set self.pending back to None.
        Otherwise: return super().act(state, legal).
        """
        # TODO: greedy goes straight to the parent; a pending action is handed out once and cleared; otherwise choose fresh
        raise NotImplementedError("TODO p4-cap: greedy goes straight to the parent; a pending action is handed out once and cleared; otherwise choose fresh")

    def learn(self, state, action, reward, next_state, done, legal_next):
        """target = reward                                          if done
        Otherwise: choose the next action now with super().act(next_state, legal_next),
        store it in self.pending, and use
            target = reward + self.table[next_state][that action]
        Then nudge the cell and call self.count_step(), as in stage 2.
        """
        # TODO: when not done, pick and store the pending action and use its value in the target; nudge the cell; self.count_step()
        raise NotImplementedError("TODO p4-cap: when not done, pick and store the pending action and use its value in the target; nudge the cell; self.count_step()")

    # ======================================================================== Stage 4

    def reset(self):
        """Forget any pending action.

        A race can stop before its last lap (a red flag, a crash in the code, an early exit
        from a loop). learn() will then have chosen an action for a lap that never comes. If
        it is still pending when the next race starts, that race's first move is one chosen
        for a different situation.
        """
        # TODO: set self.pending to None
        raise NotImplementedError("TODO p4-cap: set self.pending to None")


# ============================================================================ Stage 5


def run_race(learner, model, rng, train=True, greedy=False, offset=0.0):
    """Drive one race from start to finish. Returns {"time": total race time, "actions": [...]}.

    Start: learner.reset(); lap 1 on compound A at age 1, sc = 0, used_both = False.
    On every lap, in this order:
      1. state = (lap, compound, age, sc, used_both)
         legal = model.legal_actions(lap, compound, DRY, used_both)
         action = learner.act(state, legal, greedy=greedy)
      2. lap_time = model.cost(lap, compound, age, action, DRY, sc); add it to the total
      3. what the next lap looks like:
           next_compound, next_age = model.next_tyre(compound, age, action)
           next_used = used_both or (next_compound != compound)
           next_sc = int(rng.random() < model.sc_prob(sc))
      4. if train:
           reward = -(lap_time - offset)
           done = (lap == model.horizon)
           next_state = (lap + 1, next_compound, next_age, next_sc, next_used)
           legal_next = model.legal_actions(lap + 1, next_compound, DRY, next_used)
           learner.learn(state, action, reward, next_state, done, legal_next)
      5. move on to the next lap.

    The returned "time" is always the true race time. `offset` changes only what the learner
    is told, never what is reported.
    """
    # TODO: reset the learner, then loop over laps doing steps 1-5, summing lap times and collecting actions
    raise NotImplementedError("TODO p4-cap: reset the learner, then loop over laps doing steps 1-5, summing lap times and collecting actions")


# ============================================================================ Given: training and measuring (stage 6 uses these)


def train(learner, model, episodes, seed=0, offset=BASE_LAP):
    """Run `episodes` training races. Returns the list of race times. Given."""
    rng = np.random.default_rng(seed)
    return [run_race(learner, model, rng, train=True, offset=offset)["time"] for _ in range(episodes)]


def greedy_policy(learner, model):
    """The learner's table read as a policy, in the form toyrace.expected_time() expects. Given."""

    def policy(lap, compound, age, sc, used_both, weather):
        legal = model.legal_actions(lap, compound, weather, used_both)
        return learner.act((lap, compound, age, sc, used_both), legal, greedy=True)

    return policy


def gap_to_optimum(learner, model):
    """Exact expected time of the learner's greedy policy, minus the exact optimum. Given.

    Both numbers come from a backward pass over the model, so there is no sampling noise:
    a gap of 0.00 means the learner's policy is optimal.
    """
    from labs.labkit import toyrace

    optimum = toyrace.solve(model)[0][(1, A, 1, 0, False, DRY)]
    return toyrace.expected_time(model, greedy_policy(learner, model)) - optimum
