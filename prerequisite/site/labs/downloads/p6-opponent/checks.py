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
    close(m.expected_lane(.2)['CROSS'],.6);close(m.expected_lane(.8)['CROSS'],-.6)
    for blocked in (False,True):
        for enabled in (False,True):
            assert m.lane_reward('CROSS',blocked,enabled)==(-1 if blocked and enabled else 1)
            assert m.lane_reward('WAIT',blocked,enabled)==0
    for p in (0,.2,.8,1):
        for seed in (7,19,31):
            on=m.sample_lane(p,True,10000,seed);off=m.sample_lane(p,False,10000,seed)
            close(on['occupied_fraction'],off['occupied_fraction']);close(on['cross_mean'],1-2*on['occupied_fraction'])
            close(off['cross_mean'],1);assert abs(on['occupied_fraction']-p)<.02
            assert on==m.sample_lane(p,True,10000,seed)
    rejects(lambda:m.expected_lane(-.1));rejects(lambda:m.lane_reward('RUN',False));rejects(lambda:m.sample_lane(.2,True,0,7))

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
