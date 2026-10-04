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
    for ratio,adv,obj,derivative in ((1.3,1,1.2,0),(.7,1,.7,-.7),(.7,-1,-.8,0),(1.3,-1,-1.3,1.3)):
        x=torch.tensor([math.log(ratio)],dtype=d,requires_grad=True);old=torch.zeros(1,dtype=d,requires_grad=True);a=torch.tensor([float(adv)],dtype=d,requires_grad=True)
        loss=m.ppo_loss(x,old,a);close(float(loss.detach()),-obj);loss.backward()
        close(float(x.grad[0]),derivative);assert old.grad is None and a.grad is None
    x=torch.tensor([-.7,-.3],dtype=d,requires_grad=True);old=m.frozen(x)
    assert not old.requires_grad
    with torch.no_grad():x.add_(1)
    close_list(old.tolist(),[-.7,-.3])
    r=torch.tensor([1.3,.7,1.],dtype=d);data=m.diagnostics(r.log(),torch.zeros(3,dtype=d),torch.ones(3,dtype=d))
    close_list(data['ratios'].tolist(),r.tolist());close(data['clip_fraction'],2/3);close(data['approx_kl'],float((r-1-r.log()).mean()))
    rejects(lambda:m.ppo_loss(torch.zeros(1),torch.zeros(2),torch.ones(1)))
    rejects(lambda:m.ppo_loss(torch.zeros(1),torch.zeros(1),torch.ones(1),epsilon=1))
    rejects(lambda:m.ppo_loss(torch.tensor([1000.]),torch.zeros(1),torch.ones(1)))

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
