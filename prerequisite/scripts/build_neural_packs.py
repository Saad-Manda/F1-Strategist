"""Author standalone M4 CPU packs. Use --write to regenerate."""
import argparse
import json
from build_catalog import LABS
from build_foundation_packs import CHECK_HELPERS, CHECK_MAIN, RUNNER

COMMON = '''import math, copy, random
import torch
def finite(t): return bool(torch.isfinite(t).all())
def demo(m): return witness(m)
'''
SPECS = {
'p5-network': {
 'signatures':['predict(x, weight, bias)', 'mse(prediction, labels)', 'train_step(model, optimizer, x, labels)'],
 'functions':'''def predict(x, weight, bias):
    if x.ndim!=2 or weight.ndim!=2 or bias.ndim!=1 or x.shape[1]!=weight.shape[1] or weight.shape[0]!=len(bias):
        raise ValueError("expected x[B,D], weight[A,D], bias[A]")
    if not all(finite(t) for t in (x,weight,bias)): raise ValueError("finite inputs required")
    return x @ weight.T + bias
def mse(prediction, labels):
    if prediction.shape!=labels.shape or not prediction.numel() or not all(finite(t) for t in (prediction,labels)):
        raise ValueError("matching nonempty finite tensors required")
    return ((prediction-labels)**2).mean()
def train_step(model, optimizer, x, labels):
    optimizer.zero_grad()
    loss=mse(model(x),labels)
    loss.backward()
    optimizer.step()
    return float(loss.detach())
''',
 'broken':'''def predict(x, weight, bias): return x @ weight.T + bias
def mse(prediction, labels): return ((prediction-labels)**2).sum()
def train_step(model, optimizer, x, labels):
    loss=mse(model(x),labels)
    loss.backward()
    optimizer.step()
    return float(loss.detach())
''',
 'common':'''def witness(m):
    x=torch.tensor([[.25]],dtype=torch.float64)
    w=torch.zeros((2,1),dtype=torch.float64,requires_grad=True);b=torch.zeros(2,dtype=torch.float64,requires_grad=True)
    prediction=m.predict(x,w,b)
    loss=m.mse(prediction,torch.tensor([[.25,.75]],dtype=torch.float64));loss.backward()
    return dict(prediction=prediction.detach().tolist(),loss=float(loss.detach()),weight_gradient=w.grad.tolist(),bias_gradient=b.grad.tolist())
''',
 'checks':'''def check(m):
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
''',
 'fixtures':dict(x=.25,labels=[.25,.75],mean_loss=.3125,weight_gradient=[-.0625,-.1875],bias_gradient=[-.25,-.75])},
'p5-stability': {
 'signatures':['push(buffer, item, capacity)', 'sample(buffer, batch_size, rng)', 'make_target(online)', 'sync_target(target, online, step, interval)', 'targets(target, next_states, rewards, terminated, gamma)'],
 'functions':'''def push(buffer, item, capacity):
    if type(capacity) is not int or capacity<1:raise ValueError("positive integer capacity required")
    buffer.append(item)
    del buffer[:-capacity]
def sample(buffer, batch_size, rng):
    if not buffer or type(batch_size) is not int or batch_size<1:raise ValueError("nonempty buffer and positive batch size required")
    return [rng.choice(buffer) for _ in range(batch_size)]
def make_target(online):
    target=copy.deepcopy(online).eval()
    for p in target.parameters():p.requires_grad_(False)
    return target
def sync_target(target, online, step, interval):
    if type(step) is not int or step<1 or type(interval) is not int or interval<1:raise ValueError("positive integer step/interval required")
    if step%interval==0:target.load_state_dict(online.state_dict())
def targets(target, next_states, rewards, terminated, gamma):
    if not math.isfinite(gamma) or not 0<=gamma<=1:raise ValueError("gamma in [0,1] required")
    if rewards.ndim!=1 or terminated.shape!=rewards.shape or next_states.shape[0]!=len(rewards) or terminated.dtype!=torch.bool:
        raise ValueError("invalid batch shapes or flags")
    if not all(finite(t) for t in (next_states,rewards)):raise ValueError("finite batch required")
    with torch.no_grad():
        values=target(next_states).max(dim=1).values
        return rewards+gamma*torch.where(terminated,torch.zeros_like(values),values)
''',
 'broken':'''def push(buffer, item, capacity):
    buffer.append(item)
    if len(buffer)>capacity:buffer.pop()
def sample(buffer, batch_size, rng):return [buffer[-1]]*batch_size
def make_target(online):return online
def sync_target(target, online, step, interval):target.load_state_dict(online.state_dict())
def targets(target, next_states, rewards, terminated, gamma):return rewards+gamma*target(next_states).max(dim=1).values
''',
 'common':'''def witness(m):
    buffer=[]
    for i in range(6):m.push(buffer,i,4)
    online=torch.nn.Linear(1,2,dtype=torch.float64)
    with torch.no_grad():online.weight.zero_();online.bias.copy_(torch.tensor([1.,2.]))
    target=m.make_target(online)
    with torch.no_grad():online.bias.copy_(torch.tensor([3.,4.]))
    before=target(torch.zeros((1,1),dtype=torch.float64)).detach().tolist()
    m.sync_target(target,online,2,2)
    return dict(buffer=buffer,target_before_sync=before,target_after_sync=target(torch.zeros((1,1),dtype=torch.float64)).detach().tolist(),samples=m.sample(buffer,8,random.Random(7)))
''',
 'checks':'''def check(m):
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
''',
 'fixtures':dict(capacity=4,retained=[2,3,4,5],probability=.25,target_before_sync=[1,2],target_after_sync=[3,4])},
'p5-double-dueling': {
 'signatures':['double_targets(online_values, target_values, rewards, terminated, legal, gamma)', 'dueling(value, advantage)'],
 'functions':'''def double_targets(online_values, target_values, rewards, terminated, legal, gamma):
    if not math.isfinite(gamma) or not 0<=gamma<=1:raise ValueError("gamma in [0,1] required")
    if online_values.ndim!=2 or target_values.shape!=online_values.shape or legal.shape!=online_values.shape or rewards.shape!=(online_values.shape[0],) or terminated.shape!=rewards.shape or legal.dtype!=torch.bool or terminated.dtype!=torch.bool:raise ValueError("invalid batch shapes or flags")
    if not all(finite(t) for t in (online_values,target_values,rewards)):raise ValueError("finite values required")
    active=~terminated
    if bool((~legal[active].any(dim=1)).any()):raise ValueError("no legal next action")
    with torch.no_grad():
        result=rewards.clone()
        selected=online_values[active].masked_fill(~legal[active],-torch.inf).argmax(dim=1)
        result[active]+=gamma*target_values[active].gather(1,selected[:,None]).squeeze(1)
        return result
def dueling(value, advantage):
    if advantage.ndim!=2 or advantage.shape[1]==0 or value.shape!=(advantage.shape[0],1) or not all(finite(t) for t in (value,advantage)):raise ValueError("expected V[B,1], A[B,actions], finite")
    return value+advantage-advantage.mean(dim=1,keepdim=True)
''',
 'broken':'''def double_targets(online_values, target_values, rewards, terminated, legal, gamma):return rewards+gamma*target_values.max(dim=1).values
def dueling(value, advantage):return value+advantage
''',
 'common':'''def witness(m):
    online=torch.tensor([[5.,4.,100.]],dtype=torch.float64);target=torch.tensor([[1.,7.,99.]],dtype=torch.float64)
    return dict(double_target=m.double_targets(online,target,torch.tensor([1.],dtype=torch.float64),torch.tensor([False]),torch.tensor([[True,True,False]]),.5).tolist(),dueling=m.dueling(torch.tensor([[2.]],dtype=torch.float64),torch.tensor([[1.,3.]],dtype=torch.float64)).tolist())
''',
 'checks':'''def check(m):
    import torch
    d=torch.float64
    o=torch.tensor([[5.,4.,100.],[2.,9.,0.],[1.,2.,3.]],dtype=d,requires_grad=True)
    t=torch.tensor([[1.,7.,99.],[8.,3.,99.],[4.,5.,6.]],dtype=d,requires_grad=True)
    r=torch.tensor([1.,-2.,4.],dtype=d);done=torch.tensor([False,False,True]);legal=torch.tensor([[True,True,False],[True,True,False],[False,False,False]])
    y=m.double_targets(o,t,r,done,legal,.5);close_list(y.tolist(),[1.5,-.5,4]);assert y.shape==(3,) and not y.requires_grad
    close_list(m.double_targets(o,t,r,done,legal,0).tolist(),r.tolist())
    rejects(lambda:m.double_targets(o,t,r,torch.tensor([False,False,False]),legal,.5))
    v=torch.tensor([[2.],[-1.]],dtype=d,requires_grad=True);a=torch.tensor([[1.,3.],[8.,-2.]],dtype=d,requires_grad=True)
    q=m.dueling(v,a);assert q.shape==(2,2)
    assert torch.allclose(q,torch.tensor([[1.,3.],[4.,-6.]],dtype=d))
    assert torch.allclose(q,m.dueling(v,a+torch.tensor([[10.],[-7.]],dtype=d)))
    q[:,0].sum().backward();assert v.grad is not None and a.grad is not None
    rejects(lambda:m.dueling(torch.ones(2),a))
''',
 'fixtures':dict(online=[5,4,100],target=[1,7,99],legal=[True,True,False],double_target=1.5,vanilla_target=4.5,value=2,advantage=[1,3],q=[1,3])},
'p5-per': {
 'signatures':['distribution(raw_priorities, alpha, beta)', 'new_priority(raw_priorities)', 'update_priority(td_error, epsilon=1e-6)', 'weighted_loss(losses, weights)'],
 'functions':'''def distribution(raw_priorities, alpha, beta):
    p=np.asarray(raw_priorities,dtype=float)
    if p.ndim!=1 or not len(p) or not np.isfinite(p).all() or (p<=0).any() or not math.isfinite(alpha) or not 0<=alpha<=1 or not math.isfinite(beta) or not 0<=beta<=1:raise ValueError("positive finite priorities, alpha/beta in [0,1] required")
    masses=p**alpha;probabilities=masses/masses.sum()
    weights=(len(p)*probabilities)**(-beta)
    return probabilities,weights/weights.max()
def new_priority(raw_priorities):
    p=np.asarray(raw_priorities,dtype=float)
    if p.ndim!=1 or not np.isfinite(p).all() or (p<=0).any():raise ValueError("invalid raw priorities")
    return float(p.max()) if len(p) else 1.
def update_priority(td_error, epsilon=1e-6):
    if not math.isfinite(td_error) or not math.isfinite(epsilon) or epsilon<=0:raise ValueError("finite error and positive epsilon required")
    return abs(td_error)+epsilon
def weighted_loss(losses, weights):
    losses=np.asarray(losses,dtype=float);weights=np.asarray(weights,dtype=float)
    if losses.ndim!=1 or not len(losses) or weights.shape!=losses.shape or not np.isfinite(losses).all() or not np.isfinite(weights).all() or (losses<0).any() or (weights<0).any() or (weights>1).any():raise ValueError("invalid losses/weights")
    return float(np.mean(weights*losses))
''',
 'broken':'''def distribution(raw_priorities, alpha, beta):
    masses=np.asarray(raw_priorities,dtype=float)**alpha
    return masses/masses.sum(),np.ones(len(masses))
def new_priority(raw_priorities):return float(np.sqrt(max(raw_priorities))) if len(raw_priorities) else 1.
def update_priority(td_error, epsilon=1e-6):return td_error
def weighted_loss(losses, weights):return float(np.sum(np.asarray(losses)*weights)/np.sum(weights))
''',
 'common':'''import math
import numpy as np
def demo(m):
    p,w=m.distribution([1,4,9],.5,1)
    return dict(probabilities=p.tolist(),weights=w.tolist(),new_raw=m.new_priority([1,4,9]),weighted_loss=m.weighted_loss([1,4,9],w))
''',
 'checks':'''def check(m):
    import numpy as np
    p,w=m.distribution([1,4,9],.5,1);close_list(p,[1/6,1/3,1/2]);close_list(w,[1,.5,1/3]);close(m.weighted_loss([1,4,9],w),2)
    close(m.new_priority([1,4,9]),9);close(m.new_priority([]),1)
    pp,_=m.distribution([1,4,9,m.new_priority([1,4,9])],.5,1);close_list(pp,[1/9,2/9,3/9,3/9])
    for alpha in (0,.3,1):
        for beta in (0,.7,1):
            raw=[.25,2,7,11];p,w=m.distribution(raw,alpha,beta)
            expected=np.power(raw,alpha);expected/=sum(expected);close_list(p,expected)
            ew=np.power(4*expected,-beta);ew/=max(ew);close_list(w,ew)
    close(m.update_priority(-3),3.000001);close(m.update_priority(0),.000001)
    rejects(lambda:m.distribution([0,1],.5,1));rejects(lambda:m.distribution([1,float('nan')],.5,1))
    rejects(lambda:m.distribution([1],-1,1));rejects(lambda:m.weighted_loss([1,2],[1]))
    for seed in (7,19,31):
        p,_=m.distribution([1,4,9],.5,1);draws=np.random.default_rng(seed).choice(3,10000,p=p)
        assert np.max(np.abs(np.bincount(draws,minlength=3)/10000-p))<.02
''',
 'fixtures':dict(raw=[1,4,9],alpha=.5,beta=1,probabilities=[1/6,1/3,1/2],weights=[1,.5,1/3],weighted_loss=2)}
}

