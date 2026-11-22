"""Given code for lab p6-06: a three-car mini race, written the way the plan writes its race.

Read it; do not edit it. `Race(bugs={...})` switches on any of the three bugs page 06 describes,
in the same shape as the plan's pseudocode. `Race()` with no bugs is the reference.

    "E1"  every rival's lap time is added to its total twice: once in Car.drive_lap, which owns
          the accumulation, and again by a loop in Race.step
    "E2"  a successful pass moves the stored position up by one, and the re-sort two lines later
          overwrites it; passing is also not part of the timing, so nothing else changes either
    "E3"  the wake loss is taken off the reward but never added to the lap time

THE RACE. Three cars, 15 laps, each with a fixed pace. The agent starts 0.4 s behind RIVAL_1,
which is 0.4 s a lap slower; RIVAL_2 starts 6 s back and is slowest. Each lap costs the car's
pace plus 0.05 s per lap of tyre age. The agent chooses STAY (0) or PIT (1: +20 s, tyres reset);
the rivals never stop. In the reference the car behind loses wake time, is held up within 1 s
unless a pass succeeds (one random draw per lap), and positions are read off total time.
"""

from __future__ import annotations

import math

import numpy as np

STAY, PIT = 0, 1
LAPS = 15
PIT_LOSS = 20.0
WEAR = 0.05
FOLLOW_GAP = 1.0


def wake_loss(gap):
    return 0.0 if gap >= 1.5 else 0.5 * (1.5 - gap) / 1.5


def pass_chance(delta):
    return 0.0 if delta >= 0 else min(0.95, 1 / (1 + math.exp(5 * (delta + 0.5))))


class Car:
    def __init__(self, name, pace, start):
        self.name = name
        self.pace = pace
        self.total_time = start
        self.age = 1
        self.position = 0
        self.last_lap_time = 0.0

    def own_time(self, action=STAY):
        return self.pace + WEAR * self.age + (PIT_LOSS if action == PIT else 0.0)

    def drive_lap(self, lap_time, action=STAY):
        """Owns the accumulation: adds this lap to total_time, exactly once."""
        self.total_time += lap_time
        self.last_lap_time = lap_time
        self.age = 1 if action == PIT else self.age + 1


class Race:
    def __init__(self, passing: bool = True, seed: int = 0, bugs=()):
        self.bugs = set(bugs)
        self.passing = passing
        self.rng = np.random.default_rng(seed)
        self.agent = Car("AGENT", 80.0, 0.4)
        self.cars = [self.agent, Car("RIVAL_1", 80.4, 0.0), Car("RIVAL_2", 81.0, 6.0)]
        self.rivals = self.cars[1:]
        self.lap = 1
        self._sort_positions()

    @property
    def done(self):
        return self.lap > LAPS

    def order(self):
        """Car names from first to last, by stored position."""
        return [c.name for c in sorted(self.cars, key=lambda c: c.position)]

    def _sort_positions(self):
        for pos, car in enumerate(sorted(self.cars, key=lambda c: c.total_time), start=1):
            car.position = pos

    def step(self, action):
        """One lap for all three cars. Returns (reward, info)."""
        actions = {c.name: (action if c is self.agent else STAY) for c in self.cars}
        times = {c.name: c.own_time(actions[c.name]) for c in self.cars}
        u = self.rng.random()
        ranked = sorted(self.cars, key=lambda c: c.total_time)
        agent_wake, passed = 0.0, False
        for ahead, car in zip(ranked, ranked[1:]):
            gap = car.total_time - ahead.total_time
            wake = wake_loss(gap)
            if car is self.agent:
                agent_wake = wake
            if "E3" in self.bugs and car is self.agent:
                pass  # E3: the agent's wake loss never reaches its lap time
            else:
                times[car.name] += wake
            if gap < FOLLOW_GAP and "E2" not in self.bugs:
                if self.passing and u < pass_chance(times[car.name] - times[ahead.name]):
                    passed = car is self.agent or passed
                    times[car.name] = min(times[car.name], ahead.total_time + times[ahead.name] - 0.2 - car.total_time)
                else:
                    times[car.name] = max(times[car.name], times[ahead.name])
            elif gap < FOLLOW_GAP and car is self.agent and self.passing:
                if u < pass_chance(times[car.name] - times[ahead.name]):
                    self.agent.position -= 1  # E2: the pass is recorded in the position ...
                    passed = True

        for car in self.cars:
            car.drive_lap(times[car.name], actions[car.name])
        if "E1" in self.bugs:
            for rival in self.rivals:  # E1: drive_lap already added this lap
                rival.total_time += times[rival.name]
        self._sort_positions()  # ... and E2's position is overwritten here

        reward = -times["AGENT"]
        if "E3" in self.bugs:
            reward -= agent_wake  # E3: charged to the reward instead
        self.lap += 1
        return reward, {"agent_lap_time": times["AGENT"], "agent_wake": agent_wake, "agent_passed": passed}


def run(race, plan=None):
    """Drive a race to the end. `plan` maps lap -> action (default: never pit). Returns the rewards."""
    plan = plan or {}
    rewards = []
    while not race.done:
        r, _ = race.step(plan.get(race.lap, STAY))
        rewards.append(r)
    return rewards
