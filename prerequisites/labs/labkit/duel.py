"""The two-car duel race of the Phase 6 labs: the toy race with a rival on track.

Everything here is given, complete code. Labs import it; nothing in this file is a TODO. The
Phase 6 capstone has you build the same race yourself (`duel_race.py`); this copy is the
reference its tests compare against, and later capstones use it so that they do not depend
on your file.

THE RACE
--------
* Two cars on the 20-lap toy race of `labkit.toyrace` (same lap costs, same pit rules), with
  the safety car switched off and the weather dry.
* The RIVAL is 0.3 s a lap slower (car pace) and starts 0.3 s ahead. It follows a fixed
  script, by default one stop for compound B on lap 9. It never reacts to anything.
* The AGENT starts on compound A, 0.3 s behind, and takes one action per lap.
* Both cars always drive the same lap number.

WHAT HAPPENS ON EACH LAP (when interaction is on)
--------------------------------------------------
1. Each car's own lap time: `RaceModel.cost` (old tyre, plus the pit loss if it stops), plus
   the car's pace offset.
2. The car behind, `gap` seconds back, loses `wake_loss(gap)` to the car ahead's wake. This is
   added to its LAP TIME, so it moves the race, not just a score (the plan's bug E3).
3. If the car behind is within FOLLOW_GAP, it may try to pass: one uniform draw `u` per lap,
   success if `u < pass_chance(delta)`, where `delta` is its own time this lap (wake loss
   included) minus the car ahead's time THIS lap (not an average: bug E6a).
   - No pass: it is held up. Its lap time becomes max(its own, the car ahead's). It cannot
     gain on a car it cannot get past (the page-05 line, the plan's gap E4).
   - Pass: it drives its own time, and finishes the lap at least AFTER_PASS ahead.
4. Order is always read off accumulated time. Nothing stores a position that a later line could
   overwrite (the plan's bug E2).

With interaction off, each car simply drives its own lap time: no wake, no holding up, no
passing. That is the plan's world, where position is only a readout of time.
"""

from __future__ import annotations

import math
from itertools import combinations

import numpy as np

from .toyrace import ACTION_NAMES, PIT_A, PIT_B, STAY_OUT, A, B, RaceModel

FOLLOW_GAP = 1.0  # within this many seconds the car behind is held up unless it passes
WAKE_MAX = 0.5  # wake loss at zero gap, seconds
WAKE_RANGE = 1.5  # no wake loss from this gap on
PASS_STEEPNESS = 5.0  # the plan's sigmoid: 1 / (1 + exp(5 * (delta + 0.5)))
PASS_CAP = 0.95
AFTER_PASS = 0.2  # a successful pass ends the lap at least this far ahead
RIVAL_SLOWER = 0.3  # seconds per lap
START_GAP = 0.3  # the agent starts this far behind
RIVAL_SCRIPT = {9: PIT_B}
GAP_CAP = 10.0  # gaps are normalised by this in the observation
PLACE_BONUS = 20.0  # seconds-equivalent per place, at the finish (the plan's position_bonus_scale)

QUIET = RaceModel(sc_hazard=0.0)


def wake_loss(gap: float) -> float:
    """Seconds lost in the wake of a car `gap` seconds ahead: 0.5 at zero, 0 from 1.5 on."""
    if gap >= WAKE_RANGE:
        return 0.0
    return WAKE_MAX * (WAKE_RANGE - max(gap, 0.0)) / WAKE_RANGE


def pass_chance(delta: float) -> float:
    """Probability that a pass succeeds. `delta` = my lap time - their lap time (negative: I am faster)."""
    if delta >= 0:
        return 0.0
    return min(PASS_CAP, 1.0 / (1.0 + math.exp(PASS_STEEPNESS * (delta + 0.5))))


