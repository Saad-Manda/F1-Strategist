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
    f=module.update
    for terminal,truncated,target,value in [(False,False,5,2.75),(True,False,1,1.75),(False,True,5,2.75),(True,True,1,1.75)]:
        result=f(2,1,[4,8,99],[True,True,False],0.25,0.5,terminal,truncated)
        close(result['target'],target);close(result['error'],target-2);close(result['value'],value)
    close(f(2,1,[],[],0.25,0.5,True)['value'],1.75)
    close(f(-3,-1,[-8,-2,99],[True,True,False],1,1,False)['target'],-3)
    close(f(7,-1,[8],[True],0,0,False)['value'],7)
    values=[4,8,99];mask=[True,True,False]
    f(2,1,values,mask,0.25,0.5,False)
    assert values==[4,8,99] and mask==[True,True,False], 'input arrays mutated'
    for values,mask in [([],[]),([1],[False]),([1],[True,False])]:
        rejects(lambda:f(2,1,values,mask,0.25,0.5,False))
    for alpha,gamma in [(-0.1,0.5),(0.2,1.1),(float('nan'),0.5)]:
        rejects(lambda:f(2,1,[8],[True],alpha,gamma,False))
    rejects(lambda:f(float('inf'),1,[8],[True],0.2,0.5,False))

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
