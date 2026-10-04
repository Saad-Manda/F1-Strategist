"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def snapshot(policy):return np.asarray(policy)
def add_snapshot(pool, policy, capacity):
    pool.append(snapshot(policy));return pool
def pool_probabilities(weights):return np.asarray(weights,dtype=float)/sum(weights)
def sample_indices(weights, count, seed):return np.zeros(count,dtype=int)
def coverage(policy):return [sum(policy[i]*MATRIX[i][j] for i in range(3)) for j in range(3)]

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
