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
    rows=m.route_returns();close_list([r['base'] for r in rows],[3,4,0]);close_list([r['bonus'] for r in rows],[3,4,5]);close_list([r['shaped'] for r in rows],[1,2,-2])
    # Independent telescoping oracle across lengths, discounts and endpoints.
    for rewards,potentials in [([3],[2,0]),([0,4],[2,1,0]),([1,-2,5],[3,8,-1,7]),([],[2])]:
        for gamma in (0,.3,.5,1):
            base=sum(gamma**i*r for i,r in enumerate(rewards))
            close(m.shaped_return(rewards,potentials,gamma),base-potentials[0]+gamma**len(rewards)*potentials[-1])
    for gamma in (.5,1):
        for end in (0,10):
            rows=m.route_returns(gamma,end)
            for row in rows:close(row['shift'],-2+row['boundary'])
    mismatch=m.shaped_return([0,4],[2,1,0],.5,1);close(mismatch,0.5)
    rejects(lambda:m.shaped_return([1],[2],1));rejects(lambda:m.shaped_return([1],[2,0],1.2));rejects(lambda:m.shaped_return([float('nan')],[2,0],1))

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
