import math
import numpy as np
import torch
def vectors(*xs):
    if not xs or any(x.ndim!=1 or not x.numel() or not torch.isfinite(x).all() for x in xs) or any(x.shape!=xs[0].shape for x in xs):
        raise ValueError("matching nonempty finite vectors required")
def clip_value(epsilon):
    if not math.isfinite(epsilon) or not 0<=epsilon<1:raise ValueError("epsilon in [0,1) required")
def demo(m):
    r=torch.tensor([1.3,.7,.7,1.3],dtype=torch.float64);a=torch.tensor([1.,1.,-1.,-1.],dtype=torch.float64)
    return dict(loss=float(m.ppo_loss(r.log(),torch.zeros(4,dtype=torch.float64),a)),objectives=[-float(m.ppo_loss(r[i:i+1].log(),torch.zeros(1,dtype=torch.float64),a[i:i+1])) for i in range(4)])
def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

