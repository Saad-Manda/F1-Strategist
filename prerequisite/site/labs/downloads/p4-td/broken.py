"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def update(q, reward, next_values, legal, alpha, gamma, terminated, truncated=False):
    continuation=0 if terminated or truncated else max(next_values)
    target=reward+gamma*continuation
    return dict(target=target,error=target-q,value=q+alpha*(target-q))

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
