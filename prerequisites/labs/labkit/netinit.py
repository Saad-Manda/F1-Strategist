"""An untrained copy of the Phase 5 plan's dueling network, for lab p8-05.

Given code. `DuelingDQN` has the architecture of `phase-5-dueling-double-dqn.md` exactly:
a 2-layer trunk of 128 units, a value stream and an advantage stream of 64 units each, and
Q = V + (A - mean A). Nothing here is ever trained.
"""

from __future__ import annotations

import numpy as np
import torch
from torch import nn

OBS_DIM = 19  # 16 single-car features + 3 multi-car features (Phase 6)
N_ACTIONS = 6  # the plan's N_ACTIONS


class DuelingDQN(nn.Module):
    def __init__(self, obs_dim: int = OBS_DIM, n_actions: int = N_ACTIONS, hidden: int = 128):
        super().__init__()
        self.trunk = nn.Sequential(nn.Linear(obs_dim, hidden), nn.ReLU(), nn.Linear(hidden, hidden), nn.ReLU())
        self.value = nn.Sequential(nn.Linear(hidden, 64), nn.ReLU(), nn.Linear(64, 1))
        self.advantage = nn.Sequential(nn.Linear(hidden, 64), nn.ReLU(), nn.Linear(64, n_actions))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        f = self.trunk(x)
        a = self.advantage(f)
        return self.value(f) + a - a.mean(dim=-1, keepdim=True)


def untrained(seed: int) -> DuelingDQN:
    """A freshly initialised network: PyTorch's default initialisation, seeded."""
    torch.manual_seed(seed)
    return DuelingDQN()


def greedy_actions(net: DuelingDQN, obs: np.ndarray) -> np.ndarray:
    """argmax_a Q(obs, a) for every row of obs, as the plan's opponents act (epsilon = 0)."""
    with torch.no_grad():
        return net(torch.as_tensor(obs, dtype=torch.float32)).argmax(dim=1).numpy()


def random_observations(n: int = 2000, seed: int = 0) -> np.ndarray:
    """n observations with every feature uniform in [0, 1], the observation space's range."""
    return np.random.default_rng(seed).uniform(0.0, 1.0, (n, OBS_DIM)).astype(np.float32)


def race_trajectory(n_laps: int = 52, seed: int = 0) -> np.ndarray:
    """The observations of one race: lap fraction (feature 0) and tyre age (feature 1) rise from 0 to 1,
    every other feature is held at a value drawn once per race."""
    obs = np.tile(np.random.default_rng(seed).uniform(0.0, 1.0, OBS_DIM), (n_laps, 1)).astype(np.float32)
    obs[:, 0] = np.linspace(0.0, 1.0, n_laps)
    obs[:, 1] = np.linspace(0.0, 1.0, n_laps)
    return obs
