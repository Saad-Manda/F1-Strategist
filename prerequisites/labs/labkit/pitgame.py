"""The pit-timing duel of the Phase 8 labs: two equal cars, one stop each, who stops first?

Everything here is given, complete code. Labs import it; nothing in this file is a TODO.

THE RACE. `labkit.duel`'s two-car race, physics unchanged (wake, holding up, passing, with the
blocking switch `interaction`), on a tyre model with a real undercut window:

* wear 0.25 s (A) and 0.15 s (B) per lap of tyre age, a 0.3 s out-lap warm-up, B 0.3 s slower,
  fuel as in the toy race, no safety car, dry.
* The two cars are equally fast. The FOLLOWER starts 0.5 s behind the LEADER.
* Each car makes exactly one stop, onto B, on a lap from 2 to 18.

THE GAME. Each car's strategy is its stop lap. The follower's payoff is +1 if it finishes ahead,
-1 if not, plus 0.05 per second of final margin; the leader's is the negative. Zero-sum. The pass
dice are the only randomness; a payoff is averaged over 20 seeds, the same seeds for every cell
(common random numbers).

Why these tyres: with the toy race's own tyres, fresh B plus the 1.2 s warm-up is slower than
worn A, the leader's solo-optimal stop can never be beaten, and there is no undercut at all.

THE LEARNERS (for the p8-cap report). `selfplay_train` is closed-loop tabular self-play: the
state is (lap, my stop made, rival's stop made, am I ahead), the update is every-visit Monte
Carlo, and the opponent comes from the latest snapshot or from a recency pool.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from . import duel
from . import toyrace as tr
from .toyrace import PIT_B, STAY_OUT

LAPS = list(range(2, 19))
START_GAP = 0.5
MARGIN_WEIGHT = 0.05
SEEDS = range(20)
WEAR = (0.25, 0.15)
WARMUP = 0.3
B_SLOWER = 0.3

DATA = Path(__file__).resolve().parent / "data"


class DuelModel(tr.RaceModel):
    """The toy race with an undercut: steeper wear and a smaller out-lap warm-up."""

    def __init__(self, wear=WEAR, warmup=WARMUP, b_slower=B_SLOWER, **kw):
        super().__init__(sc_hazard=0.0, **kw)
        self.wear, self.warmup, self.b_slower = tuple(wear), float(warmup), float(b_slower)

    def lap_cost(self, lap, compound, age, weather=tr.DRY, sc=0):
        fuel = tr.FUEL_PER_LAP * (self.horizon - lap)
        return (tr.BASE_LAP + (self.b_slower if compound == tr.B else 0.0) + self.wear[compound] * age + fuel
                + (self.warmup if age == 1 else 0.0))


MODEL = DuelModel()


def race(f_lap: int, l_lap: int, seed: int, interaction: bool = True) -> dict:
    """One race: the follower stops on f_lap, the leader on l_lap. `duel.play`'s output."""
    return duel.play({f_lap: PIT_B}, seed, model=MODEL, rival_script={l_lap: PIT_B}, rival_slower=0.0,
                     start_gap=START_GAP, interaction=interaction)


def payoff_of(r: dict) -> float:
    win = 1.0 if r["finished_ahead"] else -1.0
    return win + MARGIN_WEIGHT * (r["rival_time"][-1] - r["agent_time"][-1])


def compute_matrix(interaction: bool, seeds=SEEDS) -> np.ndarray:
    seeds = list(seeds)
    return np.array([[np.mean([payoff_of(race(f, l, s, interaction)) for s in seeds]) for l in LAPS] for f in LAPS])


def _params() -> str:
    return json.dumps(dict(laps=LAPS, gap=START_GAP, w=MARGIN_WEIGHT, seeds=list(SEEDS), wear=WEAR, warm=WARMUP,
                           b=B_SLOWER, follow=duel.FOLLOW_GAP, wake=duel.WAKE_MAX, after=duel.AFTER_PASS), sort_keys=True)


def matrix(interaction: bool = True, cached: bool = True) -> np.ndarray:
    """U[i, j] = the follower's payoff, stopping on LAPS[i] against the leader's LAPS[j].

    Cached in labkit/data, keyed by every parameter above; recomputed (about 3 s) if any changed.
    """
    tag = "on" if interaction else "off"
    key = hashlib.sha256(_params().encode()).hexdigest()[:16]
    path = DATA / f"pitgame_{tag}_{key}.npy"
    if cached and path.exists():
        return np.load(path)
    U = compute_matrix(interaction)
    if cached:
        DATA.mkdir(exist_ok=True)
        np.save(path, U)
    return U


def lap_index(lap: int) -> int:
    return LAPS.index(lap)


def delta_distribution(f_mix: np.ndarray, l_mix: np.ndarray) -> dict[int, float]:
    """P(follower's stop lap - leader's stop lap = d) when both draw independently from their mixes."""
    out: dict[int, float] = {}
    for i, f in enumerate(LAPS):
        for j, l in enumerate(LAPS):
            out[f - l] = out.get(f - l, 0.0) + float(f_mix[i] * l_mix[j])
    return dict(sorted(out.items()))


