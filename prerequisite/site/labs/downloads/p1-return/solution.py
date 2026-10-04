"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def returns(rewards, gamma):
    import math
    if not math.isfinite(gamma) or not 0 <= gamma <= 1:
        raise ValueError("gamma must be finite and in [0,1]")
    if any(not math.isfinite(r) for r in rewards):
        raise ValueError("rewards must be finite")
    result, tail = [], 0.0
    for reward in reversed(rewards):
        tail = reward + gamma * tail
        result.append(tail)
    return list(reversed(result))

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
