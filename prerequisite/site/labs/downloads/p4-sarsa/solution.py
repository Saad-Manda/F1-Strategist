"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def act(memory, state, values, legal, epsilon, rng):
    pending=memory.pop('pending',None)
    if pending is None:return policy_select(values,legal,epsilon,rng)
    pending_state,action=pending
    if pending_state!=state or action not in legal_indices(values,legal):raise ValueError('stale pending action')
    return action

def target(memory, reward, next_state, values, legal, gamma, terminated, truncated, epsilon, rng):
    import math
    validate_distribution([gamma,1-gamma])
    if not math.isfinite(reward):raise ValueError('reward must be finite')
    memory.pop('pending',None)
    if terminated:return reward
    action=policy_select(values,legal,epsilon,rng)
    if not truncated:memory['pending']=(next_state,action)
    return reward+gamma*values[action]

def reset(memory):
    memory.pop('pending',None)

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
