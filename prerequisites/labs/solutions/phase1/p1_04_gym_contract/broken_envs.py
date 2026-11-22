"""Lab p1-04, task 2: three environments, each breaking the Gymnasium contract in ONE way.

Do not fix these. Find out what is wrong with each and record it in diagnosis.py.

Suggested tools: stable_baselines3's check_env (it raises, or warns, naming the offending
value), and stepping an environment by hand while printing what step() returns.

    from stable_baselines3.common.env_checker import check_env
    from broken_envs import EnvOne
    check_env(EnvOne())
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces

LEFT, RIGHT = 0, 1
N_CELLS = 8
MAX_STEPS = 30


class _Base(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self._pos, self._steps = 0, 0

    def _get_obs(self):
        return np.array([self._pos / (N_CELLS - 1)], dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._pos, self._steps = 0, 0
        return self._get_obs(), {}

    def _move(self, action):
        self._pos = max(0, self._pos - 1) if action == LEFT else min(N_CELLS - 1, self._pos + 1)
        self._steps += 1

    def step(self, action):
        self._move(action)
        terminated = self._pos == N_CELLS - 1
        truncated = self._steps >= MAX_STEPS and not terminated
        return self._get_obs(), -1.0, terminated, truncated, {}


class EnvOne(_Base):
    def step(self, action):
        self._move(action)
        at_goal = self._pos == N_CELLS - 1
        terminated = at_goal or self._steps >= MAX_STEPS
        return self._get_obs(), -1.0, terminated, False, {}


class EnvTwo(_Base):
    def _get_obs(self):
        return np.array([self._pos / (N_CELLS - 1)])


class EnvThree(_Base):
    def _get_obs(self):
        return np.array([self._pos / (N_CELLS - 2)], dtype=np.float32)
