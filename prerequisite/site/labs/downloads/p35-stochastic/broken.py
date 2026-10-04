"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def expected_value(outcomes):
    return max(outcomes,key=lambda outcome: outcome[0])[1]

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
