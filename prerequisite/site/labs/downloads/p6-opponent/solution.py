"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def lane_reward(action, occupied, blocking=True):
    if action not in ('CROSS','WAIT') or type(occupied) is not bool or type(blocking) is not bool:raise ValueError("invalid action/flags")
    return 0 if action=='WAIT' else (-1 if blocking and occupied else 1)
def expected_lane(p, blocking=True):
    lane_settings(p,blocking)
    return {'CROSS':1-2*p if blocking else 1,'WAIT':0}
def sample_lane(p, blocking, samples, seed):
    lane_settings(p,blocking)
    if type(samples) is not int or samples<1:raise ValueError("positive sample count required")
    rng=random.Random(seed);occupied=[rng.random()<p for _ in range(samples)]
    return dict(occupied_fraction=sum(occupied)/samples,cross_mean=sum(lane_reward('CROSS',o,blocking) for o in occupied)/samples,wait_mean=0)

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
