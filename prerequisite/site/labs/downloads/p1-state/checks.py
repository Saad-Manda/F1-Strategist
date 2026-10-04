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
    f = module.encode_state
    assert f(0) == 0 and f(1) == 1, "encoder aliases modes"
    assert f(1, 2) == (1, 2) and f(1, 1) == (1, 1), "remaining time is missing"
    from exercise_common import rollout
    a = rollout(f, ["CLAIM"])
    b = rollout(f, ["FLIP", "CLAIM"])
    assert a[-1]["reward"] == -1 and b[-1]["reward"] == 1
    assert a[-1]["before"] != b[-1]["before"], "different futures share an observation"
    for args in [(2,), (True,), (0, -1), (0, 1.5)]:
        rejects(lambda: f(*args))

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