def outputs():
    from build_neural_pages import CONTENT
    result={}
    for key,s in SPECS.items():
        per=key=='p5-per';folder=LABS/'downloads'/key
        common=(s['common'] if per else COMMON+s['common'])+'\n'+RUNNER
        prefix='"""Standalone CPU exercise. See README.md."""\nfrom exercise_common import *\n\n'
        suffix='\nif __name__=="__main__":\n    import sys\n    run(sys.modules[__name__])\n'
        starter='\n\n'.join(f'def {sig}:\n    # TODO: follow README.md.\n    raise NotImplementedError("Complete {sig.split("(")[0]}")' for sig in s['signatures'])+'\n'
        files={'exercise_common.py':common,'solution.py':prefix+s['functions']+suffix,'broken.py':prefix+s['broken']+suffix,'starter.py':prefix+starter+suffix,'checks.py':CHECK_HELPERS+s['checks']+CHECK_MAIN,'fixtures.json':json.dumps(s['fixtures'],indent=2)+'\n','requirements.txt':'numpy>=1.26,<3\n'+('torch>=2.2,<3\n' if not per else '')}
        compare_path=__import__('pathlib').Path(__file__).resolve().parent/'neural_templates'/f'{key}-compare.py'
        if compare_path.exists():files['compare.py']=compare_path.read_text(encoding='utf-8')
        signatures='\n'.join('- `'+sig+'`' for sig in s['signatures'])
        files['README.md']=f'''# {key}

Python 3.10+; NumPy{' and CPU PyTorch' if not per else ''}.
Tested: Python 3.12.7, NumPy 2.5.1{', PyTorch 2.13.0+cpu' if not per else ''}.
Extract anywhere; no repository or backend is required. Use an existing PyTorch
installation or install requirements. All tensors run on CPU.

```text
python -m pip install -r requirements.txt
python broken.py
python checks.py --candidate broken.py
python starter.py
python checks.py --candidate starter.py
```

The broken candidate runs and deliberately fails checks. The untouched starter
reports Exercise incomplete. Repair a copy or implement TODOs; pass its filename
to --candidate. Checks import that candidate and helpers, never solution.py.
Reference solution.py is optional help: open only when you request it.

## Contract

{CONTENT[key]['task']}

{signatures}

Float64 tensors (NumPy float arrays for PER) make hand witnesses reproducible.
Invalid inputs described above raise ValueError. Hand examples use tolerance 1e-9;
analytic SGD checks use 1e-10. Sampling checks use 10,000 draws for each seed
7,19,31 with frequency tolerance .02. Sampling is with replacement; Python and
browser RNGs do not generate identical traces. Scores are not correctness gates.

{('After implementing: `python compare.py --candidate starter.py --seed 7`. Reports include budgets and versions. Try other seeds.' if 'compare.py' in files else '')}

Explain and transfer: {CONTENT[key]['reflect']}
'''
        for name,source in files.items():result[folder/name]=source
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');a=p.parse_args()
    for path,source in outputs().items():
        if a.write:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source,encoding='utf-8')
        elif not path.exists() or path.read_text(encoding='utf-8')!=source:raise SystemExit(f'Stale M4 pack: {path}')
    print('Four M4 packs '+('generated.' if a.write else 'are current.'))
