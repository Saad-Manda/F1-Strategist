"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def update(q, reward, next_values, legal, alpha, gamma, terminated, truncated=False):
    import math
    validate_distribution([alpha,1-alpha]); validate_distribution([gamma,1-gamma])
    if not math.isfinite(q) or not math.isfinite(reward): raise ValueError("finite q/reward required")
    continuation=0 if terminated else max(next_values[i] for i in legal_indices(next_values,legal))
    target=reward+gamma*continuation
    error=target-q
    return dict(target=target,error=error,value=q+alpha*error)

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
