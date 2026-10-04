"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def joint_step(actions):
    reward=2*actions['A']+actions['B']
    return dict(rewards={'A':reward,'B':reward},terminations={'A':True,'B':True},truncations={'A':False,'B':False},agents=[])
def contributions(actions):return joint_step(actions)['rewards']

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
