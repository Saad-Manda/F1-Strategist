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
    for i in range(3):
        for j in range(3):
            # Modular winner oracle, independent of stored MATRIX.
            expected=0 if i==j else (1 if (i-j)%3==1 else -1)
            assert m.payoff(i,j)==expected
    close(m.expected_payoff([0,1,0],[.5,.25,.25]),.25)
    for j in range(3):
        pure=[int(i==j) for i in range(3)]
        close(m.expected_payoff([1/3]*3,pure),0);assert m.best_response(pure)==[(j+1)%3]
    assert set(m.best_response([1/3]*3))=={0,1,2}
    values=[1.,2.,3.];close_list(m.action_update(values,1,-1,.5),[1,.5,3]);assert values==[1,2,3]
    rejects(lambda:m.expected_payoff([1,1,1],[1,0,0]));rejects(lambda:m.payoff(3,0));rejects(lambda:m.action_update(values,0,1,1.1))

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
