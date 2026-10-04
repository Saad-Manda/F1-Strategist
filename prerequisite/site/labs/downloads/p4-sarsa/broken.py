"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def act(memory, state, values, legal, epsilon, rng):
    return policy_select(values,legal,epsilon,rng)  # Resamples instead of consuming pending.

def target(memory, reward, next_state, values, legal, gamma, terminated, truncated, epsilon, rng):
    if terminated:return reward
    action=policy_select(values,legal,epsilon,rng)
    memory['pending']=(next_state,action)
    return reward+gamma*values[action]

def reset(memory):
    pass  # Pending action can leak into a new episode.

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
