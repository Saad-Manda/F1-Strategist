"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def expected_value(outcomes):
    import math
    if not outcomes:
        raise ValueError("outcomes must not be empty")
    validate_distribution([p for p,r in outcomes])
    if any(not math.isfinite(r) for p,r in outcomes):
        raise ValueError("rewards must be finite")
    return sum(p*r for p,r in outcomes)

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
