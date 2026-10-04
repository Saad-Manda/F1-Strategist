"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def backup(action_values, policy, legal):
    return max(action_values), max(action_values)

def branch_values(gamma, via_probability):
    return backup([3, 1+gamma*4, 99], [1-via_probability, via_probability, 0], [True,True,False])

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
