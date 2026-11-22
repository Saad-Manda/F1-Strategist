"""The toy race of the capstones, as a model that can be queried instead of played.

The Phase 1 capstone builds this race as a Gymnasium environment: you can only step through
it. A planner needs more: for any state and action it must be able to ask "what does this
cost, and where could it lead, with what probability?" `RaceModel` answers those questions.
The numbers are the Phase 1 capstone's.

Everything here is given, complete code. Labs import it; nothing in this file is a TODO.

THE RACE
--------
* `horizon` laps (20 by default). Laps are numbered from 1. One decision per lap.
* Two compounds: A (0) is fast and fragile, B (1) is slow and durable. The race starts on a
  new compound A (age 1), under a green flag.
* Actions: STAY_OUT, PIT_A, PIT_B. A lap is always driven on the tyre fitted at its start;
  a pit stop adds the pit loss to that lap and the new tyre (age 1) is used from the next lap.
* A safety car may be out on a lap. Such a lap takes a fixed time, and a stop made on it
  costs only a fraction of the normal pit loss.
* Weather is DRY or WET on each lap. How it changes from lap to lap depends on the mode:
      weather="fixed"    it never changes (the Phase 1 capstone's world)
      weather="markov"   it follows the two-state chain WEATHER_CHAIN
      weather_trace=[..] it follows a known list, one entry per lap (perfect foresight)
"""

from __future__ import annotations

import numpy as np

STAY_OUT, PIT_A, PIT_B = 0, 1, 2
ALL_ACTIONS = (STAY_OUT, PIT_A, PIT_B)
A, B = 0, 1
DRY, WET = 0, 1
COMPOUND_NAMES = ("A", "B")
ACTION_NAMES = ("STAY_OUT", "PIT_A", "PIT_B")

HORIZON = 20
BASE_LAP = 10.0
PIT_LOSS = 4.0
PACE = (0.0, 0.6)
WEAR_RATE = (0.05, 0.02)
CLIFF_AGE = (6, 11)
CLIFF_SEVERITY = (0.15, 0.08)
CLIFF_CAP = 4.0
FUEL_PER_LAP = 0.03
WET_PENALTY = (6.0, 5.5)  # seconds lost in the wet, per compound
WARMUP = {1: 1.2, 2: 0.5}
SC_HAZARD = 0.06
SC_CONTINUE = 2 / 3
SC_LAP_TIME = 14.0
SC_PIT_DISCOUNT = 0.4
WEATHER_CHAIN = ((0.9, 0.1), (0.3, 0.7))  # row = weather now, column = weather next lap


class RaceModel:
    def __init__(
        self,
        horizon: int = HORIZON,
        pit_loss: float = PIT_LOSS,
        sc_hazard: float = SC_HAZARD,
        sc_continue: float = SC_CONTINUE,
        weather: str = "fixed",
        weather_trace: list[int] | None = None,
    ):
        if weather not in ("fixed", "markov"):
            raise ValueError('weather must be "fixed" or "markov"')
        if weather_trace is not None and len(weather_trace) != horizon:
            raise ValueError("weather_trace needs one entry per lap")
        self.horizon = horizon
        self.pit_loss = pit_loss
        self.sc_hazard = sc_hazard
        self.sc_continue = sc_continue
        self.weather = weather
        self.weather_trace = None if weather_trace is None else [int(w) for w in weather_trace]

    # ------------------------------------------------------------------ costs

    def lap_cost(self, lap: int, compound: int, age: int, weather: int = DRY, sc: int = 0) -> float:
        """Time of lap number `lap`, driven on `compound` at tyre age `age`, with no pit stop."""
        if sc:
            return SC_LAP_TIME
        over = max(0, age - CLIFF_AGE[compound])
        wear = WEAR_RATE[compound] * age + min(CLIFF_SEVERITY[compound] * over**2, CLIFF_CAP)
        fuel = FUEL_PER_LAP * (self.horizon - lap)
        wet = WET_PENALTY[compound] if weather == WET else 0.0
        return BASE_LAP + PACE[compound] + wear + fuel + wet + WARMUP.get(age, 0.0)

    def pit_cost(self, sc: int = 0) -> float:
        """Time a pit stop adds to the lap it is made on."""
        return self.pit_loss * (SC_PIT_DISCOUNT if sc else 1.0)

    def cost(self, lap: int, compound: int, age: int, action: int, weather: int = DRY, sc: int = 0) -> float:
        """Total time of the lap when `action` is taken on it."""
        return self.lap_cost(lap, compound, age, weather, sc) + (self.pit_cost(sc) if action != STAY_OUT else 0.0)

    # ------------------------------------------------------------------ what happens next

    @staticmethod
    def next_tyre(compound: int, age: int, action: int) -> tuple[int, int]:
        """(compound, age) the NEXT lap is driven on."""
        if action == PIT_A:
            return A, 1
        if action == PIT_B:
            return B, 1
        return compound, age + 1

    def sc_prob(self, sc_now: int) -> float:
        """Probability that the safety car is out on the next lap."""
        return self.sc_continue if sc_now else self.sc_hazard

    def weather_probs(self, lap: int, weather: int) -> tuple[float, float]:
        """(P(DRY on lap + 1), P(WET on lap + 1)), given the weather on lap `lap`."""
        if self.weather_trace is not None:
            nxt = self.weather_trace[lap] if lap < self.horizon else weather  # trace[lap] is lap + 1
            return (1.0, 0.0) if nxt == DRY else (0.0, 1.0)
        if self.weather == "markov":
            return WEATHER_CHAIN[weather]
        return (1.0, 0.0) if weather == DRY else (0.0, 1.0)

    # ------------------------------------------------------------------ rules

    def legal_actions(self, lap: int, compound: int, weather: int, used_both: bool) -> list[int]:
        """The Phase 1 capstone's four mask rules, as a list of legal actions.

        1. No pit stop for the compound already fitted.
        2. In the WET, compound B is unsafe: PIT_B is illegal.
        3. In the DRY, both compounds must be used. If they have not been and at most one lap
           remains after this one, STAY_OUT is illegal.
        4. If nothing is legal after rules 1-3, STAY_OUT is.
        """
        legal = [STAY_OUT, PIT_A, PIT_B]
        legal.remove(PIT_A if compound == A else PIT_B)
        if weather == WET and PIT_B in legal:
            legal.remove(PIT_B)
        if weather == DRY and not used_both and self.horizon - lap <= 1:
            legal.remove(STAY_OUT)
        return legal or [STAY_OUT]


