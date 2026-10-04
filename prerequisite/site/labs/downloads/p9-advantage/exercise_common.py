import math
import numpy as np
import torch
def vectors(*xs):
    if not xs or any(x.ndim!=1 or not x.numel() or not torch.isfinite(x).all() for x in xs) or any(x.shape!=xs[0].shape for x in xs):
        raise ValueError("matching nonempty finite vectors required")
def clip_value(epsilon):
    if not math.isfinite(epsilon) or not 0<=epsilon<1:raise ValueError("epsilon in [0,1) required")
def demo(m):
    values=torch.tensor([5.,5.],requires_grad=True);a=m.advantages(torch.tensor([8.,2.]),values)
    return dict(advantages=a.tolist(),advantage_requires_grad=a.requires_grad)
def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

