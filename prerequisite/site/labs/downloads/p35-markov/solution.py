"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def advance(distribution, matrix):
    validate_matrix(matrix)
    validate_distribution(distribution)
    if len(distribution)!=len(matrix):
        raise ValueError("distribution dimension mismatch")
    return [sum(p*matrix[i][j] for i,p in enumerate(distribution)) for j in range(len(matrix))]

def sample_next(state, rng, matrix):
    validate_matrix(matrix)
    if type(state) is not int or not 0 <= state < len(matrix):
        raise ValueError("invalid state")
    draw=rng.random()
    if not 0 <= draw < 1:
        raise ValueError("random() must return a value in [0,1)")
    cumulative=0.0
    for next_state,probability in enumerate(matrix[state]):
        cumulative+=probability
        if draw<cumulative:
            return next_state
    return len(matrix)-1  # Floating-point roundoff only.

def decision_values(state, matrix):
    validate_matrix(matrix)
    if len(matrix)!=2 or type(state) is not int or state not in (0,1):
        raise ValueError("prediction task needs two states")
    return dict(NONE=matrix[state][0],UMBRELLA=matrix[state][1])

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
