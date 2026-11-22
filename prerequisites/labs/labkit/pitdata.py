"""Synthetic pit-stop data for lab p8-07. Given code.

Each generator returns (agent_laps, rival_laps, sc_laps): one entry per race of a 52-lap race,
the lap each car stopped on, and the lap a safety car came out (-1 for none).

* independent       each car stops in its own window, laps 16-24, uniformly. Nothing links them.
* shared_safety_car as independent, but half the races have a safety car (laps 10-39). A car whose
                    window is within 6 laps of it stops under it instead. Both cars react to the
                    safety car; neither reacts to the other.
* reactive          as shared_safety_car, but in races with no safety car the agent stops 1 or 2
                    laps before or after the rival, half each: an undercut or an overcut.
"""

from __future__ import annotations

import numpy as np

WINDOW = (16, 25)  # numpy integers: 16 to 24
SC_RANGE = (10, 40)
SC_REACH = 6


def _race(rng, safety_car: bool, react: bool):
    sc = int(rng.integers(*SC_RANGE)) if safety_car and rng.random() < 0.5 else -1
    a, b = int(rng.integers(*WINDOW)), int(rng.integers(*WINDOW))
    if sc >= 0:
        if abs(sc - a) <= SC_REACH:
            a = sc
        if abs(sc - b) <= SC_REACH:
            b = sc
    elif react:
        step = int(rng.integers(1, 3))
        a = b - step if rng.random() < 0.5 else b + step
    return a, b, sc


def _make(n, seed, safety_car, react):
    rng = np.random.default_rng(seed)
    rows = np.array([_race(rng, safety_car, react) for _ in range(n)])
    return rows[:, 0], rows[:, 1], rows[:, 2]


def independent(n: int = 2000, seed: int = 0):
    return _make(n, seed, safety_car=False, react=False)


def shared_safety_car(n: int = 2000, seed: int = 0):
    return _make(n, seed, safety_car=True, react=False)


def reactive(n: int = 2000, seed: int = 0):
    return _make(n, seed, safety_car=True, react=True)
