"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def advance(distribution, matrix):
    return [sum(distribution[j]*matrix[i][j] for j in range(len(matrix))) for i in range(len(matrix))]

def sample_next(state, rng, matrix):
    return max(range(len(matrix)),key=lambda j:matrix[state][j])

def decision_values(state, matrix):
    return dict(NONE=1,UMBRELLA=1)

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