# ---------------------------------------------------------------------------- closed-loop learners


def _key(r: duel.DuelRace, me: int) -> tuple:
    return (r.lap, r.used_both[me], r.used_both[1 - me], r.time[me] < r.time[1 - me])


def _legal(r: duel.DuelRace, me: int) -> list[int]:
    if r.used_both[me]:
        return [STAY_OUT]
    if r.model.horizon - r.lap <= 1:
        return [PIT_B]
    return [STAY_OUT, PIT_B]


def play_closed_loop(pol_f, pol_l, seed: int, interaction: bool = True):
    """Both cars choose every lap. pol(key, legal, rng) -> action. Seat 0 is the follower.

    Returns (follower's payoff, (follower transitions, leader transitions), (follower stop, leader stop)).
    Each transition is (key, action, reward); the rewards add up to the seat's payoff.
    """
    r = duel.DuelRace(model=MODEL, rival_slower=0.0, start_gap=START_GAP, interaction=interaction)
    r.reset(seed)
    rng = np.random.default_rng(seed + 10_000)
    trans: tuple[list, list] = ([], [])
    stops = [None, None]
    while not r.done:
        k = (_key(r, 0), _key(r, 1))
        a = (pol_f(k[0], _legal(r, 0), rng), pol_l(k[1], _legal(r, 1), rng))
        for i in (0, 1):
            if a[i] == PIT_B:
                stops[i] = r.lap
        r.rival_script = {r.lap: a[1]}
        before = list(r.time)
        r.step(a[0])
        lt = [r.time[i] - before[i] for i in (0, 1)]
        for i in (0, 1):
            trans[i].append((k[i], a[i], -MARGIN_WEIGHT * (lt[i] - lt[1 - i])))
    win = 1.0 if r.time[0] < r.time[1] else -1.0
    for i, sign in ((0, 1.0), (1, -1.0)):
        key, act, rew = trans[i][-1]
        trans[i][-1] = (key, act, rew + sign * win)
    return sum(x for _, _, x in trans[0]), trans, tuple(stops)


class Table:
    """A Q table over (key, action). Unseen entries are 0."""

    def __init__(self, q=None):
        self.q = {} if q is None else q

    def get(self, k):
        return self.q.setdefault(k, np.zeros(3))

    def greedy(self, k, legal, rng):
        q = self.get(k)
        return max(legal, key=lambda a: q[a])

    def frozen(self) -> "Table":
        return Table({k: v.copy() for k, v in self.q.items()})


def random_policy(k, legal, rng):
    return legal[int(rng.integers(len(legal)))]


def selfplay_train(mode: str = "pool", interaction: bool = True, races: int = 20_000, seed: int = 0,
                   every: int = 500, alpha: float = 0.1, eps: float = 0.1):
    """Closed-loop tabular self-play. mode "latest": the opponent is the last snapshot; "pool": a
    recency pool (70% from the newest 20%, the plan's rule with the n = 1 guard), seeded with a
    uniformly random policy. The learner takes either seat at random. Returns (learner, pool)."""
    rng = np.random.default_rng(seed)
    learner = Table()
    pool: list = [None]  # None stands for the random policy
    latest = learner.frozen()
    for ep in range(races):
        if mode == "latest":
            opp = latest.greedy
        else:
            n = len(pool)
            cut = max(1, int(0.8 * n))
            idx = 0 if n == 1 else (int(rng.integers(cut, n)) if rng.random() < 0.7 else int(rng.integers(0, cut)))
            opp = random_policy if pool[idx] is None else pool[idx].greedy

        def me(k, legal, r_):
            return legal[int(r_.integers(len(legal)))] if r_.random() < eps else learner.greedy(k, legal, r_)

        seat = int(rng.random() < 0.5)
        pair = (me, opp) if seat == 0 else (opp, me)
        _, trans, _ = play_closed_loop(*pair, int(rng.integers(1 << 30)), interaction)
        G = 0.0
        for k, a, x in reversed(trans[seat]):
            G += x
            q = learner.get(k)
            q[a] += alpha * (G - q[a])
        if (ep + 1) % every == 0:
            latest = learner.frozen()
            pool.append(learner.frozen())
            pool = pool[-50:]
    return learner, pool


def selfplay_deltas(learner: Table, pool: list, interaction: bool = True, races: int = 400, seed: int = 5):
    """The learner (greedy) against members of the last 20 pool entries, half the races in each seat.
    Returns arrays of (follower stop, leader stop)."""
    rng = np.random.default_rng(seed)
    out = []
    for s in range(races):
        m = pool[-1 - int(rng.integers(min(20, len(pool))))]
        opp = random_policy if m is None else m.greedy
        pair = (learner.greedy, opp) if s % 2 else (opp, learner.greedy)
        _, _, stops = play_closed_loop(*pair, s, interaction)
        out.append(stops)
    return np.array(out)
