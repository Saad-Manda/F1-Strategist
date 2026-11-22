"""Phase 6 capstone: the two-car duel race, built one stage at a time.

Page 08 is the brief. You build the toy race of the earlier capstones with a rival on track:
first two cars that ignore each other, then the wake, then being held up, then passing, then
the reward designs, and finally a check that tells a safe shaping from an unsafe one.

    Stage 1   own_lap_time, advance          two cars, each lap counted exactly once (E1, E6b)
    Stage 2   agent_ahead, observe           order read off time; a leader flag (E6c)
    Stage 3   wake_loss, apply_wake          the wake slows the CAR, not just the score (E3)
    Stage 4   resolve_close_running: hold    a faster car cannot gain on a car it cannot pass (E4)
    Stage 5   pass_chance, ... : pass        passing, judged on this lap's times (E2, E6a)
    Stage 6   rewards                        four reward designs, from one finished race
    Stage 7   shift_is_constant              which shapings leave every plan's ranking alone

Check one stage at a time:  python -m labs check p6-cap 3

THE RACE (the same numbers as labs/labkit/duel.py, which the tests compare you against)
* The 20-lap toy race of labkit.toyrace, safety car off, dry: RaceModel.cost gives a car's lap
  time on its old tyre, plus the pit loss on a lap it stops. Pit-lap semantics as before: the
  stop is made at the end of the lap, the new tyre is used from the next lap.
* Index 0 is the AGENT, index 1 the RIVAL. The rival is RIVAL_SLOWER s a lap slower and starts
  START_GAP s ahead (the agent's time starts at START_GAP, the rival's at 0). It follows a fixed
  script {lap: action}: one stop for B on lap 9.
* step() is given. Each lap it: works out both cars' own lap times; draws ONE uniform number u
  (always, so that races with the same seed share their dice); if interaction is on, adds the
  wake and resolves close running; then advances both cars.
"""

from __future__ import annotations

import math
from itertools import combinations

import numpy as np

from labs.labkit.toyrace import ACTION_NAMES, PIT_A, PIT_B, STAY_OUT, A, B, RaceModel

FOLLOW_GAP = 1.0
WAKE_MAX = 0.5
WAKE_RANGE = 1.5
PASS_STEEPNESS = 5.0
PASS_CAP = 0.95
AFTER_PASS = 0.2
RIVAL_SLOWER = 0.3
START_GAP = 0.3
RIVAL_SCRIPT = {9: PIT_B}
GAP_CAP = 10.0
PLACE_BONUS = 20.0
AGENT, RIVAL = 0, 1

QUIET = RaceModel(sc_hazard=0.0)


# ============================================================================ Stage 3


def wake_loss(gap):
    """Seconds lost in the wake of a car `gap` seconds ahead: 0.5 at zero gap, falling in a
    straight line to 0 at 1.5 s, and 0 beyond (page 04)."""
    # TODO: 0 when gap >= WAKE_RANGE, else WAKE_MAX * (WAKE_RANGE - gap) / WAKE_RANGE
    raise NotImplementedError("TODO p6-cap: 0 when gap >= WAKE_RANGE, else WAKE_MAX * (WAKE_RANGE - gap) / WAKE_RANGE")


# ============================================================================ Stage 5


def pass_chance(delta):
    """Probability that a pass succeeds; delta = my lap time - their lap time this lap.

    0 when I am not faster (delta >= 0). Otherwise page 04's sigmoid
    1 / (1 + exp(PASS_STEEPNESS * (delta + 0.5))), capped at PASS_CAP.
    """
    # TODO: 0.0 if delta >= 0, else min(PASS_CAP, the sigmoid)
    raise NotImplementedError("TODO p6-cap: 0.0 if delta >= 0, else min(PASS_CAP, the sigmoid)")


