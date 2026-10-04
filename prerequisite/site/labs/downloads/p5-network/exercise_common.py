import math, copy, random
import torch
def finite(t): return bool(torch.isfinite(t).all())
def demo(m): return witness(m)
def witness(m):
    x=torch.tensor([[.25]],dtype=torch.float64)
    w=torch.zeros((2,1),dtype=torch.float64,requires_grad=True);b=torch.zeros(2,dtype=torch.float64,requires_grad=True)
    prediction=m.predict(x,w,b)
    loss=m.mse(prediction,torch.tensor([[.25,.75]],dtype=torch.float64));loss.backward()
    return dict(prediction=prediction.detach().tolist(),loss=float(loss.detach()),weight_gradient=w.grad.tolist(),bias_gradient=b.grad.tolist())

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

