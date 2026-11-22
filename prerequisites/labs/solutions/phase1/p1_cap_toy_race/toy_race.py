"""Phase 1 capstone: build a toy pit-stop race environment, one complication at a time.

The brief is page 05 of the Phase 1 set ("Building the Environment, Step by Step"). This
file is the same journey with the numbers pinned down so that each stage can be checked.

    python -m labs check p1-cap 1      check one stage
    python -m labs check p1-cap        check everything
    python -m labs hint  p1-cap        if you are stuck

Work through the stages in order. Each TODO says exactly what to compute; the constants it
needs are defined just below. Names here are deliberately not the real project's names.

THE TOY WORLD
-------------
* A race of HORIZON = 20 laps. One decision per lap: STAY_OUT, PIT_A or PIT_B.
* Two compounds. A is fast and fragile, B is slow and durable.
* Weather is DRY or WET for the whole race. A safety car may appear on some laps.
* reward = -lap_time, every lap.
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces

STAY_OUT, PIT_A, PIT_B = 0, 1, 2
DRY, WET = 0, 1

HORIZON = 20
BASE_LAP = 10.0  # seconds: a lap on a fresh, warm compound A with no fuel, in the dry
PIT_LOSS = 4.0  # seconds added to the lap on which you pit, under green flag

COMPOUNDS = {
    "A": {"pace": 0.0, "wear_rate": 0.05, "cliff_age": 6, "cliff_severity": 0.15, "cliff_cap": 4.0},
    "B": {"pace": 0.6, "wear_rate": 0.02, "cliff_age": 11, "cliff_severity": 0.08, "cliff_cap": 4.0},
}

FUEL_PER_LAP = 0.03  # seconds of penalty per lap of fuel still on board

WEATHER_PENALTY = {
    DRY: {"A": 0.0, "B": 0.0},
    WET: {"A": 6.0, "B": 5.5},
}

WARMUP_OUT_LAP = 1.2  # seconds, on a tyre's first lap (age 1)
WARMUP_SECOND_LAP = 0.5  # seconds, on its second lap (age 2)

SC_HAZARD = 0.06  # chance that a safety car starts on any given green lap
SC_CONTINUE = 2 / 3  # chance that a running safety car is still out on the next lap
SC_LAP_TIME = 14.0  # every lap behind the safety car takes exactly this long
SC_PIT_DISCOUNT = 0.4  # a pit stop under the safety car costs this fraction of PIT_LOSS


# ============================================================================ Stage 2


def toy_pace(compound: str) -> float:
    """Fixed pace penalty of a compound, in seconds per lap (from COMPOUNDS)."""
    # >>> SOLUTION: look the compound's "pace" up in COMPOUNDS
    return COMPOUNDS[compound]["pace"]
    # <<< SOLUTION


def apply_action(compound: str, age: int, action: int) -> tuple[str, int]:
    """Tyre bookkeeping at the END of a lap: the (compound, age) the NEXT lap is driven on.

    STAY_OUT keeps the compound and makes it one lap older. PIT_A / PIT_B fits that compound
    brand new, so the next lap is its first: age 1.
    """
    # >>> SOLUTION: return (compound, age + 1) for STAY_OUT, ("A", 1) for PIT_A, ("B", 1) for PIT_B
    if action == PIT_A:
        return "A", 1
    if action == PIT_B:
        return "B", 1
    return compound, age + 1
    # <<< SOLUTION


# ============================================================================ Stage 3


def toy_wear(compound: str, age: int) -> float:
    """Seconds lost to tyre wear on a lap driven at this tyre age.

    Two pieces added together, using the compound's entry in COMPOUNDS:
      linear = wear_rate * age
      cliff  = cliff_severity * (laps beyond cliff_age) ** 2, never more than cliff_cap
               (zero while age <= cliff_age)
    """
    # >>> SOLUTION: linear part plus a squared-and-capped penalty for every lap of age beyond cliff_age
    c = COMPOUNDS[compound]
    linear = c["wear_rate"] * age
    over = max(0, age - c["cliff_age"])
    cliff = min(c["cliff_severity"] * over**2, c["cliff_cap"])
    return linear + cliff
    # <<< SOLUTION


# ============================================================================ Stage 4


def toy_fuel_penalty(laps_left: int) -> float:
    """Seconds lost to carrying fuel: FUEL_PER_LAP for each lap still to run AFTER this one."""
    # >>> SOLUTION: FUEL_PER_LAP times laps_left
    return FUEL_PER_LAP * laps_left
    # <<< SOLUTION


# ============================================================================ Stage 5


def toy_weather_penalty(weather: int, compound: str) -> float:
    """Seconds lost for running this compound in this weather (from WEATHER_PENALTY)."""
    # >>> SOLUTION: look it up in WEATHER_PENALTY
    return WEATHER_PENALTY[weather][compound]
    # <<< SOLUTION


# ============================================================================ Stage 6


def toy_warmup(age: int) -> float:
    """Cold-tyre penalty: WARMUP_OUT_LAP at age 1, WARMUP_SECOND_LAP at age 2, nothing after."""
    # >>> SOLUTION: return the right constant for age 1, age 2, and 0.0 otherwise
    if age <= 1:
        return WARMUP_OUT_LAP
    if age == 2:
        return WARMUP_SECOND_LAP
    return 0.0
    # <<< SOLUTION


# ============================================================================ Stage 7


def sample_sc_trace(horizon: int, rng: np.random.Generator) -> np.ndarray:
    """A fresh safety-car trace: a boolean array of length `horizon`, True where the SC is out.

    Walk through the laps in order, drawing ONE `rng.random()` per lap:
      * if the previous lap was green (or this is the first lap): the SC starts on this lap
        when the draw is below SC_HAZARD;
      * if the previous lap was under the SC: it is still out on this lap when the draw is
        below SC_CONTINUE.
    """
    # >>> SOLUTION: loop over laps keeping track of whether the previous lap was under SC; compare one draw per lap with SC_HAZARD or SC_CONTINUE
    trace = np.zeros(horizon, dtype=bool)
    active = False
    for lap in range(horizon):
        threshold = SC_CONTINUE if active else SC_HAZARD
        active = bool(rng.random() < threshold)
        trace[lap] = active
    return trace
    # <<< SOLUTION


# ============================================================================ Stage 8


def toy_action_mask(compound: str, weather: int, laps_left: int, compounds_used: set) -> np.ndarray:
    """Which of [STAY_OUT, PIT_A, PIT_B] are legal. Start from all True, then apply in order:

      1. You cannot pit for the compound you are already on.
      2. In the WET, compound B is unsafe: PIT_B is illegal.
      3. In the DRY, both compounds must be used during the race. If that has not happened
         yet and laps_left <= 1, STAY_OUT is illegal (you are out of time to comply).
         In the WET this rule does not apply.
      4. Safety net: if nothing is legal after rules 1-3, STAY_OUT becomes legal.
    """
    # >>> SOLUTION: build a boolean array of three Trues and switch entries off rule by rule, then apply the safety net
    mask = np.array([True, True, True])
    mask[PIT_A if compound == "A" else PIT_B] = False
    if weather == WET:
        mask[PIT_B] = False
    if weather == DRY and len(compounds_used) < 2 and laps_left <= 1:
        mask[STAY_OUT] = False
    if not mask.any():
        mask[STAY_OUT] = True
    return mask
    # <<< SOLUTION


# ============================================================================ The environment (stages 1, 6, 7, 8)


class ToyRaceEnv(gym.Env):
    """Observation, 9 numbers, all in [0, 1], dtype float32, in this order:

        0  tyre age / HORIZON (capped at 1)
        1  1 if compound A is fitted, else 0
        2  1 if compound B is fitted, else 0
        3  1 if DRY, else 0
        4  1 if WET, else 0
        5  laps left after this one / HORIZON
        6  1 if the safety car is out on the lap about to be driven, else 0
        7  1 if compound A has been used at any point, else 0
        8  1 if compound B has been used at any point, else 0
    """

    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        # >>> SOLUTION: Stage 1 - declare self.observation_space (Box, 9 numbers in [0, 1], float32) and self.action_space (3 actions)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(9,), dtype=np.float32)
        self.action_space = spaces.Discrete(3)
        # <<< SOLUTION
        self._lap = 1
        self._compound = "A"
        self._age = 1
        self._weather = DRY
        self._used = {"A"}
        self._sc_trace = np.zeros(HORIZON, dtype=bool)

    # -- given: you do not need to change reset() ------------------------------------------
    def reset(self, seed=None, options=None):
        """Start a race on a new compound A (age 1). Weather and safety cars are sampled fresh.

        options may pin things down for testing: {"weather": DRY, "sc_trace": [...], "compound": "B"}.
        """
        super().reset(seed=seed)
        options = options or {}
        self._lap = 1
        self._compound = options.get("compound", "A")
        self._age = 1
        self._used = {self._compound}
        self._weather = options["weather"] if "weather" in options else int(self.np_random.integers(0, 2))
        if "sc_trace" in options:
            self._sc_trace = np.asarray(options["sc_trace"], dtype=bool)
        else:
            try:
                self._sc_trace = sample_sc_trace(HORIZON, self.np_random)
            except NotImplementedError:  # stage 7 not written yet: race under green
                self._sc_trace = np.zeros(HORIZON, dtype=bool)
        return self._get_obs(), {}

    def _laps_left(self) -> int:
        """Laps still to run after the one about to be driven."""
        return HORIZON - self._lap

    def _sc_now(self) -> bool:
        """Is the safety car out on the lap about to be driven? (False once the race is over.)"""
        return bool(self._lap <= HORIZON and self._sc_trace[self._lap - 1])

    # ---------------------------------------------------------------------------------------

    def _get_obs(self):
        # >>> SOLUTION: Stage 1 - build the 9-number float32 observation described in the class docstring (use self._laps_left() and self._sc_now())
        return np.array(
            [
                min(self._age / HORIZON, 1.0),
                1.0 if self._compound == "A" else 0.0,
                1.0 if self._compound == "B" else 0.0,
                1.0 if self._weather == DRY else 0.0,
                1.0 if self._weather == WET else 0.0,
                max(self._laps_left(), 0) / HORIZON,
                1.0 if self._sc_now() else 0.0,
                1.0 if "A" in self._used else 0.0,
                1.0 if "B" in self._used else 0.0,
            ],
            dtype=np.float32,
        )
        # <<< SOLUTION

    def action_masks(self):
        # >>> SOLUTION: Stage 8 - return toy_action_mask(...) for the current state
        return toy_action_mask(self._compound, self._weather, self._laps_left(), self._used)
        # <<< SOLUTION

    def step(self, action):
        """Drive one lap, then apply the action. Returns (obs, reward, terminated, truncated, info).

        TIMING HALF, on the tyre the lap is actually driven on (the OLD tyre, before any pit):
          * Stage 6, green-flag lap:
                lap_time = BASE_LAP + toy_pace + toy_wear + toy_fuel_penalty(self._laps_left())
                           + toy_weather_penalty + toy_warmup
                and PIT_LOSS is added if the action is a pit.
          * Stage 7, safety-car lap (self._sc_now() is True):
                lap_time = SC_LAP_TIME, nothing else applies,
                and PIT_LOSS * SC_PIT_DISCOUNT is added if the action is a pit.

        BOOKKEEPING HALF, strictly after the lap time is known:
          * remember which compound and age the lap was driven on (for info);
          * self._compound, self._age = apply_action(...); add the fitted compound to self._used;
          * self._lap += 1.

        reward = -lap_time. terminated when self._lap > HORIZON. truncated is always False.
        info = {"lap_time": ..., "pit": True/False,
                "lap_time_compound": the compound the lap was driven on,
                "lap_time_age": the tyre age the lap was driven on,
                "compound": the compound fitted for the next lap, "age": its age}
        """
        assert self.action_space.contains(action)
        # >>> SOLUTION: Stage 6 (and the safety-car branch in Stage 7) - timing half on the old tyre, then bookkeeping, then return the five values
        pitting = action != STAY_OUT
        driven_compound, driven_age = self._compound, self._age
        if self._sc_now():
            lap_time = SC_LAP_TIME
            if pitting:
                lap_time += PIT_LOSS * SC_PIT_DISCOUNT
        else:
            lap_time = (
                BASE_LAP
                + toy_pace(self._compound)
                + toy_wear(self._compound, self._age)
                + toy_fuel_penalty(self._laps_left())
                + toy_weather_penalty(self._weather, self._compound)
                + toy_warmup(self._age)
            )
            if pitting:
                lap_time += PIT_LOSS

        self._compound, self._age = apply_action(self._compound, self._age, action)
        self._used.add(self._compound)
        self._lap += 1

        info = {
            "lap_time": lap_time,
            "pit": pitting,
            "lap_time_compound": driven_compound,
            "lap_time_age": driven_age,
            "compound": self._compound,
            "age": self._age,
        }
        return self._get_obs(), -lap_time, self._lap > HORIZON, False, info
        # <<< SOLUTION


# ============================================================================ Stage 9


class RewardCentringWrapper(gym.Wrapper):
    """Adds a fixed `offset` to every step's reward, leaving the environment itself untouched.

    The true, uncentred reward must stay available as info["true_reward"].
    """

    def __init__(self, env, offset: float):
        super().__init__(env)
        self.offset = offset

    def step(self, action):
        # >>> SOLUTION: step the wrapped env, store the true reward in info["true_reward"], return the reward plus self.offset
        obs, reward, terminated, truncated, info = self.env.step(action)
        info["true_reward"] = reward
        return obs, reward + self.offset, terminated, truncated, info
        # <<< SOLUTION
