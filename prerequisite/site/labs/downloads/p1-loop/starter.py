"""Complete three TODOs. LEFT=0, RIGHT=1; initial position 0, goal 2.

Reward is -1 except arrival at 2 gives +5. Positions cannot go below 0.
reset returns (observation, info); step returns five Gymnasium values.
collect_episode returns one dict per executed transition, with keys:
before, action, observation, reward, terminated, truncated, info.
"""
import gymnasium as gym

from exercise_common import run_demo


class ChainEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self):
        self.observation_space = gym.spaces.Discrete(3)
        self.action_space = gym.spaces.Discrete(2)
        self.position = None
        self.steps = 0
        self.finished = False

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        # TODO 1: start a fresh episode and return observation plus fresh info.
        raise NotImplementedError("Implement ChainEnv.reset")

    def step(self, action):
        # TODO 2: validate episode/action, apply transition, and return all five values.
        # Info uses {'steps': number_of_executed_steps}.
        raise NotImplementedError("Implement ChainEnv.step")


def collect_episode(env, policy, *, seed=None):
    # TODO 3: reset, choose actions from observations, and collect transition dicts.
    # Stop collection at either kind of episode boundary.
    raise NotImplementedError("Implement collect_episode")


if __name__ == "__main__":
    run_demo(ChainEnv, collect_episode)