def simulate(model: RaceModel, policy, rng: np.random.Generator, start_weather: int = DRY) -> dict:
    """Drive one race with real dice. Given.

    `policy(lap, compound, age, sc, used_both, weather)` returns an action. Returns a dict with
    the total "time", the list of "actions", and whether "used_both" compounds were used.
    """
    compound, age, sc, used_both = A, 1, 0, False
    weather = model.weather_trace[0] if model.weather_trace is not None else start_weather
    total, actions = 0.0, []
    for lap in range(1, model.horizon + 1):
        action = policy(lap, compound, age, sc, used_both, weather)
        total += model.cost(lap, compound, age, action, weather, sc)
        actions.append(action)
        new_compound, age = model.next_tyre(compound, age, action)
        used_both = used_both or new_compound != compound
        compound = new_compound
        sc = int(rng.random() < model.sc_prob(sc))
        weather = int(rng.random() < model.weather_probs(lap, weather)[WET])
    return {"time": total, "actions": actions, "used_both": used_both}


# ---------------------------------------------------------------------------- reference answers


def state_space(model: RaceModel):
    """Every (lap, compound, age, sc, used_both, weather) with lap in 1..horizon and age <= lap."""
    for lap in range(1, model.horizon + 1):
        for compound in (A, B):
            for age in range(1, lap + 1):
                for sc in (0, 1):
                    for used_both in (False, True):
                        for weather in (DRY, WET):
                            yield lap, compound, age, sc, used_both, weather


def _backward(model: RaceModel, choose):
    """One backward pass. `choose(state, totals)` picks the action given {action: total}."""
    H = model.horizon
    V = {
        (H + 1, c, age, sc, used, w): 0.0
        for c in (A, B)
        for age in range(1, H + 2)
        for sc in (0, 1)
        for used in (False, True)
        for w in (DRY, WET)
    }
    policy = {}
    for state in sorted(state_space(model), reverse=True):
        lap, c, age, sc, used, w = state
        p_sc, p_w = model.sc_prob(sc), model.weather_probs(lap, w)
        totals = {}
        for action in model.legal_actions(lap, c, w, used):
            next_c, next_age = model.next_tyre(c, age, action)
            next_used = used or next_c != c
            expected = sum(
                p1 * p2 * V[(lap + 1, next_c, next_age, next_sc, next_used, next_w)]
                for next_sc, p1 in ((0, 1 - p_sc), (1, p_sc))
                for next_w, p2 in ((DRY, p_w[DRY]), (WET, p_w[WET]))
            )
            totals[action] = model.cost(lap, c, age, action, w, sc) + expected
        policy[state] = choose(state, totals)
        V[state] = totals[policy[state]]
    return V, policy


def solve(model: RaceModel) -> tuple[dict, dict]:
    """The exact optimum: (V, policy) keyed by (lap, compound, age, sc, used_both, weather).

    This is the answer the Phase 3.5 capstone has you compute yourself. Later capstones use it
    as their ruler.
    """
    return _backward(model, lambda state, totals: min(totals, key=lambda a: (totals[a], a)))


def expected_time(model: RaceModel, policy, start_weather: int = DRY) -> float:
    """Exact expected race time of following `policy(lap, compound, age, sc, used_both, weather)`.

    No races are simulated: this is the same backward pass with the action fixed by the policy,
    so the number has no sampling noise. An illegal action is replaced by the first legal one.
    """

    def choose(state, totals):
        action = policy(*state)
        return action if action in totals else min(totals)

    V, _ = _backward(model, choose)
    return V[(1, A, 1, 0, False, start_weather)]