class DuelRace:
    def __init__(self, model=QUIET, rival_script=None, rival_slower=RIVAL_SLOWER, start_gap=START_GAP, interaction=True, passing=True):
        self.model = model
        self.rival_script = dict(RIVAL_SCRIPT if rival_script is None else rival_script)
        self.offset = (0.0, rival_slower)
        self.start_gap = start_gap
        self.interaction = interaction
        self.passing = passing
        self.reset(0)

    def reset(self, seed):
        """Given."""
        self.rng = np.random.default_rng(seed)
        self.lap = 1
        self.compound = [A, A]
        self.age = [1, 1]
        self.used_both = [False, False]
        self.time = [self.start_gap, 0.0]
        return self.observe()

    @property
    def done(self):
        return self.lap > self.model.horizon

    # ======================================================================== Stage 1

    def own_lap_time(self, i, action):
        """Car i's lap time on its own: RaceModel.cost for this lap, its compound and tyre age,
        and the action it takes, plus its pace offset self.offset[i]."""
        # TODO: self.model.cost(self.lap, self.compound[i], self.age[i], action) + self.offset[i]
        raise NotImplementedError("TODO p6-cap: self.model.cost(self.lap, self.compound[i], self.age[i], action) + self.offset[i]")

    def advance(self, times, actions):
        """Close the lap for both cars.

        Add times[i] to self.time[i], ONCE (this is the only place time is accumulated: bug E1
        is a second place). Then move each car's tyre on with RaceModel.next_tyre, mark
        used_both when the compound changes, and finally move self.lap on by one, for both
        cars at once (bug E6b is two halves of a step disagreeing about the lap).
        """
        # TODO: accumulate, then next_tyre / used_both for each car, then self.lap += 1
        raise NotImplementedError("TODO p6-cap: accumulate, then next_tyre / used_both for each car, then self.lap += 1")

    # ======================================================================== Stage 2

    def agent_ahead(self):
        """Order is read off accumulated time, never stored: the agent is ahead when its time is lower."""
        # TODO: self.time[AGENT] < self.time[RIVAL]
        raise NotImplementedError("TODO p6-cap: self.time[AGENT] < self.time[RIVAL]")

    def observe(self):
        """Eight float32 numbers in [0, 1]:

            0 laps left, this one included, / horizon      4 gap to the car ahead / GAP_CAP, capped at 1; 0 when leading
            1 own tyre age / horizon (capped at 1)         5 gap to the car behind / GAP_CAP, capped at 1; 0 when last
            2 1.0 if on compound B                         6 position / 2  (position is 1 or 2)
            3 1.0 if both compounds used                   7 is_leader: 1.0 when ahead

        Feature 7 is the plan's missing is_leader (bug E6c): without it, "leading" and "far
        behind" can look the same to a network.
        """
        # TODO: build the eight numbers from self.lap, self.age, self.compound, self.used_both and the gap
        raise NotImplementedError("TODO p6-cap: build the eight numbers from self.lap, self.age, self.compound, self.used_both and the gap")

    # ======================================================================== Stage 3

    def apply_wake(self, times):
        """Add wake_loss(gap) to the LAP TIME of whichever car is behind. Returns the new list.

        The car ahead is the one with less accumulated time (on a tie, the rival counts as
        ahead); gap = behind's time - ahead's time, before this lap.
        """
        # TODO: find lead and tail from self.time, then times[tail] += wake_loss(gap)
        raise NotImplementedError("TODO p6-cap: find lead and tail from self.time, then times[tail] += wake_loss(gap)")

    # ======================================================================== Stages 4 and 5

    def resolve_close_running(self, times, u):
        """The car behind, if within FOLLOW_GAP, either passes or is held up.

        `times` already includes the wake. Returns (times, passer) with passer the index of a
        car that passed this lap, or None.
        """
        times = list(times)
        lead, tail = (AGENT, RIVAL) if self.time[AGENT] < self.time[RIVAL] else (RIVAL, AGENT)
        if self.time[tail] - self.time[lead] >= FOLLOW_GAP:
            return times, None
        if self.passing:
            # Stage 5. Attempt a pass when u < pass_chance(this lap's tail time - this lap's
            # lead time). On success the passer keeps its own time, but must finish the lap at
            # least AFTER_PASS ahead of the other car: its lap time becomes
            #     min(its time, (lead's total + lead's lap time) - AFTER_PASS - its total)
            # and the pass is returned at once.
            # TODO: if u < pass_chance(times[tail] - times[lead]): set times[tail] as above and return times, tail
            raise NotImplementedError("TODO p6-cap: if u < pass_chance(times[tail] - times[lead]): set times[tail] as above and return times, tail")
        # Stage 4. No pass: the car behind cannot be faster than the car ahead this lap.
        # TODO: times[tail] = max(times[tail], times[lead])
        raise NotImplementedError("TODO p6-cap: times[tail] = max(times[tail], times[lead])")
        return times, None

    # ======================================================================== given

    def step(self, action):
        """Given. One lap. Returns (the agent's lap time, info)."""
        if self.done:
            raise RuntimeError("the race is over")
        lap = self.lap
        actions = (action, self.rival_script.get(lap, STAY_OUT))
        times = [self.own_lap_time(i, actions[i]) for i in (AGENT, RIVAL)]
        u = self.rng.random()
        passer = None
        if self.interaction:
            times = self.apply_wake(times)
            times, passer = self.resolve_close_running(times, u)
        before = list(self.time)
        self.advance(times, actions)
        return self.time[AGENT] - before[AGENT], {"lap": lap, "rival_lap_time": self.time[RIVAL] - before[RIVAL], "passer": passer}