class DuelRace:
    """The reference two-car race. `reset(seed)`, then `step(action)` once per lap."""

    def __init__(
        self,
        model: RaceModel = QUIET,
        rival_script: dict | None = None,
        rival_slower: float = RIVAL_SLOWER,
        start_gap: float = START_GAP,
        interaction: bool = True,
        passing: bool = True,
    ):
        self.model = model
        self.rival_script = dict(RIVAL_SCRIPT if rival_script is None else rival_script)
        self.offset = (0.0, rival_slower)
        self.start_gap = start_gap
        self.interaction = interaction
        self.passing = passing
        self.reset(0)

    # ------------------------------------------------------------------ state

    def reset(self, seed: int) -> np.ndarray:
        self.rng = np.random.default_rng(seed)
        self.lap = 1
        self.compound = [A, A]
        self.age = [1, 1]
        self.used_both = [False, False]
        self.time = [self.start_gap, 0.0]  # [agent, rival]
        return self.observe()

    @property
    def done(self) -> bool:
        return self.lap > self.model.horizon

    def gap(self) -> float:
        """Agent time minus rival time: positive means the agent is behind."""
        return self.time[0] - self.time[1]

    def agent_ahead(self) -> bool:
        return self.time[0] < self.time[1]

    def position(self) -> int:
        return 1 if self.agent_ahead() else 2

    def observe(self) -> np.ndarray:
        """Eight numbers in [0, 1]: four about the agent's own car, four about the duel."""
        H = self.model.horizon
        g = abs(self.gap())
        ahead = self.agent_ahead()
        return np.array(
            [
                (H - self.lap + 1) / H,  # laps left, this one included
                min(self.age[0], H) / H,
                float(self.compound[0] == B),
                float(self.used_both[0]),
                0.0 if ahead else min(g / GAP_CAP, 1.0),  # gap to the car ahead
                min(g / GAP_CAP, 1.0) if ahead else 0.0,  # gap to the car behind
                self.position() / 2,
                float(ahead),  # is_leader: tells "leading" from "far behind" (bug E6c)
            ],
            dtype=np.float32,
        )

    # ------------------------------------------------------------------ one lap

    def step(self, action: int) -> tuple[float, dict]:
        """Drive one lap. Returns (the agent's lap time, info)."""
        if self.done:
            raise RuntimeError("the race is over")
        lap = self.lap
        actions = (action, self.rival_script.get(lap, STAY_OUT))
        own = [self.model.cost(lap, self.compound[i], self.age[i], actions[i]) + self.offset[i] for i in (0, 1)]
        times = list(own)
        u = self.rng.random()  # one draw per lap, used or not, so races with the same seed share their dice
        lead, tail = (0, 1) if self.time[0] < self.time[1] else (1, 0)
        gap = self.time[tail] - self.time[lead]
        held = passed = False
        wake = 0.0
        if self.interaction:
            wake = wake_loss(gap)
            times[tail] += wake
            if gap < FOLLOW_GAP:
                if self.passing and u < pass_chance(times[tail] - times[lead]):
                    passed = True
                elif times[tail] < times[lead]:
                    held = True
                    times[tail] = times[lead]
        before = list(self.time)
        for i in (0, 1):
            self.time[i] += times[i]
        if passed and self.time[tail] > self.time[lead] - AFTER_PASS:
            self.time[tail] = self.time[lead] - AFTER_PASS
        for i in (0, 1):
            new_compound, self.age[i] = self.model.next_tyre(self.compound[i], self.age[i], actions[i])
            self.used_both[i] = self.used_both[i] or new_compound != self.compound[i]
            self.compound[i] = new_compound
        self.lap += 1
        lap_times = [self.time[i] - before[i] for i in (0, 1)]
        info = {
            "lap": lap,
            "rival_lap_time": lap_times[1],
            "agent_wake": wake if tail == 0 else 0.0,
            "agent_held": held and tail == 0,
            "passed": passed,
            "passer": ("agent", "rival")[tail] if passed else None,
        }
        return lap_times[0], info


# ---------------------------------------------------------------------------- whole races


