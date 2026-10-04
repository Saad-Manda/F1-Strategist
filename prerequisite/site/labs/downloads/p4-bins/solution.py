"""Standalone RL exercise. Standard library only."""
from exercise_common import *

def bin_index(x, edges):
    import bisect
    import math
    if not math.isfinite(x) or not 0<=x<=1:raise ValueError('x must be in [0,1]')
    if len(edges)<2 or edges[0]!=0 or edges[-1]!=1 or any(not math.isfinite(e) or (i and e<=edges[i-1]) for i,e in enumerate(edges)):
        raise ValueError('edges must strictly increase from 0 to 1')
    return min(bisect.bisect_right(edges,x)-1,len(edges)-2)

def table_size(bin_counts, actions=2):
    import math
    if not bin_counts or any(type(n) is not int or n<1 for n in list(bin_counts)+[actions]):raise ValueError('positive integer counts required')
    states=math.prod(bin_counts);entries=states*actions
    return dict(states=states,entries=entries,bytes=entries*8)

if __name__ == "__main__":
    import sys
    run(sys.modules[__name__])
