"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def probabilities(values, legal, epsilon):
    validate_distribution([epsilon,1-epsilon])
    indices=legal_indices(values,legal)
    maximum=max(values[i] for i in indices)
    ties=[i for i in indices if values[i]==maximum]
    return [epsilon/len(indices)+(1-epsilon)/len(ties)*(i in ties) if legal[i] else 0
            for i in range(len(values))]

def select_action(values, legal, epsilon, rng):
    probabilities_=probabilities(values,legal,epsilon)
    draw=rng.random()
    if not 0<=draw<1:raise ValueError('draw must be in [0,1)')
    cumulative=0.0
    for action,p in enumerate(probabilities_):
        cumulative+=p
        if draw<cumulative:return action
    return max(i for i,p in enumerate(probabilities_) if p>0)

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
