"""Behaviour checks. No reference-solution import; alternate correct implementations welcome."""
import argparse
import importlib.util
import math
from pathlib import Path
import sys

def close(actual,expected):
    assert math.isfinite(actual) and math.isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-9), f"expected {expected}, got {actual}"

def close_list(actual,expected):
    assert len(actual)==len(expected), "wrong result length"
    for a,b in zip(actual,expected): close(a,b)

def rejects(call):
    try: call()
    except ValueError: return
    raise AssertionError("invalid input must raise ValueError")

def load_candidate(path):
    path=Path(path).resolve()
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location("candidate",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class Draws:
    def __init__(self,draws):self.draws=iter(draws);self.calls=0
    def random(self):self.calls+=1;return next(self.draws)

def check(module):
    memory={};rng=Draws([0.95,0.05])
    close(module.target(memory,0,'RISK',[6,-10],[True,True],1,False,False,0.2,rng),-10)
    assert rng.calls==1 and memory.get('pending')==('RISK',1),'target must commit its sampled action'
    assert module.act(memory,'RISK',[6,-10],[True,True],0.2,rng)==1,'executed action differs from target'
    assert rng.calls==1 and 'pending' not in memory,'act must consume without resampling'
    assert module.act(memory,'RISK',[6,-10],[True,True],0.2,rng)==0 and rng.calls==2
    memory['pending']=('RISK',1);module.reset(memory)
    assert 'pending' not in memory,'reset leaked pending action'
    assert module.act(memory,'RISK',[6,-10],[True,True],0,Draws([0.99]))==0,'greedy evaluation retained exploration'
    for terminated,truncated in [(True,False),(True,True)]:
        memory['pending']=('RISK',1);rng=Draws([])
        close(module.target(memory,3,'T',[],[],1,terminated,truncated,0.2,rng),3)
        assert rng.calls==0 and 'pending' not in memory,'terminal target sampled or leaked cache'
    rng=Draws([0.95]);memory['pending']=('old',0)
    close(module.target(memory,1,'RISK',[6,-10],[True,True],0.5,False,True,0.2,rng),-4)
    assert 'pending' not in memory,'truncation leaked hypothetical bootstrap action'
    rng=Draws([0.1]);memory={}
    close(module.target(memory,0,'RISK',[99,6],[False,True],1,False,False,0.2,rng),6)
    assert module.act(memory,'RISK',[99,6],[False,True],0.2,rng)==1
    memory['pending']=('wrong',0)
    rejects(lambda:module.act(memory,'RISK',[6,-10],[True,True],0.2,Draws([0])))
    rejects(lambda:module.target({},0,'RISK',[],[],1,False,False,0.2,Draws([0])))
    rejects(lambda:module.target({},0,'RISK',[6],[True],2,False,False,0.2,Draws([0])))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate",default="starter.py")
    args=parser.parse_args()
    try:
        check(load_candidate(args.candidate))
    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}")
        raise SystemExit(1)
    print("PASS: all behavioural and boundary checks")

if __name__=="__main__": main()
