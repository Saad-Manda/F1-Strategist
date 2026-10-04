"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def joint_step(actions):
    team_actions(actions)
    reward=2*actions['A']+actions['B']
    return dict(rewards={'A':reward,'B':reward},terminations={'A':True,'B':True},truncations={'A':False,'B':False},agents=[])
def contributions(actions):
    team_actions(actions)
    total=joint_step(actions)['rewards']['A'];result={}
    for agent in ('A','B'):
        counterfactual=dict(actions);counterfactual[agent]=0
        result[agent]=total-joint_step(counterfactual)['rewards']['A']
    return result

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
