"""The toy race as a masked Gymnasium environment, for the Stable-Baselines3 labs. Given code.

The race is `labkit.toyrace.RaceModel` with the safety car off and dry weather throughout (the
"quiet" race of the p4-cap and p5-cap learning checks). The observation is the five numbers the
p5-cap network learner used:

    [laps left including this one / horizon,  tyre age / horizon,  compound,  used both,  safety car]

The reward of a lap is -(lap time - offset). With the default offset of 10 s (a typical lap) the
reward is centred near zero; with offset=0 it is the raw -lap time. `info["lap_time"]` always
holds the true lap time.

`action_masks()` returns a bool array of the legal actions on the current lap, which is what
sb3-contrib's MaskablePPO looks for.

Labs import this; nothing in this file is a TODO.
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from . import toyrace as tr

QUIET = tr.RaceModel(sc_hazard=0.0)


def encode(lap: int, compound: int, age: int, used_both: bool, horizon: int = tr.HORIZON) -> np.ndarray:
    return np.array([(horizon - lap + 1) / horizon, min(age, horizon) / horizon, float(compound), float(used_both), 0.0], dtype=np.float32)


def legal_mask(model: tr.RaceModel, lap: int, compound: int, used_both: bool) -> np.ndarray:
    mask = np.zeros(3, dtype=bool)
    if lap > model.horizon:
        mask[tr.STAY_OUT] = True
    else:
        mask[model.legal_actions(lap, compound, tr.DRY, used_both)] = True
    return mask


class TinyRaceEnv(gym.Env):
    """One quiet toy race per episode: `horizon` steps, one per lap, always the same length."""

    metadata = {"render_modes": []}

    def __init__(self, offset: float = tr.BASE_LAP, model: tr.RaceModel | None = None):
        self.model = model or QUIET
        self.offset = float(offset)
        self.observation_space = spaces.Box(0.0, 1.0, (5,), np.float32)
        self.action_space = spaces.Discrete(3)
        self.lap, self.compound, self.age, self.used_both = 1, tr.A, 1, False

    def _obs(self) -> np.ndarray:
        return encode(min(self.lap, self.model.horizon + 1), self.compound, self.age, self.used_both, self.model.horizon)

    def reset(self, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self.lap, self.compound, self.age, self.used_both = 1, tr.A, 1, False
        return self._obs(), {}

    def action_masks(self) -> np.ndarray:
        return legal_mask(self.model, self.lap, self.compound, self.used_both)

    def step(self, action):
        action = int(action)
        if not self.action_masks()[action]:  # an unmasked learner gets the first legal action instead
            action = int(np.flatnonzero(self.action_masks())[0])
        lap_time = self.model.cost(self.lap, self.compound, self.age, action, tr.DRY, 0)
        new_compound, self.age = self.model.next_tyre(self.compound, self.age, action)
        self.used_both = self.used_both or new_compound != self.compound
        self.compound = new_compound
        self.lap += 1
        done = self.lap > self.model.horizon
        return self._obs(), -(lap_time - self.offset), done, False, {"lap_time": lap_time, "action": action}


def optimum(model: tr.RaceModel | None = None) -> float:
    """The exact optimal expected race time of the quiet race (224.49 s by default)."""
    model = model or QUIET
    V, _ = tr.solve(model)
    return V[(1, tr.A, 1, 0, False, tr.DRY)]


def gap_of_sb3(sb3_model, model: tr.RaceModel | None = None) -> float:
    """Exact gap to the optimum of a trained SB3 model's deterministic policy, in seconds.

    Asks the model for its action in every state (no races are simulated), then evaluates that
    policy exactly with `toyrace.expected_time`.
    """
    model = model or QUIET

    def policy(lap, compound, age, sc, used_both, weather):
        obs = encode(lap, compound, age, used_both, model.horizon)
        action, _ = sb3_model.predict(obs, action_masks=legal_mask(model, lap, compound, used_both), deterministic=True)
        return int(action)

    return tr.expected_time(model, policy) - optimum(model)
