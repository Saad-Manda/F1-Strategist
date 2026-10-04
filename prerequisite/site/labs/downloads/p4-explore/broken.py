"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def probabilities(values, legal, epsilon):
    chosen=max(legal_indices(values,legal),key=lambda i:values[i])
    return [int(i==chosen) for i in range(len(values))]

def select_action(values, legal, epsilon, rng):
    return max(legal_indices(values,legal),key=lambda i:values[i])

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
