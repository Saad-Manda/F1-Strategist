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
    close_list(module.branch_values(0.5,0.5),[3,3])
    close_list(module.branch_values(1,0.5),[4,5])
    close_list(module.branch_values(1,0),[3,5])
    close_list(module.branch_values(1,1),[5,5])
    f=module.backup
    close_list(f([-8,-2,99],[0.25,0.75,0],[True,True,False]),[-3.5,-2])
    close_list(f([999,7],[0,1],[False,True]),[7,7])
    for args in [([1],[1],[False]), ([1,2],[0.5,0.4],[True,True]),
                 ([1,2],[0.5,0.5],[True,False]), ([1],[1,0],[True]),
                 ([1,2],[-1,2],[True,True])]:
        rejects(lambda: f(*args))
    rejects(lambda: module.branch_values(2,0.5))

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
