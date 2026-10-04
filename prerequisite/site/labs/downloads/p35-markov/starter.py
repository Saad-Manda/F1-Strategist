"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def advance(distribution, matrix):
    # TODO: implement the contract described in README.md.
    raise NotImplementedError("Complete advance")

def sample_next(state, rng, matrix):
    # TODO: implement the contract described in README.md.
    raise NotImplementedError("Complete sample_next")

def decision_values(state, matrix):
    # TODO: implement the contract described in README.md.
    raise NotImplementedError("Complete decision_values")

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
