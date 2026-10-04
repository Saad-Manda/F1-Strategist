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
    import torch
    d=torch.float64
    o=torch.tensor([[5.,4.,100.],[2.,9.,0.],[1.,2.,3.]],dtype=d,requires_grad=True)
    t=torch.tensor([[1.,7.,99.],[8.,3.,99.],[4.,5.,6.]],dtype=d,requires_grad=True)
    r=torch.tensor([1.,-2.,4.],dtype=d);done=torch.tensor([False,False,True]);legal=torch.tensor([[True,True,False],[True,True,False],[False,False,False]])
    y=m.double_targets(o,t,r,done,legal,.5);close_list(y.tolist(),[1.5,-.5,4]);assert y.shape==(3,) and not y.requires_grad
    close_list(m.double_targets(o,t,r,done,legal,0).tolist(),r.tolist())
    rejects(lambda:m.double_targets(o,t,r,torch.tensor([False,False,False]),legal,.5))
    v=torch.tensor([[2.],[-1.]],dtype=d,requires_grad=True);a=torch.tensor([[1.,3.],[8.,-2.]],dtype=d,requires_grad=True)
    q=m.dueling(v,a);assert q.shape==(2,2)
    assert torch.allclose(q,torch.tensor([[1.,3.],[4.,-6.]],dtype=d))
    assert torch.allclose(q,m.dueling(v,a+torch.tensor([[10.],[-7.]],dtype=d)))
    q[:,0].sum().backward();assert v.grad is not None and a.grad is not None
    rejects(lambda:m.dueling(torch.ones(2),a))

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
