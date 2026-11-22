"""Lab p1-04, task 1: implement a Gymnasium environment from a written spec.

THE SPEC — CorridorEnv
----------------------
A corridor of N_CELLS = 8 cells in a row, numbered 0..7. The agent starts in cell 0 and has
to reach cell 7.

    [A][ ][ ][ ][ ][ ][ ][G]
     0  1  2  3  4  5  6  7

* Actions: Discrete(2). LEFT = 0 moves one cell toward 0, RIGHT = 1 moves one cell toward 7.
* Observation: a Box of shape (1,), dtype float32, in [0, 1]: the position divided by 7.
* Reward: -1.0 on every step.
* The episode TERMINATES when the agent is in cell 7 (the task is finished).
* The episode is TRUNCATED after MAX_STEPS = 30 steps if the goal has not been reached
  (an outside limit cut it off). The two flags are never both True.
* Cell 0 has a wall on its left. LEFT is not a legal move there:
    - action_masks() returns a boolean array [LEFT legal?, RIGHT legal?];
    - if LEFT is taken in cell 0 anyway, the agent stays in cell 0 (and the step still
      costs -1 and still counts toward MAX_STEPS).
* reset(seed=...) must call super().reset(seed=seed) and return (observation, info).

Run the checks with:  python -m labs check p1-04
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces

LEFT, RIGHT = 0, 1
N_CELLS = 8
MAX_STEPS = 30


class CorridorEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        # >>> SOLUTION: declare self.observation_space (Box) and self.action_space (Discrete) exactly as the spec says
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        # <<< SOLUTION
        self._pos = 0
        self._steps = 0

    def _get_obs(self):
        # >>> SOLUTION: build the observation from self._pos, with the declared shape and dtype
        return np.array([self._pos / (N_CELLS - 1)], dtype=np.float32)
        # <<< SOLUTION

    def reset(self, seed=None, options=None):
        # >>> SOLUTION: seed the base class, put the agent back at the start, zero the step counter, return (obs, info)
        super().reset(seed=seed)
        self._pos = 0
        self._steps = 0
        return self._get_obs(), {}
        # <<< SOLUTION

    def action_masks(self):
        # >>> SOLUTION: a boolean array of length 2 saying which actions are legal in the current cell
        return np.array([self._pos > 0, True], dtype=bool)
        # <<< SOLUTION

    def step(self, action):
        assert self.action_space.contains(action)
        # >>> SOLUTION: move (clamped at the wall), count the step, then work out reward, terminated and truncated and return the five values
        if action == LEFT:
            self._pos = max(0, self._pos - 1)
        else:
            self._pos = min(N_CELLS - 1, self._pos + 1)
        self._steps += 1
        terminated = self._pos == N_CELLS - 1
        truncated = self._steps >= MAX_STEPS and not terminated
        return self._get_obs(), -1.0, terminated, truncated, {}
        # <<< SOLUTION
