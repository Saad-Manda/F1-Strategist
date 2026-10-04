"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def shaped_return(rewards, potentials, gamma, shaping_gamma=None):
    sg=gamma if shaping_gamma is None else shaping_gamma
    if len(potentials)!=len(rewards)+1 or any(not math.isfinite(v) for v in [*rewards,*potentials,gamma,sg]) or not 0<=gamma<=1 or not 0<=sg<=1:raise ValueError("finite rewards/potentials and valid discounts required")
    return sum(gamma**i*(r+sg*potentials[i+1]-potentials[i]) for i,r in enumerate(rewards))
def route_returns(gamma=1, failure_potential=0, shaping_gamma=None):
    result=[]
    for name,rewards,potentials,bonus in routes(failure_potential):
        shaped=shaped_return(rewards,potentials,gamma,shaping_gamma)
        base=sum(gamma**i*r for i,r in enumerate(rewards))
        result.append(dict(route=name,base=base,bonus=sum(gamma**i*r for i,r in enumerate(bonus)),shaped=shaped,shift=shaped-base,boundary=gamma**len(rewards)*potentials[-1]))
    return result

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
