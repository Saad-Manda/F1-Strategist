"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def double_targets(online_values, target_values, rewards, terminated, legal, gamma):return rewards+gamma*target_values.max(dim=1).values
def dueling(value, advantage):return value+advantage

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
