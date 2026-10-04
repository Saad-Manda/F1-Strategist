"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def backup(action_values, policy, legal):
    import math
    if not (len(action_values) == len(policy) == len(legal)) or not any(legal):
        raise ValueError("matching arrays and at least one legal action required")
    if any(not math.isfinite(q) for q in action_values):
        raise ValueError("values must be finite")
    validate_distribution(policy)
    if any(p != 0 for p, allowed in zip(policy, legal) if not allowed):
        raise ValueError("policy has mass on illegal actions")
    return (sum(p*q for p,q,allowed in zip(policy,action_values,legal) if allowed),
            max(q for q,allowed in zip(action_values,legal) if allowed))

def branch_values(gamma, via_probability):
    validate_distribution([via_probability, 1-via_probability])
    validate_distribution([gamma, 1-gamma])
    return backup([3, 1+gamma*4, 99], [1-via_probability, via_probability, 0], [True,True,False])

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
