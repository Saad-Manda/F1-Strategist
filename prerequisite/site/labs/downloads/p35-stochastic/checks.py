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
    f=module.expected_value
    for p,target in [(0.25,1),(0.5,4),(1/3,2),(0,-2),(1,10)]:
        close(f([(p,10),(1-p,-2)]),target)
    close(f([(0.2,-5),(0.3,0),(0.5,8)]),3)
    close(f([(1,2)]),2)
    close(f([(0,999),(1,-3)]),-3)
    for outcomes in [[],[(-0.1,2),(1.1,3)],[(0.4,2),(0.4,3)],
                     [(float("nan"),1)],[(1,float("inf"))]]:
        rejects(lambda: f(outcomes))

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
