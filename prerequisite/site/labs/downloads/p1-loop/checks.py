"""Independent behaviour checks; never imports the reference solution as oracle."""
import argparse
import importlib.util
from pathlib import Path
import sys

import gymnasium as gym


def load_candidate(path):
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("lab_candidate", path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def check_environment(candidate):
    env = candidate.ChainEnv()
    try:
        observation, info = env.reset(seed=7)
        require(observation == 0 and isinstance(info, dict), "reset must return observation 0 and an info dict")
        first_info = info
        for action, expected in [(0, (0, -1, False)), (1, (1, -1, False)), (1, (2, 5, True))]:
            result = env.step(action)
            require(len(result) == 5, f"step returned {len(result)} values; expected 5")
            obs, reward, terminated, truncated, info = result
            require((obs, reward, terminated) == expected, f"action {action}: expected {expected}, got {(obs, reward, terminated)}")
            require(env.observation_space.contains(obs), "observation must be inside its declared space")
            require(truncated is False and isinstance(info, dict), "base environment must not add a collection cap")
        try:
            env.step(1)
        except (RuntimeError, ValueError):
            pass
        else:
            raise AssertionError("stepping after true termination must fail clearly")
        observation, info = env.reset(seed=7)
        require(observation == 0 and info is not first_info and info.get('steps') == 0, "reset must return fresh state/info with steps=0")
        try:
            env.step(8)
        except (RuntimeError, ValueError, AssertionError):
            pass
        else:
            raise AssertionError("action 8 must be rejected")
    finally:
        env.close()


class BoundaryProbe(gym.Wrapper):
    """Stop a wrong collector immediately instead of letting its loop hang."""
    def __init__(self, env):
        super().__init__(env)
        self.ended = False

    def reset(self, **kwargs):
        self.ended = False
        return self.env.reset(**kwargs)

    def step(self, action):
        require(not self.ended, "collector stepped again after an episode boundary")
        result = self.env.step(action)
        self.ended = result[2] or result[3]
        return result


def check_collector(candidate):
    for limit, expected in [(6, [(0, 1, -1, False, False), (1, 2, 5, True, False)]),
                            (1, [(0, 1, -1, False, True)])]:
        env = BoundaryProbe(gym.wrappers.TimeLimit(candidate.ChainEnv(), max_episode_steps=limit))
        try:
            trace = candidate.collect_episode(env, lambda observation: 1, seed=7)
            actual = [(r['before'], r['observation'], r['reward'], r['terminated'], r['truncated']) for r in trace]
            require(actual == expected, f"limit {limit}: expected trace {expected}, got {actual}")
            require(all(r['action'] == 1 and isinstance(r['info'], dict) for r in trace), "trace must retain action and info")
            require(sum(r['reward'] for r in trace) == (4 if limit == 6 else -1), "episode total disagrees with its rewards")
        finally:
            env.close()


def run_checks(candidate):
    failures = []
    for name, check in [("Environment contract", check_environment), ("Episode collection", check_collector)]:
        try:
            check(candidate)
            print(f"PASS: {name}")
        except Exception as error:
            failures.append(name)
            print(f"FAIL: {name}: {type(error).__name__}: {error}")
    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default="starter.py")
    args = parser.parse_args()
    raise SystemExit(bool(run_checks(load_candidate(args.candidate))))
