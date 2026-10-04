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
    torch.set_num_threads(1);d=torch.float64
    x=torch.tensor([[.25]],dtype=d);w=torch.zeros((2,1),dtype=d,requires_grad=True);b=torch.zeros(2,dtype=d,requires_grad=True)
    p=m.predict(x,w,b);assert p.shape==(1,2)
    loss=m.mse(p,torch.tensor([[.25,.75]],dtype=d));close(float(loss.detach()),.3125)
    loss.backward();close_list(w.grad.flatten().tolist(),[-.0625,-.1875]);close_list(b.grad.tolist(),[-.25,-.75])
    x=torch.tensor([[0.],[1.],[.4]],dtype=d);w=torch.tensor([[2.],[-3.]],dtype=d);b=torch.tensor([1.,4.],dtype=d)
    assert torch.allclose(m.predict(x,w,b),torch.tensor([[1.,4.],[3.,1.],[1.8,2.8]],dtype=d))
    rejects(lambda:m.mse(torch.zeros(2),torch.zeros(3)))
    rejects(lambda:m.predict(x,torch.zeros((2,2),dtype=d),b))
    rejects(lambda:m.mse(torch.tensor([float('nan')]),torch.zeros(1)))
    model=torch.nn.Linear(1,2,dtype=d)
    with torch.no_grad():model.weight.zero_();model.bias.zero_()
    opt=torch.optim.SGD(model.parameters(),lr=.1);labels=torch.cat((x,1-x),dim=1)
    # Independent analytic SGD oracle: second step catches stale gradients.
    for _ in range(2):
        ow=model.weight.detach().clone();ob=model.bias.detach().clone();error=x@ow.T+ob-labels
        gw=2*error.T@x/error.numel();gb=2*error.sum(0)/error.numel()
        m.train_step(model,opt,x,labels)
        assert torch.allclose(model.weight,ow-.1*gw,atol=1e-10,rtol=0)
        assert torch.allclose(model.bias,ob-.1*gb,atol=1e-10,rtol=0)
        assert all(torch.isfinite(p.grad).all() for p in model.parameters())

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
