"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def bin_index(x, edges):
    return min(int(x*len(edges)),len(edges)-1)  # Counts edges as bins; ignores nonuniform boundaries.

def table_size(bin_counts, actions=2):
    states=sum(bin_counts)
    return dict(states=states,entries=states*actions,bytes=states*actions*8)

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
