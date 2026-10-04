"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def push(buffer, item, capacity):
    # TODO: follow README.md.
    raise NotImplementedError("Complete push")

def sample(buffer, batch_size, rng):
    # TODO: follow README.md.
    raise NotImplementedError("Complete sample")

def make_target(online):
    # TODO: follow README.md.
    raise NotImplementedError("Complete make_target")

def sync_target(target, online, step, interval):
    # TODO: follow README.md.
    raise NotImplementedError("Complete sync_target")

def targets(target, next_states, rewards, terminated, gamma):
    # TODO: follow README.md.
    raise NotImplementedError("Complete targets")

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
