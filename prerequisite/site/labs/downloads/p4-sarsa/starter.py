"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def act(memory, state, values, legal, epsilon, rng):
    # TODO: implement the contract described in README.md.
    raise NotImplementedError("Complete act")

def target(memory, reward, next_state, values, legal, gamma, terminated, truncated, epsilon, rng):
    # TODO: implement the contract described in README.md.
    raise NotImplementedError("Complete target")

def reset(memory):
    # TODO: implement the contract described in README.md.
    raise NotImplementedError("Complete reset")

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
