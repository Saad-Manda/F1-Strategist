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

class Draw:
    def __init__(self,x):self.x=x
    def random(self):return self.x

def check(module):
    import random
    f=module.probabilities;s=module.select_action
    close_list(f([0.6,0.1,99],[True,True,False],0.2),[0.9,0.1,0])
    close_list(f([0.6,0.1,99],[True,True,False],1),[0.5,0.5,0])
    close_list(f([3,3,99],[True,True,False],0),[0.5,0.5,0])
    close_list(f([-3,-1,-1],[True,True,True],0.3),[0.1,0.45,0.45])
    for draw,action in [(0,0),(0.899,0),(0.9,1),(0.999,1)]:
        assert s([0.6,0.1,99],[True,True,False],0.2,Draw(draw))==action
    assert s([99,2],[False,True],0,Draw(0))==1
    for seed in (7,31,89):
        rng=random.Random(seed)
        draws=[s([1,1,99],[True,True,False],0,rng) for _ in range(10000)]
        assert set(draws)=={0,1} and abs(draws.count(0)/len(draws)-0.5)<0.02,'tie selection biased or illegal'
    a,b=random.Random(9),random.Random(9)
    assert [s([1,2],[True,True],0.3,a) for _ in range(100)]==[s([1,2],[True,True],0.3,b) for _ in range(100)]
    for args in [([1],[False],0.2),([1],[True,False],0.2),([1],[True],-0.1),([float('nan')],[True],0.2)]:
        rejects(lambda:f(*args))
    rejects(lambda:s([1],[True],0,Draw(1)))

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
