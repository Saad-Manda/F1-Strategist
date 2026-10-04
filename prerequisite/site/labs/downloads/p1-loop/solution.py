"""Optional reference solution. Open only when you want the explained answer."""
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
        self.position = 0
        self.steps = 0
        self.finished = False
        return self.position, {"steps": self.steps}

    def step(self, action):
        if self.position is None or self.finished:
            raise RuntimeError("Reset before stepping a new or finished episode.")
        if not self.action_space.contains(action):
            raise ValueError("Action must be LEFT=0 or RIGHT=1.")
        self.position = max(0, min(2, self.position + (1 if action == 1 else -1)))
        self.steps += 1
        self.finished = self.position == 2
        reward = 5.0 if self.finished else -1.0
        return self.position, reward, self.finished, False, {"steps": self.steps}


def collect_episode(env, policy, *, seed=None):
    observation, info = env.reset(seed=seed)
    trace = []
    while True:
        before = observation
        action = policy(observation)
        observation, reward, terminated, truncated, info = env.step(action)
        trace.append(dict(before=before, action=action, observation=observation,
                          reward=float(reward), terminated=bool(terminated),
                          truncated=bool(truncated), info=info))
        if terminated or truncated:
            break
    return trace


if __name__ == "__main__":
    run_demo(ChainEnv, collect_episode)
