"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def push(buffer, item, capacity):
    buffer.append(item)
    if len(buffer)>capacity:buffer.pop()
def sample(buffer, batch_size, rng):return [buffer[-1]]*batch_size
def make_target(online):return online
def sync_target(target, online, step, interval):target.load_state_dict(online.state_dict())
def targets(target, next_states, rewards, terminated, gamma):return rewards+gamma*target(next_states).max(dim=1).values

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
