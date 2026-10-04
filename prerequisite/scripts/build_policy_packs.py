"""Generate standalone M6 exercises; --write updates authored outputs."""
import argparse
import json
from build_catalog import LABS
from build_foundation_packs import CHECK_HELPERS, CHECK_MAIN, RUNNER
from build_policy_pages import CONTENT

TORCH_COMMON='''import math
import numpy as np
import torch
def vectors(*xs):
    if not xs or any(x.ndim!=1 or not x.numel() or not torch.isfinite(x).all() for x in xs) or any(x.shape!=xs[0].shape for x in xs):
        raise ValueError("matching nonempty finite vectors required")
def clip_value(epsilon):
    if not math.isfinite(epsilon) or not 0<=epsilon<1:raise ValueError("epsilon in [0,1) required")
'''
SPECS={
'p9-reinforce':dict(signatures=['probabilities(logits, legal=None)','reinforce_loss(logits, actions, returns, legal=None)'],functions='''def probabilities(logits, legal=None):
    if logits.ndim!=2 or not logits.numel() or not torch.isfinite(logits).all():raise ValueError("finite logits[B,A] required")
    if legal is not None:
        if legal.shape!=logits.shape or legal.dtype!=torch.bool or not legal.any(1).all():raise ValueError("valid boolean legal mask required")
        logits=logits.masked_fill(~legal,-torch.inf)
    return torch.softmax(logits,dim=1)
def reinforce_loss(logits, actions, returns, legal=None):
    probabilities(logits,legal)
    if actions.shape!=(len(logits),) or actions.dtype!=torch.long or returns.shape!=actions.shape or not torch.isfinite(returns).all():raise ValueError("invalid samples")
    if ((actions<0)|(actions>=logits.shape[1])).any():raise ValueError("invalid action")
    if legal is not None and not legal[torch.arange(len(logits)),actions].all():raise ValueError("illegal action")
    masked=logits if legal is None else logits.masked_fill(~legal,-torch.inf)
    logs=torch.log_softmax(masked,dim=1)[torch.arange(len(logits)),actions]
    return -(logs*returns.detach()).mean()
''',broken='''def probabilities(logits, legal=None):return torch.softmax(logits,dim=1)
def reinforce_loss(logits, actions, returns, legal=None):
    return (torch.log_softmax(logits,dim=1)[torch.arange(len(logits)),actions]*returns).mean()
''',demo='''def demo(m):
    x=torch.zeros((1,2),dtype=torch.float64,requires_grad=True)
    loss=m.reinforce_loss(x,torch.tensor([0]),torch.tensor([2.],dtype=torch.float64));loss.backward()
    return dict(loss=float(loss.detach()),gradient=x.grad.tolist(),next_probability=m.probabilities(x.detach()-.1*x.grad).tolist())
''',checks='''def check(m):
    import torch
    d=torch.float64
    x=torch.zeros((1,2),dtype=d,requires_grad=True);r=torch.tensor([2.],dtype=d,requires_grad=True)
    loss=m.reinforce_loss(x,torch.tensor([0]),r);close(float(loss.detach()),2*math.log(2));loss.backward()
    close_list(x.grad[0].tolist(),[-1,1]);assert r.grad is None
    close(float(m.probabilities(x.detach()-.1*x.grad)[0,0]),.549833997312478)
    for action,ret in ((0,-2),(1,3),(1,-1)):
        z=torch.tensor([[.3,-.7]],dtype=d,requires_grad=True);p=torch.softmax(z.detach(),1)
        m.reinforce_loss(z,torch.tensor([action]),torch.tensor([float(ret)],dtype=d)).backward()
        oracle=p.clone();oracle[0,action]-=1;assert torch.allclose(z.grad,ret*oracle)
    mask=torch.tensor([[True,False,True]])
    close_list(m.probabilities(torch.zeros((1,3),dtype=d),mask)[0].tolist(),[.5,0,.5])
    rejects(lambda:m.probabilities(torch.zeros((1,2)),torch.zeros((1,2),dtype=torch.bool)))
    rejects(lambda:m.reinforce_loss(torch.zeros((1,3)),torch.tensor([1]),torch.ones(1),mask))
    rejects(lambda:m.probabilities(torch.tensor([[float('nan'),0]])))
    rejects(lambda:m.reinforce_loss(torch.zeros((1,2)),torch.tensor([2]),torch.ones(1)))
    # Stable log-softmax must not log an underflowed probability.
    close(float(m.reinforce_loss(torch.tensor([[1000.,-1000.]],dtype=d),torch.tensor([1]),torch.ones(1,dtype=d))),2000)
''',fixture={'gradient':[-1,1],'next_probability_A':.549833997312478}),
'p9-advantage':dict(signatures=['advantages(returns, values)','actor_loss(log_probs, advantage)','critic_loss(values, targets)'],functions='''def advantages(returns, values):
    vectors(returns,values)
    return (returns-values).detach()
def actor_loss(log_probs, advantage):
    vectors(log_probs,advantage)
    return -(log_probs*advantage.detach()).mean()
def critic_loss(values, targets):
    vectors(values,targets)
    return ((values-targets.detach())**2).mean()
''',broken='''def advantages(returns, values):return returns-values
def actor_loss(log_probs, advantage):return -(log_probs*advantage).mean()
def critic_loss(values, targets):return ((values-targets)**2).mean()
''',demo='''def demo(m):
    values=torch.tensor([5.,5.],requires_grad=True);a=m.advantages(torch.tensor([8.,2.]),values)
    return dict(advantages=a.tolist(),advantage_requires_grad=a.requires_grad)
''',checks='''def check(m):
    import torch
    d=torch.float64
    v=torch.tensor([5.,5.],dtype=d,requires_grad=True);r=torch.tensor([8.,2.],dtype=d,requires_grad=True)
    a=m.advantages(r,v);close_list(a.tolist(),[3,-3]);assert not a.requires_grad
    lp=torch.tensor([-.7,-.9],dtype=d,requires_grad=True)
    supplied=torch.tensor([3.,-3.],dtype=d,requires_grad=True)
    loss=m.actor_loss(lp,supplied);close(float(loss.detach()),-.3);loss.backward()
    close_list(lp.grad.tolist(),[-1.5,1.5]);assert supplied.grad is None and v.grad is None
    loss=m.critic_loss(v,r);close(float(loss.detach()),9);loss.backward()
    close_list(v.grad.tolist(),[-3,3]);assert r.grad is None
    for f in (m.advantages,m.actor_loss,m.critic_loss):
        rejects(lambda:f(torch.zeros(2),torch.zeros(3)))
        rejects(lambda:f(torch.tensor([float('nan')]),torch.zeros(1)))
        rejects(lambda:f(torch.zeros(0),torch.zeros(0)))
''',fixture={'advantages':[3,-3],'constant_baseline_score':[0,0],'action_dependent_baseline_score':[.25,-.25]}),
'p9-gae':dict(signatures=['gae(rewards, values, next_values, terminated, trace_continue, gamma=.9, lam=1)'],functions='''def gae(rewards, values, next_values, terminated, trace_continue, gamma=.9, lam=1):
    xs=[np.asarray(x) for x in (rewards,values,next_values,terminated,trace_continue)]
    r,v,n,t,c=xs
    if any(x.ndim!=1 or not x.size or x.shape!=r.shape for x in xs):raise ValueError("matching nonempty vectors required")
    if t.dtype!=bool or c.dtype!=bool or np.any(t & c):raise ValueError("invalid boundary flags")
    if not all(np.isfinite(x).all() for x in (r,v,n)) or not all(math.isfinite(x) and 0<=x<=1 for x in (gamma,lam)):raise ValueError("finite data and discounts in [0,1] required")
    delta=r+gamma*np.where(t,0,n)-v
    a=np.zeros(len(r),dtype=float);tail=0.
    for i in range(len(r)-1,-1,-1):
        tail=delta[i]+gamma*lam*c[i]*tail;a[i]=tail
    return a,a+v
''',broken='''def gae(rewards, values, next_values, terminated, trace_continue, gamma=.9, lam=1):
    r,v,n=np.asarray(rewards),np.asarray(values),np.asarray(next_values)
    delta=r+gamma*n-v;a=np.zeros(len(r));tail=0.
    for i in range(len(r)-1,-1,-1):tail=delta[i]+gamma*lam*tail;a[i]=tail
    return a,a+v
''',demo='''def demo(m):
    a,target=m.gae([1,2],[.5,1],[1,3],np.array([False,True]),np.array([True,False]))
    return dict(advantages=a.tolist(),targets=target.tolist())
''',checks='''def check(m):
    import numpy as np
    flags=lambda x:np.array(x,dtype=bool)
    for terminal,lam,expected in ((True,1,[2.3,1]),(True,0,[1.4,1]),(False,1,[4.73,3.7]),(False,.5,[3.065,3.7])):
        a,t=m.gae([1,2],[.5,1],[1,3],flags([False,terminal]),flags([True,False]),lam=lam)
        close_list(a,expected);close_list(t,np.array(expected)+[.5,1])
    a,_=m.gae([1,2,100],[.5,1,0],[1,3,999],flags([False,False,True]),flags([True,False,False]))
    close_list(a,[4.73,3.7,100]) # reset reward must not leak backward
    a,_=m.gae([1],[.5],[3],flags([False]),flags([True]));close_list(a,[3.2])
    rejects(lambda:m.gae([1],[0],[0],flags([True]),flags([True])))
    rejects(lambda:m.gae([1],[0],[0],[0],[0]))
    rejects(lambda:m.gae([1],[0],[float('nan')],flags([False]),flags([False])))
    rejects(lambda:m.gae([1],[0],[0],flags([False]),flags([False]),lam=2))
''',fixture={'terminal':[2.3,1],'continuing':[4.73,3.7],'continuing_lambda_half':[3.065,3.7]}),
'p9-ppo':dict(signatures=['frozen(log_probs)','ppo_loss(new_log_probs, old_log_probs, advantage, epsilon=.2)','diagnostics(new_log_probs, old_log_probs, advantage, epsilon=.2)'],functions='''def frozen(log_probs):
    vectors(log_probs)
    return log_probs.detach().clone()
def ratio_data(new_log_probs, old_log_probs, advantage, epsilon):
    vectors(new_log_probs,old_log_probs,advantage);clip_value(epsilon)
    lr=new_log_probs-old_log_probs.detach();ratio=lr.exp()
    if not torch.isfinite(ratio).all():raise ValueError("ratio overflow")
    return ratio,lr,advantage.detach()
def ppo_loss(new_log_probs, old_log_probs, advantage, epsilon=.2):
    r,lr,a=ratio_data(new_log_probs,old_log_probs,advantage,epsilon)
    return -torch.minimum(r*a,r.clamp(1-epsilon,1+epsilon)*a).mean()
def diagnostics(new_log_probs, old_log_probs, advantage, epsilon=.2):
    r,lr,a=ratio_data(new_log_probs,old_log_probs,advantage,epsilon)
    return dict(ratios=r.detach(),clip_fraction=float(((r-1).abs()>epsilon).double().mean()),approx_kl=float((r-1-lr).detach().mean()))
''',broken='''def frozen(log_probs):return log_probs.detach()
def ppo_loss(new_log_probs, old_log_probs, advantage, epsilon=.2):
    return -((new_log_probs-old_log_probs).exp().clamp(1-epsilon,1+epsilon)*advantage).mean()
def diagnostics(new_log_probs, old_log_probs, advantage, epsilon=.2):
    r=(new_log_probs-old_log_probs).exp()
    return dict(ratios=r,clip_fraction=0.,approx_kl=0.)
''',demo='''def demo(m):
    r=torch.tensor([1.3,.7,.7,1.3],dtype=torch.float64);a=torch.tensor([1.,1.,-1.,-1.],dtype=torch.float64)
    return dict(loss=float(m.ppo_loss(r.log(),torch.zeros(4,dtype=torch.float64),a)),objectives=[-float(m.ppo_loss(r[i:i+1].log(),torch.zeros(1,dtype=torch.float64),a[i:i+1])) for i in range(4)])
''',checks='''def check(m):
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
''',fixture={'epsilon':.2,'ratios':[1.3,.7,.7,1.3],'advantages':[1,1,-1,-1],'objectives':[1.2,.7,-.8,-1.3]})}