def play(plan: dict, seed: int, **race_kwargs) -> dict:
    """Drive one race with an open-loop plan {lap: action}. Returns the race, lap by lap.

    keys: "lap_times" (agent), "agent_time" / "rival_time" (accumulated, after each lap),
    "ahead" (agent ahead after each lap), "finished_ahead", "total".
    """
    race = DuelRace(**race_kwargs)
    race.reset(seed)
    out = {"lap_times": [], "agent_time": [], "rival_time": [], "ahead": []}
    while not race.done:
        t, _ = race.step(plan.get(race.lap, STAY_OUT))
        out["lap_times"].append(t)
        out["agent_time"].append(race.time[0])
        out["rival_time"].append(race.time[1])
        out["ahead"].append(race.agent_ahead())
    out["finished_ahead"] = out["ahead"][-1]
    out["total"] = race.time[0]
    out["start_gap"] = race.start_gap
    return out


def one_stop_plans(horizon: int = 20) -> list[dict]:
    """Every single stop for compound B, the only one-stop plans that use both compounds."""
    return [{lap: PIT_B} for lap in range(1, horizon)]


def two_stop_plans(horizon: int = 20) -> list[dict]:
    """B then A, at any two laps."""
    return [{l1: PIT_B, l2: PIT_A} for l1, l2 in combinations(range(1, horizon), 2)]


def plan_name(plan: dict) -> str:
    return " + ".join(f"lap {lap} {ACTION_NAMES[a]}" for lap, a in sorted(plan.items())) or "no stop"


# ---------------------------------------------------------------------------- rewards


def potential(ahead: bool, final: bool) -> float:
    """Φ = -position / 2, and Φ = 0 once the race is over: the zero at the finish keeps it safe."""
    return 0.0 if final else -(1 if ahead else 2) / 2


def rewards(race: dict, kind: str) -> list[float]:
    """The per-lap rewards of a finished race under one reward design.

    "time"            -lap time                                     the honest single-car reward
    "time_plus_place" -lap time, + PLACE_BONUS per place beaten at the finish
    "gap_change"      -(change in gap to the rival)                 the plan's formula, gap starts at 0
    "potential"       time_plus_place + Φ(s') - Φ(s), Φ = -position/2, Φ(finish) = 0
    "flat_bonus"      time_plus_place + 1/2 every lap the agent is not last   (the plan's E5)
    "unzeroed"        time_plus_place + Φ(s') - Φ(s) without the zero at the finish
    """
    H = len(race["lap_times"])
    out, prev_gap = [], 0.0
    prev_phi = potential(race["start_gap"] < 0, False)
    for i in range(H):
        final = i == H - 1
        ahead = race["ahead"][i]
        r = -race["lap_times"][i]
        if kind == "gap_change":
            gap = race["agent_time"][i] - race["rival_time"][i]
            out.append(-(gap - prev_gap))
            prev_gap = gap
            continue
        if kind != "time" and final:
            r += PLACE_BONUS * (1 if ahead else 0)
        if kind == "potential":
            phi = potential(ahead, final)
            r += phi - prev_phi
            prev_phi = phi
        elif kind == "unzeroed":
            phi = potential(ahead, False)
            r += phi - prev_phi
            prev_phi = phi
        elif kind == "flat_bonus":
            r += 0.5 if ahead else 0.0
        elif kind not in ("time", "time_plus_place"):
            raise ValueError(f"unknown reward kind {kind!r}")
        out.append(r)
    return out


def plan_returns(plans: list[dict], kind: str, seeds, **race_kwargs) -> np.ndarray:
    """returns[i, j] = the return of plans[i] on seed j. Same seeds for every plan."""
    seeds = list(seeds)
    return np.array([[sum(rewards(play(p, s, **race_kwargs), kind)) for s in seeds] for p in plans])


def finish_ahead_rate(plan: dict, seeds, **race_kwargs) -> float:
    seeds = list(seeds)
    return float(np.mean([play(plan, s, **race_kwargs)["finished_ahead"] for s in seeds]))
