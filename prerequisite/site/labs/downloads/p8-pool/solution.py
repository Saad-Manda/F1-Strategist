"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def snapshot(policy):
    validate_policy(policy)
    result=np.array(policy,dtype=float,copy=True);result.setflags(write=False)
    return result
def add_snapshot(pool, policy, capacity):
    if type(capacity) is not int or capacity<1:raise ValueError("positive capacity required")
    return [*pool,snapshot(policy)][-capacity:]
def pool_probabilities(weights):
    w=np.asarray(weights,dtype=float)
    if w.ndim!=1 or not len(w) or not np.isfinite(w).all() or (w<=0).any():raise ValueError("positive finite weights required")
    scaled=w/w.max()
    return scaled/scaled.sum()
def sample_indices(weights, count, seed):
    if type(count) is not int or count<1:raise ValueError("positive sample count required")
    p=pool_probabilities(weights)
    return np.random.default_rng(seed).choice(len(p),size=count,p=p)
def coverage(policy):
    validate_policy(policy)
    return [sum(policy[i]*MATRIX[i][j] for i in range(3)) for j in range(3)]

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
