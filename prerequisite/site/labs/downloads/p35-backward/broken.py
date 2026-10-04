"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def solve(horizon, gamma):
    rows=[dict(A=0.0,B=0.0,T=0.0,action=None)]
    for h in range(1,horizon+1):
        via=1+gamma*4  # Uses the eventual B value even with no time to collect it.
        rows.append(dict(A=max(3,via),B=4,T=0,action="VIA" if via>3 else "DIRECT"))
    return rows

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
