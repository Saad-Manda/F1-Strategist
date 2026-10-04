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
    v=torch.tensor([5.,5.],dtype=d,requires_grad=True);r=torch.tensor([8.,2.],dtype=d,requires_grad=True)
    a=m.advantages(r,v);close_list(a.tolist(),[3,-3]);assert not a.requires_grad
    lp=torch.tensor([-.7,-.9],dtype=d,requires_grad=True)
    supplied=torch.tensor([3.,-3.],dtype=d,requires_grad=True)
    loss=m.actor_loss(lp,supplied);close(float(loss.detach()),-.3);loss.backward()
    close_list(lp.grad.tolist(),[-1.5,1.5]);assert supplied.grad is None and v.grad is None
    loss=m.critic_loss(v,r);close(float(loss.detach()),9);loss.backward()
    close_list(v.grad.tolist(),[-3,3]);assert r.grad is None
    for f in (m.advantages,m.actor_loss,m.critic_loss):
        rejects(lambda:f(torch.zeros(2),torch.zeros(3)))
        rejects(lambda:f(torch.tensor([float('nan')]),torch.zeros(1)))
        rejects(lambda:f(torch.zeros(0),torch.zeros(0)))

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
