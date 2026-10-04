import math, copy, random
import torch
def finite(t): return bool(torch.isfinite(t).all())
def demo(m): return witness(m)
def witness(m):
    online=torch.tensor([[5.,4.,100.]],dtype=torch.float64);target=torch.tensor([[1.,7.,99.]],dtype=torch.float64)
    return dict(double_target=m.double_targets(online,target,torch.tensor([1.],dtype=torch.float64),torch.tensor([False]),torch.tensor([[True,True,False]]),.5).tolist(),dueling=m.dueling(torch.tensor([[2.]],dtype=torch.float64),torch.tensor([[1.,3.]],dtype=torch.float64)).tolist())

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

