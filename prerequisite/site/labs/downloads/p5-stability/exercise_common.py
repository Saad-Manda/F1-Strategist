import math, copy, random
import torch
def finite(t): return bool(torch.isfinite(t).all())
def demo(m): return witness(m)
def witness(m):
    buffer=[]
    for i in range(6):m.push(buffer,i,4)
    online=torch.nn.Linear(1,2,dtype=torch.float64)
    with torch.no_grad():online.weight.zero_();online.bias.copy_(torch.tensor([1.,2.]))
    target=m.make_target(online)
    with torch.no_grad():online.bias.copy_(torch.tensor([3.,4.]))
    before=target(torch.zeros((1,1),dtype=torch.float64)).detach().tolist()
    m.sync_target(target,online,2,2)
    return dict(buffer=buffer,target_before_sync=before,target_after_sync=target(torch.zeros((1,1),dtype=torch.float64)).detach().tolist(),samples=m.sample(buffer,8,random.Random(7)))

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

