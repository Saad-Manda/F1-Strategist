"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def distribution(raw_priorities, alpha, beta):
    # TODO: follow README.md.
    raise NotImplementedError("Complete distribution")

def new_priority(raw_priorities):
    # TODO: follow README.md.
    raise NotImplementedError("Complete new_priority")

def update_priority(td_error, epsilon=1e-6):
    # TODO: follow README.md.
    raise NotImplementedError("Complete update_priority")

def weighted_loss(losses, weights):
    # TODO: follow README.md.
    raise NotImplementedError("Complete weighted_loss")

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
