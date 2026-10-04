"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def returns(rewards, gamma):
    return [gamma * sum(rewards[t:]) for t in range(len(rewards))]

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
