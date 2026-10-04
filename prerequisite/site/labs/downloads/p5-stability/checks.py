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
    import torch,random
    buffer=[]
    for i in range(6):m.push(buffer,i,4)
    assert buffer==[2,3,4,5],"FIFO eviction is wrong"
    rejects(lambda:m.push([],0,0));rejects(lambda:m.sample([],1,random.Random(1)))
    for seed in (7,19,31):
        draws=m.sample(buffer,10000,random.Random(seed));assert all(v in buffer for v in draws)
        for v in buffer:assert abs(draws.count(v)/len(draws)-.25)<.02,"uniform with-replacement sampling required"
    assert m.sample(buffer,20,random.Random(7))==m.sample(buffer,20,random.Random(7))
    online=torch.nn.Linear(1,2,dtype=torch.float64)
    with torch.no_grad():online.weight.zero_();online.bias.copy_(torch.tensor([1.,2.]))
    target=m.make_target(online);assert target is not online and not target.training
    with torch.no_grad():online.bias.copy_(torch.tensor([3.,4.]))
    close_list(target.bias.detach().tolist(),[1,2]);m.sync_target(target,online,1,2);close_list(target.bias.detach().tolist(),[1,2])
    m.sync_target(target,online,2,2);close_list(target.bias.detach().tolist(),[3,4])
    # Deliberately trainable target source: targets() must itself detach.
    t=m.targets(online,torch.zeros((2,1),dtype=torch.float64),torch.tensor([1.,1.],dtype=torch.float64),torch.tensor([False,True]),.5)
    close_list(t.tolist(),[3,1]);assert not t.requires_grad
    online.zero_grad();prediction=online(torch.ones((2,1),dtype=torch.float64))[:,0]
    ((prediction-t)**2).mean().backward()
    assert online.weight.grad is not None and all(p.grad is None for p in target.parameters())
    rejects(lambda:m.sync_target(target,online,0,2))
    rejects(lambda:m.targets(online,torch.zeros((2,1)),torch.ones(2),torch.tensor([False,True]),1.1))

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
