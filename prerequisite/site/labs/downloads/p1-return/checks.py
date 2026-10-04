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

def check(module):
    f = module.returns
    for gamma, target in [(0, [2,-1,4]), (0.5, [2.5,1,4]), (1, [5,3,4])]:
        close_list(f([2,-1,4], gamma), target)
    assert f([], 0.5) == []
    # Independent forward sum, including negative-only and longer trajectories.
    for rewards in [[-3], [1,0,-2,7], [-2,-1,-3], [0,0]]:
        for gamma in (0,0.2,0.8,1):
            target = [sum(gamma**(k-t)*rewards[k] for k in range(t,len(rewards)))
                      for t in range(len(rewards))]
            close_list(f(rewards,gamma),target)
    for gamma in (-0.1,1.1,float("nan"),float("inf")):
        rejects(lambda: f([1],gamma))
    rejects(lambda: f([float("nan")],0.5))

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
