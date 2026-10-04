import math
import numpy as np
import torch
def vectors(*xs):
    if not xs or any(x.ndim!=1 or not x.numel() or not torch.isfinite(x).all() for x in xs) or any(x.shape!=xs[0].shape for x in xs):
        raise ValueError("matching nonempty finite vectors required")
def clip_value(epsilon):
    if not math.isfinite(epsilon) or not 0<=epsilon<1:raise ValueError("epsilon in [0,1) required")
def demo(m):
    x=torch.zeros((1,2),dtype=torch.float64,requires_grad=True)
    loss=m.reinforce_loss(x,torch.tensor([0]),torch.tensor([2.],dtype=torch.float64));loss.backward()
    return dict(loss=float(loss.detach()),gradient=x.grad.tolist(),next_probability=m.probabilities(x.detach()-.1*x.grad).tolist())
def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

