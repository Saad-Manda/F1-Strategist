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

def check(m):
    import numpy as np
    p,w=m.distribution([1,4,9],.5,1);close_list(p,[1/6,1/3,1/2]);close_list(w,[1,.5,1/3]);close(m.weighted_loss([1,4,9],w),2)
    close(m.new_priority([1,4,9]),9);close(m.new_priority([]),1)
    pp,_=m.distribution([1,4,9,m.new_priority([1,4,9])],.5,1);close_list(pp,[1/9,2/9,3/9,3/9])
    for alpha in (0,.3,1):
        for beta in (0,.7,1):
            raw=[.25,2,7,11];p,w=m.distribution(raw,alpha,beta)
            expected=np.power(raw,alpha);expected/=sum(expected);close_list(p,expected)
            ew=np.power(4*expected,-beta);ew/=max(ew);close_list(w,ew)
    close(m.update_priority(-3),3.000001);close(m.update_priority(0),.000001)
    rejects(lambda:m.distribution([0,1],.5,1));rejects(lambda:m.distribution([1,float('nan')],.5,1))
    rejects(lambda:m.distribution([1],-1,1));rejects(lambda:m.weighted_loss([1,2],[1]))
    for seed in (7,19,31):
        p,_=m.distribution([1,4,9],.5,1);draws=np.random.default_rng(seed).choice(3,10000,p=p)
        assert np.max(np.abs(np.bincount(draws,minlength=3)/10000-p))<.02

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
