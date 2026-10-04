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
    learner=np.array([.2,.3,.5]);saved=m.snapshot(learner);learner[:]=[1,0,0]
    close_list(saved,[.2,.3,.5]);assert not np.shares_memory(learner,saved) and not saved.flags.writeable
    try:saved[0]=1
    except ValueError:pass
    else:raise AssertionError("snapshot is writable")
    pool=[]
    for p in ([1,0,0],[0,1,0],[0,0,1]):
        original=len(pool);updated=m.add_snapshot(pool,p,2);assert len(pool)==original;pool=updated
    assert len(pool)==2;close_list(pool[0],[0,1,0]);close_list(pool[1],[0,0,1])
    close_list(m.pool_probabilities([1,2,3]),[1/6,1/3,1/2]);close_list(m.coverage([0,1,0]),[1,0,-1])
    for seed in (7,19,31):
        draws=m.sample_indices([1,2,3],10000,seed);assert np.array_equal(draws,m.sample_indices([1,2,3],10000,seed))
        close_list(m.coverage([1/3]*3),[0,0,0]);assert np.max(np.abs(np.bincount(draws,minlength=3)/10000-[1/6,1/3,1/2]))<.02
    rejects(lambda:m.snapshot([1,1,1]));rejects(lambda:m.pool_probabilities([0,1]));rejects(lambda:m.add_snapshot([],learner,0))

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