# ============================================================================ given: whole races


def play(plan, seed, **race_kwargs):
    """Drive one race with an open-loop plan {lap: action}; the same dict as labkit.duel.play."""
    race = DuelRace(**race_kwargs)
    race.reset(seed)
    out = {"lap_times": [], "agent_time": [], "rival_time": [], "ahead": []}
    while not race.done:
        t, _ = race.step(plan.get(race.lap, STAY_OUT))
        out["lap_times"].append(t)
        out["agent_time"].append(race.time[AGENT])
        out["rival_time"].append(race.time[RIVAL])
        out["ahead"].append(race.agent_ahead())
    out["finished_ahead"] = out["ahead"][-1]
    out["total"] = race.time[AGENT]
    out["start_gap"] = race.start_gap
    return out


def one_stop_plans(horizon=20):
    return [{lap: PIT_B} for lap in range(1, horizon)]


def two_stop_plans(horizon=20):
    return [{l1: PIT_B, l2: PIT_A} for l1, l2 in combinations(range(1, horizon), 2)]


def plan_name(plan):
    return " + ".join(f"lap {lap} {ACTION_NAMES[a]}" for lap, a in sorted(plan.items())) or "no stop"


# ============================================================================ Stage 6


def potential(ahead, final):
    """Given. Φ = -position / 2 during the race, and 0 once it is over."""
    return 0.0 if final else -(1 if ahead else 2) / 2


def rewards(race, kind):
    """The per-lap rewards of a finished race (a dict from play) under one design.

    "time"             -lap time, every lap
    "time_plus_place"  -lap time, plus PLACE_BONUS on the last lap if the agent finished ahead
    "gap_change"       the plan's formula: -(gap now - gap a lap ago), with the gap taken as
                       agent time - rival time after each lap, and the gap "a lap ago" starting
                       at 0 (the plan resets it to 0.0)
    "potential"        time_plus_place, plus Φ(s') - Φ(s) every lap, γ = 1. Φ(s) for the start
                       is potential(race["start_gap"] < 0, False); after lap i it is
                       potential(race["ahead"][i], i is the last lap)

    Two more designs are given below yours: the plan's flat bonus (E5) and the potential
    without its zero at the finish. Stage 7 needs them.
    """
    H = len(race["lap_times"])
    out = []
    if kind in ("time", "time_plus_place", "potential"):
        # TODO: -lap time; + PLACE_BONUS at the finish if ahead (not for "time"); + Φ(s') - Φ(s) for "potential"
        raise NotImplementedError("TODO p6-cap: -lap time; + PLACE_BONUS at the finish if ahead (not for \"time\"); + Φ(s') - Φ(s) for \"potential\"")
    if kind == "gap_change":
        # TODO: prev = 0.0; each lap gap = agent_time[i] - rival_time[i]; append -(gap - prev); prev = gap
        raise NotImplementedError("TODO p6-cap: prev = 0.0; each lap gap = agent_time[i] - rival_time[i]; append -(gap - prev); prev = gap")
    base = rewards(race, "time_plus_place")
    if kind == "flat_bonus":  # given: the plan's "potential_shaping" branch (E5)
        return [r + (0.5 if race["ahead"][i] else 0.0) for i, r in enumerate(base)]
    if kind == "unzeroed":  # given: a real Φ difference, but Φ is not set to 0 at the finish
        prev_phi, out = potential(race["start_gap"] < 0, False), []
        for i, r in enumerate(base):
            phi = potential(race["ahead"][i], False)
            out.append(r + phi - prev_phi)
            prev_phi = phi
        return out
    raise ValueError(f"unknown reward kind {kind!r}")


def plan_returns(plans, kind, seeds, **race_kwargs):
    """Given. returns[i, j] = the return of plans[i] on seeds[j], every plan on the same seeds."""
    seeds = list(seeds)
    return np.array([[sum(rewards(play(p, s, **race_kwargs), kind)) for s in seeds] for p in plans])


# ============================================================================ Stage 7


def shift_is_constant(kind, plans, seeds, base="time_plus_place", tol=1e-9):
    """True when `kind` adds the same constant to the return of EVERY plan on EVERY seed,
    compared with `base`. Such a shaping cannot change which plan is best, on any race.

    Compare race by race, not averages: a shaping that shifts some races and not others can
    average out to a constant over the plans you happened to try.
    """
    # TODO: diff = plan_returns(plans, kind, seeds) - plan_returns(plans, base, seeds); its max - min must be <= tol
    raise NotImplementedError("TODO p6-cap: diff = plan_returns(plans, kind, seeds) - plan_returns(plans, base, seeds); its max - min must be <= tol")
