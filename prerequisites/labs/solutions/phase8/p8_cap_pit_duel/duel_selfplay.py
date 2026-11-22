"""Lab p8-cap · The pit-timing duel.

Page 08 is the brief. Two equal cars, one stop each, and the only question is who stops first.
You build, in seven checked stages, the game-theory side of self-play on this duel: its payoff,
best responses and the latest-only loop, fictitious play, a checkpoint pool of best responses, the
plan's pool rule, the pit-delta histogram the Phase 8 plan wants to read, and the null test on it.

THE DUEL (labs/labkit/pitgame.py, given). labkit.duel's two-car race with a real undercut window.
The FOLLOWER starts 0.5 s behind the LEADER; each car stops once, onto B, on a lap from 2 to 18
(pitgame.LAPS). With blocking on (`interaction=True`) a car within 1 s behind is held up and must
roll the dice to pass; with it off, the cars run through each other.

THE GAME. A strategy is a stop lap. The follower's payoff is +1 for finishing ahead, -1 if not,
plus 0.05 per second of final margin; the leader's is its negative (zero-sum). The follower is the
ROW player and maximises; the leader is the COLUMN player and minimises. A mixed strategy is a
probability vector over the 17 laps, indexed like pitgame.LAPS.

THE MATRIX. pitgame.matrix(interaction) holds U[i, j], the follower's payoff for laps
(LAPS[i], LAPS[j]) averaged over 20 dice seeds. It is cached; stage 1 proves the cache is honest by
rebuilding entries from your own payoff function.

THE RULER. exploitability(U, row, col) = max_i (U col)_i - min_j (row U)_j: what the two players
could gain, together, by switching to a best response. 0 exactly at a Nash equilibrium.

What is given: the loaders and the sampling helper. What you write: the functions with a TODO.

Check one stage at a time:  python -m labs check p8-cap 1   (then 2, 3, ...)
"""

from __future__ import annotations

import numpy as np

from labs.labkit import pitgame

LAPS = pitgame.LAPS
N = len(LAPS)


def matrix(interaction: bool = True) -> np.ndarray:
    """Given. The cached payoff matrix (17 x 17), follower's payoff."""
    return pitgame.matrix(interaction)


# ============================================================================ Stage 1: the payoff


def payoff(f_lap: int, l_lap: int, seed: int, interaction: bool = True) -> float:
    """The follower's payoff for one race: +1 if it finished ahead, else -1, plus
    pitgame.MARGIN_WEIGHT times (leader's final time - follower's final time).

    pitgame.race(f_lap, l_lap, seed, interaction) runs the race and returns a dict with
    "finished_ahead" (bool, the follower) and the cumulative times "agent_time" (follower) and
    "rival_time" (leader), one entry per lap.
    """
    # >>> SOLUTION: run the race, then win/lose plus the weighted margin
    r = pitgame.race(f_lap, l_lap, seed, interaction)
    win = 1.0 if r["finished_ahead"] else -1.0
    return win + pitgame.MARGIN_WEIGHT * (r["rival_time"][-1] - r["agent_time"][-1])
    # <<< SOLUTION


def expected_payoff(f_lap: int, l_lap: int, interaction: bool = True) -> float:
    """The mean of payoff over pitgame.SEEDS: one cell of the matrix."""
    # >>> SOLUTION: average payoff over the 20 seeds
    return float(np.mean([payoff(f_lap, l_lap, s, interaction) for s in pitgame.SEEDS]))
    # <<< SOLUTION


# ============================================================================ Stage 2: best responses


def best_response(U: np.ndarray, opp_mix: np.ndarray, player: str) -> int:
    """The index of the best pure reply to the opponent's mixture (lowest index on ties).

    player "row" (follower) maximises U @ opp_mix; player "col" (leader) minimises opp_mix @ U.
    """
    # >>> SOLUTION: argmax of U @ mix for the row player, argmin of mix @ U for the column player
    if player == "row":
        return int(np.argmax(U @ opp_mix))
    return int(np.argmin(opp_mix @ U))
    # <<< SOLUTION


def pure(i: int) -> np.ndarray:
    """Given. The mixture that plays index i with certainty."""
    v = np.zeros(N)
    v[i] = 1.0
    return v


def latest_only(U: np.ndarray, start: tuple[int, int], rounds: int) -> list[tuple[int, int]]:
    """Self-play against the latest snapshot only. Each round the follower best-responds to the
    leader's last lap, THEN the leader best-responds to the follower's new lap. Returns the
    (follower index, leader index) pair after each round, `rounds` pairs in all."""
    # >>> SOLUTION: row then column, each against the other's latest pure strategy
    i, j = start
    out = []
    for _ in range(rounds):
        i = best_response(U, pure(j), "row")
        j = best_response(U, pure(i), "col")
        out.append((i, j))
    return out
    # <<< SOLUTION


# ============================================================================ Stage 3: fictitious play


def exploitability(U: np.ndarray, row: np.ndarray, col: np.ndarray) -> float:
    """max_i (U col)_i - min_j (row U)_j."""
    # >>> SOLUTION: the best row reply's value minus the best column reply's value
    return float((U @ col).max() - (row @ U).min())
    # <<< SOLUTION


