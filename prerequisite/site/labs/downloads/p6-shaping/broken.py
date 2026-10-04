"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def shaped_return(rewards, potentials, gamma, shaping_gamma=None):
    return sum(gamma**i*(r+potentials[i+1]-potentials[i]) for i,r in enumerate(rewards))
def route_returns(gamma=1, failure_potential=0, shaping_gamma=None):
    result=[]
    for name,rewards,potentials,bonus in routes(failure_potential):
        base=sum(gamma**i*r for i,r in enumerate(rewards));shaped=shaped_return(rewards,potentials,gamma,shaping_gamma)
        result.append(dict(route=name,base=base,bonus=sum(gamma**i*r for i,r in enumerate(bonus)),shaped=shaped,shift=shaped-base,boundary=0))
    return result

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
