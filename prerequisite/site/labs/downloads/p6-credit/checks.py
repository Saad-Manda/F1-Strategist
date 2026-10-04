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
    for a in (0,1):
        for b in (0,1):
            actions={'A':a,'B':b};r=m.joint_step(actions)
            assert r['rewards']=={'A':2*a+b,'B':2*a+b}
            assert r['terminations']=={'A':True,'B':True} and r['truncations']=={'A':False,'B':False} and r['agents']==[]
            assert m.contributions(actions)=={'A':2*a,'B':b}
            assert actions=={'A':a,'B':b},"inputs were mutated"
    for invalid in ({'A':1},{'A':1,'B':1,'C':0},{'A':2,'B':0},{'A':True,'B':0}):
        rejects(lambda:m.joint_step(invalid));rejects(lambda:m.contributions(invalid))

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
