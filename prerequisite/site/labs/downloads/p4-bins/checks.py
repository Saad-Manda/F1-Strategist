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
    f=module.bin_index
    assert f(0.49,[0,1])==f(0.51,[0,1])==0
    for x,target in [(0,0),(0.49,0),(0.5,1),(0.51,1),(1,1)]:assert f(x,[0,0.5,1])==target,f'boundary failed at {x}'
    for x,target in [(0.1,0),(0.45,1),(0.49,1),(0.5,2),(0.55,3),(0.99,3),(1,3)]:
        assert f(x,[0,0.45,0.5,0.55,1])==target,'nonuniform edges ignored'
    assert module.table_size([4,4,4])==dict(states=64,entries=128,bytes=1024)
    assert module.table_size([8,8,8])['entries']/module.table_size([4,4,4])['entries']==8
    assert module.table_size([12,5,10,3,3,2,8,2],6)['states']==172800
    for x in (-0.1,1.1,float('nan')):rejects(lambda:f(x,[0,0.5,1]))
    for edges in [[],[0],[0,0.5,0.5,1],[0,0.8,0.5,1],[0.1,1],[0,0.9],[0,float('nan'),1]]:
        rejects(lambda:f(0.5,edges))
    for counts,actions in [([],2),([0],2),([1.5],2),([2],0),([True],2)]:rejects(lambda:module.table_size(counts,actions))

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
