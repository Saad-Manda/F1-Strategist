"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def solve(horizon, gamma):
    if type(horizon) is not int or not 0 <= horizon <= 10:
        raise ValueError("horizon must be an integer from 0 to 10")
    validate_distribution([gamma,1-gamma])
    rows=[dict(A=0.0,B=0.0,T=0.0,action=None)]
    for h in range(1,horizon+1):
        previous=rows[-1]
        values={s: {a: reward + gamma*previous[next_state]
                    for a,(next_state,reward) in actions.items()}
                for s,actions in MODEL.items()}
        action=max(values["A"],key=values["A"].get)
        rows.append(dict(A=values["A"][action], B=max(values["B"].values()), T=0.0,action=action))
    return rows

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
