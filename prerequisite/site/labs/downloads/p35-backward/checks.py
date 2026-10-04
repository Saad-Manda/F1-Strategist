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

def paths(state, remaining, rewards=()):
    # Exhaustive trajectories on an independently specified tiny world.
    if state == "T" or remaining == 0:
        return [rewards]
    edges = {"A": [("T",3),("B",1)], "B": [("T",4)]}[state]
    return [path for successor,reward in edges
            for path in paths(successor,remaining-1,rewards+(reward,))]

def check(module):
    for horizon in range(6):
        for gamma in (0,0.25,0.5,0.75,1):
            rows=module.solve(horizon,gamma)
            assert len(rows)==horizon+1, "one row per remaining horizon required"
            for h,values in enumerate(rows):
                for state in ("A","B","T"):
                    target=max(sum(gamma**i*r for i,r in enumerate(path)) for path in paths(state,h))
                    close(values[state],target)
                if h == 0:
                    assert values["action"] is None
                else:
                    assert values["action"] in ("DIRECT","VIA")
                    # Accept either action in an exact tie.
                    action_value=3 if values["action"]=="DIRECT" else 1+gamma*(4 if h>1 else 0)
                    close(action_value,values["A"])
    assert module.solve(1,1)[1]["action"]=="DIRECT"
    assert module.solve(2,1)[2]["action"]=="VIA"
    for args in [(-1,1),(1.5,1),(11,1),(2,-0.1),(2,float("nan"))]:
        rejects(lambda: module.solve(*args))

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
