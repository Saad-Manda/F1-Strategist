"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def lane_reward(action, occupied, blocking=True):return 0 if action=='WAIT' else 1
def expected_lane(p, blocking=True):return {'CROSS':1,'WAIT':0}
def sample_lane(p, blocking, samples, seed):
    rng=random.Random(seed);occupied=[rng.random()<p for _ in range(samples)]
    return dict(occupied_fraction=sum(occupied)/samples,cross_mean=1,wait_mean=0)

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