def outputs():
    result={}
    for key,s in SPECS.items():
        folder=LABS/'downloads'/key
        common=('import math\nimport numpy as np\n' if key=='p9-gae' else TORCH_COMMON)+s['demo']+RUNNER
        prefix='from exercise_common import *\n\n';suffix='\nif __name__=="__main__":\n    import sys\n    run(sys.modules[__name__])\n'
        starter='\n'.join('def '+sig+':\n    raise NotImplementedError("Complete '+sig.split('(')[0]+'")\n' for sig in s['signatures'])
        files={'exercise_common.py':common,'solution.py':prefix+s['functions']+suffix,'broken.py':prefix+s['broken']+suffix,'starter.py':prefix+starter+suffix,'checks.py':CHECK_HELPERS+s['checks']+CHECK_MAIN,'fixtures.json':json.dumps(s['fixture'],indent=2)+'\n','requirements.txt':'numpy>=1.26,<3\n'+('torch>=2.2,<3\n' if key!='p9-gae' else '')}
        template=__import__('pathlib').Path(__file__).parent/'policy_templates'/f'{key}-compare.py'
        if template.exists():files['compare.py']=template.read_text(encoding='utf-8')
        files['README.md']=f'''# {key}

Standalone Python 3.10+ exercise. Extract this folder anywhere. All tensors use CPU.
Tested with Python 3.12.7, NumPy 2.5.1 and PyTorch 2.13.0+cpu.

```text
python -m pip install -r requirements.txt
python broken.py
python checks.py --candidate broken.py
python starter.py
python checks.py --candidate starter.py
```

Broken code runs but fails checks. Starter reports Exercise incomplete until implemented.
Checks import only the chosen candidate and helpers; they never import solution.py.
Open solution.py only when you want the reference. Invalid contract inputs raise ValueError.
Hand witnesses use float64 and tolerance 1e-9. Stochastic scores are not pass/fail gates.

{CONTENT[key]['task']}

{CONTENT[key]['reflect']}

{('Optional: python compare.py --candidate starter.py --integration. First install gymnasium stable-baselines3 sb3-contrib. Run in a terminal; the Windows main guard is included.' if key=='p9-ppo' else 'Optional: python compare.py --candidate starter.py --seed 7.' if key=='p9-reinforce' else '')}
'''
        for name,source in files.items():result[folder/name]=source
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    for path,source in outputs().items():
        if args.write:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source,encoding='utf-8')
        elif not path.exists() or path.read_text(encoding='utf-8')!=source:raise SystemExit(f'Stale M6 pack: {path}')
    print('Four M6 packs '+('generated.' if args.write else 'are current.'))
