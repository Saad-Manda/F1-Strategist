"""A table Q-learner for the quiet toy race: the p4-cap off-policy learner, as given code.

Used by lab p9-08 to compare an off-policy learner and an on-policy one (labkit.minipg) by the
experience each was given. Same rules as the p4-cap solution: epsilon-greedy over the legal
actions (lowest number on ties), epsilon decayed linearly from 1.0 to 0.05, alpha 0.1, reward
-(lap time - 10).

Labs import this; nothing in this file is a TODO.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from . import toyrace as tr
from .racegym import QUIET, optimum

N_ACTIONS = 3


def train(races: int, seed: int = 0, checkpoint_every: int = 100, alpha: float = 0.1, eps_start: float = 1.0,
          eps_end: float = 0.05, decay_steps: int = 30_000, model: tr.RaceModel = QUIET, offset: float = tr.BASE_LAP):
    """Train for `races` races. Returns (table, [(environment steps so far, exact gap), ...])."""
    rng = np.random.default_rng(seed)
    table = defaultdict(lambda: np.zeros(N_ACTIONS))
    steps, curve = 0, []
    best = optimum(model)
    for race in range(1, races + 1):
        compound, age, used = tr.A, 1, False
        for lap in range(1, model.horizon + 1):
            state = (lap, compound, age, used)
            legal = model.legal_actions(lap, compound, tr.DRY, used)
            eps = max(eps_end, eps_start - steps * (eps_start - eps_end) / decay_steps)
            if rng.random() < eps:
                action = int(rng.choice(legal))
            else:
                action = int(max(legal, key=lambda a: (table[state][a], -a)))
            lap_time = model.cost(lap, compound, age, action, tr.DRY, 0)
            new_compound, new_age = model.next_tyre(compound, age, action)
            new_used = used or new_compound != compound
            if lap == model.horizon:
                target = -(lap_time - offset)
            else:
                nxt = (lap + 1, new_compound, new_age, new_used)
                target = -(lap_time - offset) + max(table[nxt][a] for a in model.legal_actions(lap + 1, new_compound, tr.DRY, new_used))
            table[state][action] += alpha * (target - table[state][action])
            compound, age, used = new_compound, new_age, new_used
            steps += 1
        if race % checkpoint_every == 0:
            curve.append((steps, gap(table, model, best)))
    return table, curve


def greedy_policy(table, model: tr.RaceModel = QUIET):
    def policy(lap, compound, age, sc, used_both, weather):
        legal = model.legal_actions(lap, compound, tr.DRY, used_both)
        values = table.get((lap, compound, age, used_both), np.zeros(N_ACTIONS))
        return int(max(legal, key=lambda a: (values[a], -a)))

    return policy


def gap(table, model: tr.RaceModel = QUIET, best: float | None = None) -> float:
    best = optimum(model) if best is None else best
    return tr.expected_time(model, greedy_policy(table, model)) - best
