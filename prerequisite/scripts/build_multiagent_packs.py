"""Author six standalone M5 packs with independent mathematical and lifecycle checks."""
import argparse,json
from build_catalog import LABS,ROOT
from build_foundation_packs import CHECK_HELPERS,CHECK_MAIN,RUNNER,VALIDATION

GAME='''MATRIX=((0,-1,1),(1,0,-1),(-1,1,0))
def action(a):
    if type(a) is not int or a not in (0,1,2):raise ValueError("action must be integer 0,1,2")
def policy(p):
    if len(p)!=3:raise ValueError("three probabilities required")
    validate_distribution(p)
validate_action=action
validate_policy=policy
'''
SPECS={
'p6-credit':dict(
 signatures=['joint_step(actions)','contributions(actions)'],
 functions='''def joint_step(actions):
    team_actions(actions)
    reward=2*actions['A']+actions['B']
    return dict(rewards={'A':reward,'B':reward},terminations={'A':True,'B':True},truncations={'A':False,'B':False},agents=[])
def contributions(actions):
    team_actions(actions)
    total=joint_step(actions)['rewards']['A'];result={}
    for agent in ('A','B'):
        counterfactual=dict(actions);counterfactual[agent]=0
        result[agent]=total-joint_step(counterfactual)['rewards']['A']
    return result
''',
 broken='''def joint_step(actions):
    reward=2*actions['A']+actions['B']
    return dict(rewards={'A':reward,'B':reward},terminations={'A':True,'B':True},truncations={'A':False,'B':False},agents=[])
def contributions(actions):return joint_step(actions)['rewards']
''',
 common='''def team_actions(actions):
    if set(actions)!= {'A','B'} or any(type(a) is not int or a not in (0,1) for a in actions.values()):raise ValueError("exactly A/B integer actions 0 or 1 required")
def demo(m):return dict(joint=m.joint_step({'A':1,'B':1}),differences=m.contributions({'A':1,'B':1}))
''',
 checks='''def check(m):
    for a in (0,1):
        for b in (0,1):
            actions={'A':a,'B':b};r=m.joint_step(actions)
            assert r['rewards']=={'A':2*a+b,'B':2*a+b}
            assert r['terminations']=={'A':True,'B':True} and r['truncations']=={'A':False,'B':False} and r['agents']==[]
            assert m.contributions(actions)=={'A':2*a,'B':b}
            assert actions=={'A':a,'B':b},"inputs were mutated"
    for invalid in ({'A':1},{'A':1,'B':1,'C':0},{'A':2,'B':0},{'A':True,'B':0}):
        rejects(lambda:m.joint_step(invalid));rejects(lambda:m.contributions(invalid))
''',fixtures=dict(shared=3,differences=dict(A=2,B=1))),
'p6-shaping':dict(
 signatures=['shaped_return(rewards, potentials, gamma, shaping_gamma=None)','route_returns(gamma=1, failure_potential=0, shaping_gamma=None)'],
 functions='''def shaped_return(rewards, potentials, gamma, shaping_gamma=None):
    sg=gamma if shaping_gamma is None else shaping_gamma
    if len(potentials)!=len(rewards)+1 or any(not math.isfinite(v) for v in [*rewards,*potentials,gamma,sg]) or not 0<=gamma<=1 or not 0<=sg<=1:raise ValueError("finite rewards/potentials and valid discounts required")
    return sum(gamma**i*(r+sg*potentials[i+1]-potentials[i]) for i,r in enumerate(rewards))
def route_returns(gamma=1, failure_potential=0, shaping_gamma=None):
    result=[]
    for name,rewards,potentials,bonus in routes(failure_potential):
        shaped=shaped_return(rewards,potentials,gamma,shaping_gamma)
        base=sum(gamma**i*r for i,r in enumerate(rewards))
        result.append(dict(route=name,base=base,bonus=sum(gamma**i*r for i,r in enumerate(bonus)),shaped=shaped,shift=shaped-base,boundary=gamma**len(rewards)*potentials[-1]))
    return result
''',
 broken='''def shaped_return(rewards, potentials, gamma, shaping_gamma=None):
    return sum(gamma**i*(r+potentials[i+1]-potentials[i]) for i,r in enumerate(rewards))
def route_returns(gamma=1, failure_potential=0, shaping_gamma=None):
    result=[]
    for name,rewards,potentials,bonus in routes(failure_potential):
        base=sum(gamma**i*r for i,r in enumerate(rewards));shaped=shaped_return(rewards,potentials,gamma,shaping_gamma)
        result.append(dict(route=name,base=base,bonus=sum(gamma**i*r for i,r in enumerate(bonus)),shaped=shaped,shift=shaped-base,boundary=0))
    return result
''',
 common='''def routes(failure_potential):
    return [('DIRECT',[3],[2,0],[3]),('VIA+FINISH',[0,4],[2,1,0],[0,4]),('VIA+WAIT',[0,0],[2,1,failure_potential],[0,5])]
def demo(m):return {'gamma_1':m.route_returns(),'gamma_half':m.route_returns(.5),'nonzero_failure':m.route_returns(1,10)}
''',
 checks='''def check(m):
    rows=m.route_returns();close_list([r['base'] for r in rows],[3,4,0]);close_list([r['bonus'] for r in rows],[3,4,5]);close_list([r['shaped'] for r in rows],[1,2,-2])
    # Independent telescoping oracle across lengths, discounts and endpoints.
    for rewards,potentials in [([3],[2,0]),([0,4],[2,1,0]),([1,-2,5],[3,8,-1,7]),([],[2])]:
        for gamma in (0,.3,.5,1):
            base=sum(gamma**i*r for i,r in enumerate(rewards))
            close(m.shaped_return(rewards,potentials,gamma),base-potentials[0]+gamma**len(rewards)*potentials[-1])
    for gamma in (.5,1):
        for end in (0,10):
            rows=m.route_returns(gamma,end)
            for row in rows:close(row['shift'],-2+row['boundary'])
    mismatch=m.shaped_return([0,4],[2,1,0],.5,1);close(mismatch,0.5)
    rejects(lambda:m.shaped_return([1],[2],1));rejects(lambda:m.shaped_return([1],[2,0],1.2));rejects(lambda:m.shaped_return([float('nan')],[2,0],1))
''',fixtures=dict(base=[3,4,0],bonus=[3,4,5],shaped=[1,2,-2])),
'p6-opponent':dict(
 signatures=['lane_reward(action, occupied, blocking=True)','expected_lane(p, blocking=True)','sample_lane(p, blocking, samples, seed)'],
 functions='''def lane_reward(action, occupied, blocking=True):
    if action not in ('CROSS','WAIT') or type(occupied) is not bool or type(blocking) is not bool:raise ValueError("invalid action/flags")
    return 0 if action=='WAIT' else (-1 if blocking and occupied else 1)
def expected_lane(p, blocking=True):
    lane_settings(p,blocking)
    return {'CROSS':1-2*p if blocking else 1,'WAIT':0}
def sample_lane(p, blocking, samples, seed):
    lane_settings(p,blocking)
    if type(samples) is not int or samples<1:raise ValueError("positive sample count required")
    rng=random.Random(seed);occupied=[rng.random()<p for _ in range(samples)]
    return dict(occupied_fraction=sum(occupied)/samples,cross_mean=sum(lane_reward('CROSS',o,blocking) for o in occupied)/samples,wait_mean=0)
''',
 broken='''def lane_reward(action, occupied, blocking=True):return 0 if action=='WAIT' else 1
def expected_lane(p, blocking=True):return {'CROSS':1,'WAIT':0}
def sample_lane(p, blocking, samples, seed):
    rng=random.Random(seed);occupied=[rng.random()<p for _ in range(samples)]
    return dict(occupied_fraction=sum(occupied)/samples,cross_mean=1,wait_mean=0)
''',
 common='''import random
def lane_settings(p,blocking):
    if not math.isfinite(p) or not 0<=p<=1 or type(blocking) is not bool:raise ValueError("p in [0,1] and boolean blocking required")
def demo(m):return dict(low=m.expected_lane(.2),high=m.expected_lane(.8),disconnected=m.expected_lane(.8,False),samples=m.sample_lane(.2,True,1000,7))
''',
 checks='''def check(m):
    close(m.expected_lane(.2)['CROSS'],.6);close(m.expected_lane(.8)['CROSS'],-.6)
    for blocked in (False,True):
        for enabled in (False,True):
            assert m.lane_reward('CROSS',blocked,enabled)==(-1 if blocked and enabled else 1)
            assert m.lane_reward('WAIT',blocked,enabled)==0
    for p in (0,.2,.8,1):
        for seed in (7,19,31):
            on=m.sample_lane(p,True,10000,seed);off=m.sample_lane(p,False,10000,seed)
            close(on['occupied_fraction'],off['occupied_fraction']);close(on['cross_mean'],1-2*on['occupied_fraction'])
            close(off['cross_mean'],1);assert abs(on['occupied_fraction']-p)<.02
            assert on==m.sample_lane(p,True,10000,seed)
    rejects(lambda:m.expected_lane(-.1));rejects(lambda:m.lane_reward('RUN',False));rejects(lambda:m.sample_lane(.2,True,0,7))
''',fixtures=dict(low=.6,high=-.6,disconnected=1)),
'p8-game':dict(
 signatures=['payoff(learner, opponent)','expected_payoff(policy, opponent)','action_update(values, action, reward, alpha)','best_response(opponent)'],
 functions='''def payoff(learner, opponent):
    action(learner);action(opponent)
    return MATRIX[learner][opponent]
def expected_payoff(policy, opponent):
    validate_policy(policy);validate_policy(opponent)
    return sum(policy[i]*opponent[j]*payoff(i,j) for i in range(3) for j in range(3))
def action_update(values, action, reward, alpha):
    validate_action(action)
    if len(values)!=3 or any(not math.isfinite(v) for v in [*values,reward,alpha]) or not 0<=alpha<=1:raise ValueError("finite values and alpha in [0,1] required")
    result=list(values);result[action]+=alpha*(reward-result[action])
    return result
def best_response(opponent):
    policy(opponent)
    values=[sum(MATRIX[i][j]*opponent[j] for j in range(3)) for i in range(3)]
    return [i for i,v in enumerate(values) if math.isclose(v,max(values),abs_tol=1e-12)]
''',
 broken='''def payoff(learner, opponent):return MATRIX[opponent][learner]
def expected_payoff(policy, opponent):return sum(policy[i]*opponent[j]*payoff(i,j) for i in range(3) for j in range(3))
def action_update(values, action, reward, alpha):return [v+alpha*(reward-v) for v in values]
def best_response(opponent):return [0]
''',
 common=GAME+'''def demo(m):return dict(paper_rock=m.payoff(1,0),paper_scissors=m.payoff(1,2),mixed=m.expected_payoff([0,1,0],[.5,.25,.25]),uniform=[m.expected_payoff([1/3]*3,[int(j==i) for j in range(3)]) for i in range(3)])
''',
 checks='''def check(m):
    for i in range(3):
        for j in range(3):
            # Modular winner oracle, independent of stored MATRIX.
            expected=0 if i==j else (1 if (i-j)%3==1 else -1)
            assert m.payoff(i,j)==expected
    close(m.expected_payoff([0,1,0],[.5,.25,.25]),.25)
    for j in range(3):
        pure=[int(i==j) for i in range(3)]
        close(m.expected_payoff([1/3]*3,pure),0);assert m.best_response(pure)==[(j+1)%3]
    assert set(m.best_response([1/3]*3))=={0,1,2}
    values=[1.,2.,3.];close_list(m.action_update(values,1,-1,.5),[1,.5,3]);assert values==[1,2,3]
    rejects(lambda:m.expected_payoff([1,1,1],[1,0,0]));rejects(lambda:m.payoff(3,0));rejects(lambda:m.action_update(values,0,1,1.1))
''',fixtures=dict(paper_rock=1,paper_scissors=-1,mixed=.25,uniform=[0,0,0])),
'p8-pool':dict(
 signatures=['snapshot(policy)','add_snapshot(pool, policy, capacity)','pool_probabilities(weights)','sample_indices(weights, count, seed)','coverage(policy)'],
 functions='''def snapshot(policy):
    validate_policy(policy)
    result=np.array(policy,dtype=float,copy=True);result.setflags(write=False)
    return result
def add_snapshot(pool, policy, capacity):
    if type(capacity) is not int or capacity<1:raise ValueError("positive capacity required")
    return [*pool,snapshot(policy)][-capacity:]
def pool_probabilities(weights):
    w=np.asarray(weights,dtype=float)
    if w.ndim!=1 or not len(w) or not np.isfinite(w).all() or (w<=0).any():raise ValueError("positive finite weights required")
    scaled=w/w.max()
    return scaled/scaled.sum()
def sample_indices(weights, count, seed):
    if type(count) is not int or count<1:raise ValueError("positive sample count required")
    p=pool_probabilities(weights)
    return np.random.default_rng(seed).choice(len(p),size=count,p=p)
def coverage(policy):
    validate_policy(policy)
    return [sum(policy[i]*MATRIX[i][j] for i in range(3)) for j in range(3)]
''',
 broken='''def snapshot(policy):return np.asarray(policy)
def add_snapshot(pool, policy, capacity):
    pool.append(snapshot(policy));return pool
def pool_probabilities(weights):return np.asarray(weights,dtype=float)/sum(weights)
def sample_indices(weights, count, seed):return np.zeros(count,dtype=int)
def coverage(policy):return [sum(policy[i]*MATRIX[i][j] for i in range(3)) for j in range(3)]
''',
 common='''import numpy as np
'''+GAME+'''def validate_policy(p):
    values=np.asarray(p,dtype=float)
    if values.ndim!=1 or len(values)!=3:raise ValueError("length-three policy vector required")
    policy(values.tolist())
def demo(m):
    learner=np.array([.2,.3,.5]);saved=m.snapshot(learner);learner[:]=[1,0,0]
    return dict(saved=saved.tolist(),current=learner.tolist(),weights=m.pool_probabilities([1,2,3]).tolist(),paper_coverage=list(m.coverage([0,1,0])))
''',
 checks='''def check(m):
    import numpy as np
    learner=np.array([.2,.3,.5]);saved=m.snapshot(learner);learner[:]=[1,0,0]
    close_list(saved,[.2,.3,.5]);assert not np.shares_memory(learner,saved) and not saved.flags.writeable
    try:saved[0]=1
    except ValueError:pass
    else:raise AssertionError("snapshot is writable")
    pool=[]
    for p in ([1,0,0],[0,1,0],[0,0,1]):
        original=len(pool);updated=m.add_snapshot(pool,p,2);assert len(pool)==original;pool=updated
    assert len(pool)==2;close_list(pool[0],[0,1,0]);close_list(pool[1],[0,0,1])
    close_list(m.pool_probabilities([1,2,3]),[1/6,1/3,1/2]);close_list(m.coverage([0,1,0]),[1,0,-1])
    for seed in (7,19,31):
        draws=m.sample_indices([1,2,3],10000,seed);assert np.array_equal(draws,m.sample_indices([1,2,3],10000,seed))
        close_list(m.coverage([1/3]*3),[0,0,0]);assert np.max(np.abs(np.bincount(draws,minlength=3)/10000-[1/6,1/3,1/2]))<.02
    rejects(lambda:m.snapshot([1,1,1]));rejects(lambda:m.pool_probabilities([0,1]));rejects(lambda:m.add_snapshot([],learner,0))
''',fixtures=dict(saved=[.2,.3,.5],weights=[1/6,1/3,1/2],paper_coverage=[1,0,-1]))
}