def fictitious_play(U: np.ndarray, iters: int, start: tuple[int, int]):
    """Best responses to the opponent's AVERAGE play so far.

    Start each player's counts with one play of its `start` index. Each round: the follower
    best-responds to the leader's frequencies and its count goes up by one; THEN the leader
    best-responds to the follower's (updated) frequencies. Record the exploitability of the two
    frequency vectors after every round.

    Returns (follower frequencies, leader frequencies, list of `iters` exploitabilities).
    """
    # >>> SOLUTION: counts, row update, column update against the new row counts, record
    cr, cc = pure(start[0]), pure(start[1])
    trace = []
    for _ in range(iters):
        cr[best_response(U, cc / cc.sum(), "row")] += 1
        cc[best_response(U, cr / cr.sum(), "col")] += 1
        trace.append(exploitability(U, cr / cr.sum(), cc / cc.sum()))
    return cr / cr.sum(), cc / cc.sum(), trace
    # <<< SOLUTION


# ============================================================================ Stage 4: a pool of best responses


def pool_mix(pool: list[int], recency_bias: float | None) -> np.ndarray:
    """The mixture over laps that sampling an opponent from `pool` gives.

    `pool` is a list of lap indices, oldest first: each entry is one frozen snapshot, and a
    snapshot here is a pure strategy. recency_bias None: every entry equally likely. Otherwise
    lab p8-03's rule: cut = max(1, int(0.8 * n)); the entries from cut on (the newest 20%) share
    recency_bias, the older ones share 1 - recency_bias; a one-entry pool is that entry for sure.
    The same lap can appear several times; its probabilities add.
    """
    # >>> SOLUTION: per-entry weights, then add them up by lap
    n = len(pool)
    if recency_bias is None or n == 1:
        w = np.full(n, 1.0 / n)
    else:
        cut = max(1, int(0.8 * n))
        w = np.where(np.arange(n) >= cut, recency_bias / (n - cut), (1 - recency_bias) / cut)
    mix = np.zeros(N)
    np.add.at(mix, np.asarray(pool), w)
    return mix
    # <<< SOLUTION


def pool_play(U: np.ndarray, rounds: int, start: tuple[int, int], recency_bias: float | None,
              max_size: int | None) -> list[float]:
    """Self-play with a checkpoint pool per player, each holding lap indices.

    Each pool starts as [start index]. Each round: the follower best-responds to
    pool_mix(leader's pool) and appends it to its pool; THEN the leader best-responds to
    pool_mix(follower's pool) and appends. If max_size is not None, each pool keeps only its newest
    max_size entries. Record exploitability(pool_mix(follower's pool), pool_mix(leader's pool))
    after every round, and return the list.
    """
    # >>> SOLUTION: as fictitious play, but through the pool and its sampling rule
    pf, pl = [start[0]], [start[1]]
    trace = []
    for _ in range(rounds):
        pf.append(best_response(U, pool_mix(pl, recency_bias), "row"))
        if max_size is not None:
            pf = pf[-max_size:]
        pl.append(best_response(U, pool_mix(pf, recency_bias), "col"))
        if max_size is not None:
            pl = pl[-max_size:]
        trace.append(exploitability(U, pool_mix(pf, recency_bias), pool_mix(pl, recency_bias)))
    return trace
    # <<< SOLUTION


# Stage 5 has no code of its own: it runs pool_play with the Phase 8 plan's rule.


# ============================================================================ Stage 6: the histogram


def delta_distribution(f_mix: np.ndarray, l_mix: np.ndarray) -> dict[int, float]:
    """P(follower's stop lap - leader's stop lap = d) when the two draw independently from their
    mixtures. Keys are the deltas d that have probability > 0, sorted; values add up to 1."""
    # >>> SOLUTION: the outer product, summed along each diagonal
    out: dict[int, float] = {}
    for i in np.flatnonzero(f_mix):
        for j in np.flatnonzero(l_mix):
            d = LAPS[i] - LAPS[j]
            out[d] = out.get(d, 0.0) + float(f_mix[i] * l_mix[j])
    return dict(sorted(out.items()))
    # <<< SOLUTION


# ============================================================================ Stage 7: your null on your result


def sample_stops(f_mix: np.ndarray, l_mix: np.ndarray, n: int, rng: np.random.Generator):
    """Given. n races in which each car draws its stop lap from its mixture before the start.
    Returns (follower laps, leader laps) as arrays."""
    laps = np.array(LAPS)
    return laps[rng.choice(N, n, p=f_mix)], laps[rng.choice(N, n, p=l_mix)]


def shuffle_p(f_laps: np.ndarray, l_laps: np.ndarray, shuffles: int, rng: np.random.Generator) -> float:
    """Lab p8-07's test. The statistic is P(delta = 0), the share of races with equal stop laps.
    Permute l_laps `shuffles` times to build the null; return the two-sided p-value
    (1 + #null values at least as far from the null's mean as the real one) / (shuffles + 1)."""
    # >>> SOLUTION: statistic, permutation null, two-sided p with the +1s
    f_laps, l_laps = np.asarray(f_laps), np.asarray(l_laps)
    real = float(np.mean(f_laps == l_laps))
    null = np.array([np.mean(f_laps == rng.permutation(l_laps)) for _ in range(shuffles)])
    far = np.abs(null - null.mean()) >= abs(real - null.mean())
    return float((far.sum() + 1) / (shuffles + 1))
    # <<< SOLUTION
