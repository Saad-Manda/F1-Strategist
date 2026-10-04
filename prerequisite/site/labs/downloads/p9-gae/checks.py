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
    flags=lambda x:np.array(x,dtype=bool)
    for terminal,lam,expected in ((True,1,[2.3,1]),(True,0,[1.4,1]),(False,1,[4.73,3.7]),(False,.5,[3.065,3.7])):
        a,t=m.gae([1,2],[.5,1],[1,3],flags([False,terminal]),flags([True,False]),lam=lam)
        close_list(a,expected);close_list(t,np.array(expected)+[.5,1])
    a,_=m.gae([1,2,100],[.5,1,0],[1,3,999],flags([False,False,True]),flags([True,False,False]))
    close_list(a,[4.73,3.7,100]) # reset reward must not leak backward
    a,_=m.gae([1],[.5],[3],flags([False]),flags([True]));close_list(a,[3.2])
    rejects(lambda:m.gae([1],[0],[0],flags([True]),flags([True])))
    rejects(lambda:m.gae([1],[0],[0],[0],[0]))
    rejects(lambda:m.gae([1],[0],[float('nan')],flags([False]),flags([False])))
    rejects(lambda:m.gae([1],[0],[0],flags([False]),flags([False]),lam=2))

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
