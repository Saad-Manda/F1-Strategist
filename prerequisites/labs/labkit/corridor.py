"""The short corridor with switched actions (Sutton & Barto, Example 13.1). Given code.

Four cells in a row; the episode starts in cell 0 and ends on reaching cell 3. Every step costs
-1. In cells 0 and 2, "right" moves right and "left" moves left (cell 0's left is a wall). In
cell 1 the two actions are **switched**: "right" moves left, "left" moves right.

The policy sees nothing that tells the cells apart: one shared feature, so it can only choose a
single probability of pressing "right", the same in every cell. That is what makes the problem
interesting. Any fixed choice of action loops forever. The best policy presses "right" with
probability 0.586 and takes about 11.66 steps on average.

Labs import this; nothing in this file is a TODO.
"""

from __future__ import annotations

import numpy as np

LEFT, RIGHT = 0, 1
GOAL = 3
STEP_CAP = 1000  # an episode that has not finished by then is cut off


def step(cell: int, action: int) -> tuple[int, float, bool]:
    """(next cell, reward, done)."""
    if cell == 1:
        action = 1 - action  # the switched cell
    nxt = max(cell + (1 if action == RIGHT else -1), 0)
    return nxt, -1.0, nxt == GOAL


def p_right(theta: float) -> float:
    """Softmax over the two logits (0 for left, theta for right): the chance of pressing right."""
    return float(1.0 / (1.0 + np.exp(-theta)))


def episode(theta: float, rng: np.random.Generator, cap: int = STEP_CAP) -> list[tuple[int, int, float]]:
    """One episode under p_right(theta): a list of (cell, action, reward)."""
    cell, out = 0, []
    p = p_right(theta)
    while len(out) < cap:
        action = RIGHT if rng.random() < p else LEFT
        nxt, reward, done = step(cell, action)
        out.append((cell, action, reward))
        cell = nxt
        if done:
            break
    return out


def true_value(p: float) -> float:
    """Exact expected return from cell 0 when "right" is pressed with probability p (0 < p < 1).

    Solves the three Bellman equations v0 = -1 + p v1 + (1-p) v0, v1 = -1 + p v0 + (1-p) v2,
    v2 = -1 + (1-p) v1, which gives v0 = (4 - 2p) / (p (p - 1)). A fixed action (p = 0 or 1)
    never reaches the goal; it is reported as the cut-off, -STEP_CAP.
    """
    if p <= 0.0 or p >= 1.0:
        return -float(STEP_CAP)
    return (4.0 - 2.0 * p) / (p * (p - 1.0))


def best_p() -> tuple[float, float]:
    """(the best probability of pressing right, its value), by a fine grid search."""
    ps = np.linspace(0.001, 0.999, 99_801)
    vs = (4.0 - 2.0 * ps) / (ps * (ps - 1.0))
    i = int(vs.argmax())
    return float(ps[i]), float(vs[i])
