"""Small two-player zero-sum matrix games and the tools Phase 8's labs use on them.

Everything here is given, complete code. Labs import it; nothing in this file is a TODO.

Conventions: U[i, j] is the ROW player's payoff when row plays i and column plays j. The game is
zero-sum, so the column player's payoff is -U[i, j]. The row player maximises, the column player
minimises. A mixed strategy is a probability vector over a player's actions.
"""

from __future__ import annotations

import numpy as np

# Page 02's original 2x2 (Rock, Paper). Paper beats Rock and ties Paper, so P dominates R.
DOMINATED = np.array([[0.0, -1.0], [1.0, 0.0]])
DOMINATED_NAMES = ("R", "P")

# Matching pennies: row wins on a match, column wins on a mismatch. No pure equilibrium.
MATCHING_PENNIES = np.array([[1.0, -1.0], [-1.0, 1.0]])
PENNIES_NAMES = ("H", "T")

# Rock-paper-scissors.
RPS = np.array([[0.0, -1.0, 1.0], [1.0, 0.0, -1.0], [-1.0, 1.0, 0.0]])
RPS_NAMES = ("R", "P", "S")


def pure(n: int, i: int) -> np.ndarray:
    v = np.zeros(n)
    v[i] = 1.0
    return v


def value(U: np.ndarray, row: np.ndarray, col: np.ndarray) -> float:
    """Expected payoff to the row player."""
    return float(row @ U @ col)


def row_best_response(U: np.ndarray, col: np.ndarray) -> int:
    """The row action with the highest expected payoff against the column mixture (lowest index on ties)."""
    return int(np.argmax(U @ col))


def col_best_response(U: np.ndarray, row: np.ndarray) -> int:
    """The column action with the lowest expected payoff to row against the row mixture."""
    return int(np.argmin(row @ U))


def exploitability(U: np.ndarray, row: np.ndarray, col: np.ndarray) -> float:
    """How much the two players could gain, in total, by each switching to a best response.

    max_i (U col)_i - min_j (row U)_j. It is 0 exactly at a Nash equilibrium and positive otherwise.
    """
    return float((U @ col).max() - (row @ U).min())


def latest_dynamics(U: np.ndarray, start: tuple[int, int], rounds: int) -> list[tuple[int, int]]:
    """Best response to the opponent's LATEST action, row first, then column. Returns the pairs played."""
    i, j = start
    out = []
    for _ in range(rounds):
        i = row_best_response(U, pure(U.shape[1], j))
        j = col_best_response(U, pure(U.shape[0], i))
        out.append((i, j))
    return out


def fictitious_play(U: np.ndarray, iters: int, start: tuple[int, int] = (0, 0), every: int = 0):
    """Each round both players best-respond to the other's AVERAGE play so far.

    Returns (row_mix, col_mix, trace) where the mixes are the empirical frequencies and trace is a
    list of (iteration, exploitability) recorded every `every` rounds (empty if every == 0).
    """
    cr, cc = pure(U.shape[0], start[0]), pure(U.shape[1], start[1])
    trace = []
    for t in range(1, iters + 1):
        cr[row_best_response(U, cc / cc.sum())] += 1
        cc[col_best_response(U, cr / cr.sum())] += 1
        if every and t % every == 0:
            trace.append((t, exploitability(U, cr / cr.sum(), cc / cc.sum())))
    return cr / cr.sum(), cc / cc.sum(), trace


def find_period(seq: list, tail: int = 12) -> int:
    """The length of the cycle the end of `seq` repeats (1 means it has settled), or 0 if none is found."""
    end = seq[-tail:]
    for p in range(1, tail // 2 + 1):
        if all(end[k] == end[k + p] for k in range(len(end) - p)):
            return p
    return 0
