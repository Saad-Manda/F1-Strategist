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
    x=torch.zeros((1,2),dtype=d,requires_grad=True);r=torch.tensor([2.],dtype=d,requires_grad=True)
    loss=m.reinforce_loss(x,torch.tensor([0]),r);close(float(loss.detach()),2*math.log(2));loss.backward()
    close_list(x.grad[0].tolist(),[-1,1]);assert r.grad is None
    close(float(m.probabilities(x.detach()-.1*x.grad)[0,0]),.549833997312478)
    for action,ret in ((0,-2),(1,3),(1,-1)):
        z=torch.tensor([[.3,-.7]],dtype=d,requires_grad=True);p=torch.softmax(z.detach(),1)
        m.reinforce_loss(z,torch.tensor([action]),torch.tensor([float(ret)],dtype=d)).backward()
        oracle=p.clone();oracle[0,action]-=1;assert torch.allclose(z.grad,ret*oracle)
    mask=torch.tensor([[True,False,True]])
    close_list(m.probabilities(torch.zeros((1,3),dtype=d),mask)[0].tolist(),[.5,0,.5])
    rejects(lambda:m.probabilities(torch.zeros((1,2)),torch.zeros((1,2),dtype=torch.bool)))
    rejects(lambda:m.reinforce_loss(torch.zeros((1,3)),torch.tensor([1]),torch.ones(1),mask))
    rejects(lambda:m.probabilities(torch.tensor([[float('nan'),0]])))
    rejects(lambda:m.reinforce_loss(torch.zeros((1,2)),torch.tensor([2]),torch.ones(1)))
    # Stable log-softmax must not log an underflowed probability.
    close(float(m.reinforce_loss(torch.tensor([[1000.,-1000.]],dtype=d),torch.tensor([1]),torch.ones(1,dtype=d))),2000)

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
