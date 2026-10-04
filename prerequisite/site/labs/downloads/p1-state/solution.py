"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def encode_state(mode, remaining=None):
    if type(mode) is not int or mode not in (0, 1):
        raise ValueError("mode must be 0 or 1")
    if remaining is not None and (type(remaining) is not int or remaining < 0):
        raise ValueError("remaining must be a nonnegative integer")
    return mode if remaining is None else (mode, remaining)

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
