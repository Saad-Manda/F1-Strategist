"""Checks for lab p1-01. Given code: read it if you like, but there is nothing to edit here."""

from labs.labkit import envs
from labs.labkit.checks import passed, require, todo
from labs.labkit.envs import DOWN, LEFT, RIGHT

LAB = "p1-01"


def part_a(ended_signal, hole_reward):
    if ended_signal is None or hole_reward is None:
        raise todo(LAB, "answer both Part A questions")
    require(
        ended_signal == "terminated",
        "Look again at the second step's printout. Only one of the five values changed in a way that says "
        "'this episode is finished because of something in the task itself'.",
    )
    require(float(hole_reward) == 0.0, "Read the reward printed for the step that entered the hole.")
    passed(LAB, "A", "Part A: `terminated` ended the episode, and the hole paid 0, the same as any other step.")


class _SpyEnv:
    """Wraps an env and remembers how reset() was called."""

    def __init__(self, env):
        self.env, self.reset_seeds = env, []

    def reset(self, seed=None, options=None):
        self.reset_seeds.append(seed)
        return self.env.reset(seed=seed, options=options)

    def step(self, action):
        return self.env.step(action)


def part_b(run_episode):
    lake = envs.make_frozen_lake(slippery=False)

    safe_path = {0: DOWN, 4: DOWN, 8: RIGHT, 9: DOWN, 13: RIGHT, 14: RIGHT}
    result = run_episode(lake, lambda obs: safe_path[obs], seed=0)
    require(isinstance(result, tuple) and len(result) == 2, "run_episode should return a pair: (total_reward, steps).")
    total, steps = result
    require(total == 1.0, f"Following the safe path should collect a total reward of 1.0, but got {total}.")
    require(steps == 6, f"The safe path is 6 steps long, but run_episode reported {steps}.")

    total, steps = run_episode(lake, lambda obs: RIGHT if obs == 0 else DOWN, seed=0)
    require(steps == 2 and total == 0.0, "An episode that falls in a hole on its second step should stop there, with total reward 0.")

    total, steps = run_episode(lake, lambda obs: LEFT, seed=0)
    require(
        steps == 100,
        f"A policy that walks into the wall forever is cut off by the time limit after 100 steps, but your loop ran {steps}. "
        "There are two ways an episode can end; the loop has to stop on both.",
    )

    spy = _SpyEnv(lake)
    run_episode(spy, lambda obs: safe_path[obs], seed=123)
    require(spy.reset_seeds == [123], "run_episode should call env.reset exactly once, passing the seed it was given.")
    passed(LAB, "B", "Part B: your loop returns the right total and stops on both termination and truncation.")


def part_c(replayed, fresh):
    require(replayed > 0.95, "With the same seed every time, the memorised sequence should win essentially always. Check that run_episode passes `seed` to reset().")
    require(fresh < 0.5, "With fresh seeds the memorised sequence should win far less often.")
    passed(LAB, "C", "Part C: perfect on replayed randomness, poor on fresh randomness.")