def outputs():
    from build_multiagent_pages import CONTENT
    from multiagent_audit_spec import SPEC
    specs={**SPECS,'p8-audit':SPEC}
    result={}
    for key,s in specs.items():
        folder=LABS/'downloads'/key
        prefix='"""Standalone M5 exercise. Optional reference; see README.md."""\nfrom exercise_common import *\n\n'
        suffix='\nif __name__=="__main__":\n    import sys\n    run(sys.modules[__name__])\n'
        starter='\n\n'.join(f'def {sig}:\n    # TODO: implement the README contract.\n    raise NotImplementedError("Complete {sig.split("(")[0]}")' for sig in s['signatures'])+'\n'
        files={'exercise_common.py':'import math\n'+VALIDATION+s['common']+'\n'+RUNNER,'solution.py':prefix+s['functions']+suffix,'broken.py':prefix+s['broken']+suffix,'starter.py':prefix+starter+suffix,'checks.py':CHECK_HELPERS+s['checks']+CHECK_MAIN,'fixtures.json':json.dumps(s['fixtures'],indent=2)+'\n','requirements.txt':('numpy>=1.26,<3\n' if key in ('p8-pool','p8-audit') else '# Python 3.10+ standard library only.\n')+('pettingzoo>=1.24,<2\ngymnasium>=1.0,<2\n' if key=='p8-audit' else '')}
        template=ROOT/'scripts'/'multiagent_templates'/f'{key}-compare.py'
        if template.is_file():files['compare.py']=template.read_text(encoding='utf-8')
        signatures='\n'.join('- `'+sig+'`' for sig in s['signatures'])
        files['README.md']=f'''# {key}

Python 3.10+{'; NumPy' if key in ('p8-pool','p8-audit') else ', standard library only'}{', PettingZoo and Gymnasium' if key=='p8-audit' else ''}.
Extract anywhere. All files are standalone; no repository or backend required.

```text
python -m pip install -r requirements.txt
python broken.py
python checks.py --candidate broken.py
python starter.py
python checks.py --candidate starter.py
```

Broken code runs but fails checks. Untouched starter reports Exercise incomplete.
Implement TODOs or repair a copy; pass its filename to --candidate. Checks never
import solution.py. Open that optional reference only when you request help.

## Contract

{CONTENT[key]['task']}

{signatures}

Floating comparisons use 1e-9; normalized probability rows use 1e-10. Invalid
inputs described above raise ValueError. Seeded frequency checks use 10,000 draws
for seeds 7,19,31, with tolerance .02. Browser and Python RNGs are different;
identical seeds reproduce within each implementation, not between languages.
Counterfactuals and exact payoffs are model calculations, not measured training.
No test requires a learner to outperform a baseline on a lucky seed.

Tested locally: Python 3.12.7, NumPy 2.5.1, Gymnasium 1.3.0 and PettingZoo 1.27.0
(only install the packages listed in this pack's requirements). The audit's tiny
constant observation and A/B names trigger official API-test recommendations;
the lifecycle assertions still pass. These recommendations are not suppressed.

{('After checks, run `python compare.py --candidate starter.py --seed 7`.' if key=='p8-game' else 'After checks, run `python compare.py --candidate starter.py` for actual Parallel/AEC and official API tests.' if key=='p8-audit' else '')}

Explain and transfer: {CONTENT[key]['reflect']}
'''
        for name,source in files.items():result[folder/name]=source
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');a=p.parse_args()
    for path,source in outputs().items():
        if a.write:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source,encoding='utf-8')
        elif not path.exists() or path.read_text(encoding='utf-8')!=source:raise SystemExit(f'Stale M5 pack: {path}')
    print('Six M5 packs '+('generated.' if a.write else 'are current.'))
