"""Generate four independent M3 Python packs and their seeded comparison CLIs."""
import argparse
from build_foundation_packs import outputs as pack_outputs
from build_tabular_pages import CONTENT

LEGAL_HELPERS = '''def legal_indices(values, legal):
    import math
    if len(values)!=len(legal) or any(not math.isfinite(v) for v in values):
        raise ValueError("finite values and matching mask required")
    indices=[i for i,allowed in enumerate(legal) if allowed]
    if not indices: raise ValueError("at least one legal action required")
    return indices

'''
POLICY_HELPERS = LEGAL_HELPERS + '''def policy_probabilities(values, legal, epsilon):
    validate_distribution([epsilon,1-epsilon])
    indices=legal_indices(values,legal)
    best=max(values[i] for i in indices)
    tied=[i for i in indices if values[i]==best]
    return [epsilon/len(indices)+(1-epsilon)/len(tied)*(i in tied) if legal[i] else 0
            for i in range(len(values))]

def policy_select(values, legal, epsilon, rng):
    probabilities=policy_probabilities(values,legal,epsilon)
    draw=rng.random()
    if not 0<=draw<1: raise ValueError("random draw must be in [0,1)")
    cumulative=0.0
    for action,probability in enumerate(probabilities):
        cumulative+=probability
        if draw<cumulative: return action
    return max(i for i,p in enumerate(probabilities) if p>0)

'''
SETTINGS_HELPERS = '''def validate_settings(episodes, epsilon, alpha):
    if type(episodes) is not int or not 1<=episodes<=5000:
        raise ValueError("episodes must be an integer from 1 to 5000")
    validate_distribution([epsilon,1-epsilon])
    validate_distribution([alpha,1-alpha])

'''
POLICY_HELPERS += SETTINGS_HELPERS

COMPARE = '''"""Run your candidate with visible training/evaluation budgets; no solution import."""
import argparse
import json
from checks import load_candidate
from exercise_common import comparison, validate_settings

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',default='starter.py')
    parser.add_argument('--episodes',type=int,default=1000)
    parser.add_argument('--seeds',default='7,31,89')
    parser.add_argument('--epsilon',type=float,default=0.2)
    parser.add_argument('--alpha',type=float,default=0.1)
    args=parser.parse_args()
    try:
        seeds=[int(x) for x in args.seeds.split(',')]
        if not 2<=len(seeds)<=10 or len(set(seeds))!=len(seeds) or any(not 0<=s<=4294967295 for s in seeds):
            raise ValueError('use 2–10 distinct uint32 seeds')
        validate_settings(args.episodes,args.epsilon,args.alpha)
        print(json.dumps(comparison(load_candidate(args.candidate),seeds,args.episodes,args.epsilon,args.alpha),indent=2))
    except (ValueError,NotImplementedError) as error:
        print(f'Exercise incomplete or invalid settings: {error}')
        raise SystemExit(1)

if __name__=='__main__':main()
'''
COMPARE_README = '''
## Seeded local comparison

Once checks pass, run your candidate:

```text
python compare.py --candidate starter.py --episodes 1000 --seeds 7,31,89 --epsilon 0.2 --alpha 0.1
```

This prints JSON with every seed, final Q tables, training means, evaluation means, and
the mean across seeds for each variant. Evaluation freezes the table and disables
exploration. Policy and observations/rewards use separate random streams. Paired
variants use the same seeds and budgets; trajectories can differ with their policies.
These finite sampled results illustrate learning; no checker requires winning on a
particular seed. Alter epsilon or budget and explain the changes. Browser seed triplets
default to 7,8,9; pass those locally if you want matching seed labels, remembering the
browser LCG and Python random.Random generate different paths.
'''

SPECS = {
 'p4-td': {
  'signatures':['update(q, reward, next_values, legal, alpha, gamma, terminated, truncated=False)'],
  'functions':'''def update(q, reward, next_values, legal, alpha, gamma, terminated, truncated=False):
    import math
    validate_distribution([alpha,1-alpha]); validate_distribution([gamma,1-gamma])
    if not math.isfinite(q) or not math.isfinite(reward): raise ValueError("finite q/reward required")
    continuation=0 if terminated else max(next_values[i] for i in legal_indices(next_values,legal))
    target=reward+gamma*continuation
    error=target-q
    return dict(target=target,error=error,value=q+alpha*error)
''',
  'broken':'''def update(q, reward, next_values, legal, alpha, gamma, terminated, truncated=False):
    continuation=0 if terminated or truncated else max(next_values)
    target=reward+gamma*continuation
    return dict(target=target,error=target-q,value=q+alpha*(target-q))
''',
  'common':LEGAL_HELPERS+'''def demo(module):
    return {label:module.update(2,1,[4,8,99],[True,True,False],0.25,0.5,terminal,truncated)
            for label,terminal,truncated in [('ongoing',False,False),('terminal',True,False),('truncated',False,True)]}
''',
  'checks':'''def check(module):
    f=module.update
    for terminal,truncated,target,value in [(False,False,5,2.75),(True,False,1,1.75),(False,True,5,2.75),(True,True,1,1.75)]:
        result=f(2,1,[4,8,99],[True,True,False],0.25,0.5,terminal,truncated)
        close(result['target'],target);close(result['error'],target-2);close(result['value'],value)
    close(f(2,1,[],[],0.25,0.5,True)['value'],1.75)
    close(f(-3,-1,[-8,-2,99],[True,True,False],1,1,False)['target'],-3)
    close(f(7,-1,[8],[True],0,0,False)['value'],7)
    values=[4,8,99];mask=[True,True,False]
    f(2,1,values,mask,0.25,0.5,False)
    assert values==[4,8,99] and mask==[True,True,False], 'input arrays mutated'
    for values,mask in [([],[]),([1],[False]),([1],[True,False])]:
        rejects(lambda:f(2,1,values,mask,0.25,0.5,False))
    for alpha,gamma in [(-0.1,0.5),(0.2,1.1),(float('nan'),0.5)]:
        rejects(lambda:f(2,1,[8],[True],alpha,gamma,False))
    rejects(lambda:f(float('inf'),1,[8],[True],0.2,0.5,False))
''',
  'fixtures':{'q':2,'reward':1,'alpha':0.25,'gamma':0.5,'next_values':[4,8,99],'legal':[True,True,False],'ongoing':{'target':5,'error':3,'value':2.75},'terminal':{'target':1,'error':-1,'value':1.75}},
 },
 'p4-explore': {
  'signatures':['probabilities(values, legal, epsilon)','select_action(values, legal, epsilon, rng)'],
  'functions':'''def probabilities(values, legal, epsilon):
    validate_distribution([epsilon,1-epsilon])
    indices=legal_indices(values,legal)
    maximum=max(values[i] for i in indices)
    ties=[i for i in indices if values[i]==maximum]
    return [epsilon/len(indices)+(1-epsilon)/len(ties)*(i in ties) if legal[i] else 0
            for i in range(len(values))]

def select_action(values, legal, epsilon, rng):
    probabilities_=probabilities(values,legal,epsilon)
    draw=rng.random()
    if not 0<=draw<1:raise ValueError('draw must be in [0,1)')
    cumulative=0.0
    for action,p in enumerate(probabilities_):
        cumulative+=p
        if draw<cumulative:return action
    return max(i for i,p in enumerate(probabilities_) if p>0)
''',
  'broken':'''def probabilities(values, legal, epsilon):
    chosen=max(legal_indices(values,legal),key=lambda i:values[i])
    return [int(i==chosen) for i in range(len(values))]

def select_action(values, legal, epsilon, rng):
    return max(legal_indices(values,legal),key=lambda i:values[i])
''',
  'common':LEGAL_HELPERS+SETTINGS_HELPERS+'''def train(module, seed, episodes, epsilon, alpha):
    import random
    q=[0.6,0.1,99];mask=[True,True,False];visits=[0,0,0]
    rng=random.Random(seed+303); rewards=[random.Random(seed+101),random.Random(seed+202)]
    total=0
    for _ in range(episodes):
        action=module.select_action(q,mask,epsilon,rng)
        if action not in (0,1):raise ValueError('candidate selected illegal C')
        reward=int(rewards[action].random()<[0.4,0.8][action]);total+=reward;visits[action]+=1
        q[action]+=alpha*(reward-q[action])  # One-step true terminal target.
    evaluation_policy=random.Random(seed+606); evaluation_rewards=[random.Random(seed+404),random.Random(seed+505)]
    evaluated=0;eval_visits=[0,0,0]; frozen=q[:]
    for _ in range(200):
        action=module.select_action(q,mask,0,evaluation_policy)
        if action not in (0,1):raise ValueError('candidate selected illegal C during evaluation')
        eval_visits[action]+=1;evaluated+=int(evaluation_rewards[action].random()<[0.4,0.8][action])
    assert q==frozen,'evaluation changed Q'
    return dict(q=q,visits=visits,eval_visits=eval_visits,training_mean=total/episodes,evaluation_mean=evaluated/200)

def comparison(module,seeds,episodes,epsilon,alpha):
    runs=[dict(variant=label,seed=seed,**train(module,seed,episodes,eps,alpha))
          for seed in seeds for label,eps in [('epsilon_0',0),('chosen_epsilon',epsilon)]]
    return report(runs,dict(episodes=episodes,transitions_per_seed=episodes,epsilon=epsilon,baseline_epsilon=0,alpha=alpha,gamma=0,
                            initial_q=[0.6,0.1,99],reward_means=[0.4,0.8],legal=[True,True,False]),
                  dict(episodes=200,epsilon=0,frozen_q=True,reward_streams='fresh paired streams per action'))

def demo(module):
    return dict(training_probabilities=module.probabilities([0.6,0.1,99],[True,True,False],0.2),
                evaluation_probabilities=module.probabilities([0.6,0.1,99],[True,True,False],0))
''',
  'checks':'''class Draw:
    def __init__(self,x):self.x=x
    def random(self):return self.x

def check(module):
    import random
    f=module.probabilities;s=module.select_action
    close_list(f([0.6,0.1,99],[True,True,False],0.2),[0.9,0.1,0])
    close_list(f([0.6,0.1,99],[True,True,False],1),[0.5,0.5,0])
    close_list(f([3,3,99],[True,True,False],0),[0.5,0.5,0])
    close_list(f([-3,-1,-1],[True,True,True],0.3),[0.1,0.45,0.45])
    for draw,action in [(0,0),(0.899,0),(0.9,1),(0.999,1)]:
        assert s([0.6,0.1,99],[True,True,False],0.2,Draw(draw))==action
    assert s([99,2],[False,True],0,Draw(0))==1
    for seed in (7,31,89):
        rng=random.Random(seed)
        draws=[s([1,1,99],[True,True,False],0,rng) for _ in range(10000)]
        assert set(draws)=={0,1} and abs(draws.count(0)/len(draws)-0.5)<0.02,'tie selection biased or illegal'
    a,b=random.Random(9),random.Random(9)
    assert [s([1,2],[True,True],0.3,a) for _ in range(100)]==[s([1,2],[True,True],0.3,b) for _ in range(100)]
    for args in [([1],[False],0.2),([1],[True,False],0.2),([1],[True],-0.1),([float('nan')],[True],0.2)]:
        rejects(lambda:f(*args))
    rejects(lambda:s([1],[True],0,Draw(1)))
''',
  'fixtures':{'q':[0.6,0.1,99],'legal':[True,True,False],'epsilon_02':[0.9,0.1,0],'epsilon_1':[0.5,0.5,0],'tie':[0.5,0.5,0]},
 },
 'p4-sarsa': {
  'signatures':['act(memory, state, values, legal, epsilon, rng)','target(memory, reward, next_state, values, legal, gamma, terminated, truncated, epsilon, rng)','reset(memory)'],
  'functions':'''def act(memory, state, values, legal, epsilon, rng):
    pending=memory.pop('pending',None)
    if pending is None:return policy_select(values,legal,epsilon,rng)
    pending_state,action=pending
    if pending_state!=state or action not in legal_indices(values,legal):raise ValueError('stale pending action')
    return action

def target(memory, reward, next_state, values, legal, gamma, terminated, truncated, epsilon, rng):
    import math
    validate_distribution([gamma,1-gamma])
    if not math.isfinite(reward):raise ValueError('reward must be finite')
    memory.pop('pending',None)
    if terminated:return reward
    action=policy_select(values,legal,epsilon,rng)
    if not truncated:memory['pending']=(next_state,action)
    return reward+gamma*values[action]

def reset(memory):
    memory.pop('pending',None)
''',
  'broken':'''def act(memory, state, values, legal, epsilon, rng):
    return policy_select(values,legal,epsilon,rng)  # Resamples instead of consuming pending.

def target(memory, reward, next_state, values, legal, gamma, terminated, truncated, epsilon, rng):
    if terminated:return reward
    action=policy_select(values,legal,epsilon,rng)
    memory['pending']=(next_state,action)
    return reward+gamma*values[action]

def reset(memory):
    pass  # Pending action can leak into a new episode.
''',
  'common':POLICY_HELPERS+'''def train(module,seed,episodes,epsilon,alpha,algorithm):
    import random
    q={'START':[0,0],'RISK':[0,0],'SAFE':[0]};rng=random.Random(seed+303);memory={}
    total=slips=0
    for _ in range(episodes):
        module.reset(memory)
        action=module.act(memory,'START',q['START'],[True,True],epsilon,rng) if algorithm=='sarsa' else policy_select(q['START'],[True,True],epsilon,rng)
        state='RISK' if action==0 else 'SAFE';mask=[True]*len(q[state])
        if algorithm=='sarsa':
            backed=module.target(memory,0,state,q[state],mask,1,False,False,epsilon,rng)
            q['START'][action]+=alpha*(backed-q['START'][action])
            next_action=module.act(memory,state,q[state],mask,epsilon,rng)
        else:
            next_action=policy_select(q[state],mask,epsilon,rng)
            q['START'][action]+=alpha*(max(q[state])-q['START'][action])
        reward=3 if state=='SAFE' else 6 if next_action==0 else -10
        total+=reward;slips+=reward==-10
        terminal_target=module.target(memory,reward,'T',[],[],1,True,False,epsilon,rng) if algorithm=='sarsa' else reward
        q[state][next_action]+=alpha*(terminal_target-q[state][next_action])
    evaluation_rng=random.Random(seed+606);evaluated=0
    frozen={s:values[:] for s,values in q.items()}
    for _ in range(200):
        module.reset(memory)  # Clear training cache before evaluating a new episode.
        action=module.act(memory,'START',q['START'],[True,True],0,evaluation_rng)
        state='RISK' if action==0 else 'SAFE'
        next_action=module.act(memory,state,q[state],[True]*len(q[state]),0,evaluation_rng)
        evaluated+=3 if state=='SAFE' else 6 if next_action==0 else -10
    assert q==frozen,'evaluation changed Q'
    return dict(q=q,training_mean=total/episodes,evaluation_mean=evaluated/200,slips=slips)

def comparison(module,seeds,episodes,epsilon,alpha):
    runs=[dict(variant=algorithm,seed=seed,**train(module,seed,episodes,epsilon,alpha,algorithm))
          for seed in seeds for algorithm in ('q-learning','sarsa')]
    return report(runs,dict(episodes=episodes,transitions_per_seed=episodes*2,epsilon=epsilon,alpha=alpha,gamma=1,initial_q='all zeros'),
                  dict(episodes=200,transitions_per_seed=400,epsilon=0,frozen_q=True,reset_pending=True))

def demo(module):
    class Witness:
        def random(self):return 0.95
    memory={};rng=Witness()
    value=module.target(memory,0,'RISK',[6,-10],[True,True],1,False,False,0.2,rng)
    action=module.act(memory,'RISK',[6,-10],[True,True],0.2,rng)
    return dict(sarsa_target=value,executed_action=action,q_learning_target=6,memory_after=memory)
''',
  'checks':'''class Draws:
    def __init__(self,draws):self.draws=iter(draws);self.calls=0
    def random(self):self.calls+=1;return next(self.draws)

def check(module):
    memory={};rng=Draws([0.95,0.05])
    close(module.target(memory,0,'RISK',[6,-10],[True,True],1,False,False,0.2,rng),-10)
    assert rng.calls==1 and memory.get('pending')==('RISK',1),'target must commit its sampled action'
    assert module.act(memory,'RISK',[6,-10],[True,True],0.2,rng)==1,'executed action differs from target'
    assert rng.calls==1 and 'pending' not in memory,'act must consume without resampling'
    assert module.act(memory,'RISK',[6,-10],[True,True],0.2,rng)==0 and rng.calls==2
    memory['pending']=('RISK',1);module.reset(memory)
    assert 'pending' not in memory,'reset leaked pending action'
    assert module.act(memory,'RISK',[6,-10],[True,True],0,Draws([0.99]))==0,'greedy evaluation retained exploration'
    for terminated,truncated in [(True,False),(True,True)]:
        memory['pending']=('RISK',1);rng=Draws([])
        close(module.target(memory,3,'T',[],[],1,terminated,truncated,0.2,rng),3)
        assert rng.calls==0 and 'pending' not in memory,'terminal target sampled or leaked cache'
    rng=Draws([0.95]);memory['pending']=('old',0)
    close(module.target(memory,1,'RISK',[6,-10],[True,True],0.5,False,True,0.2,rng),-4)
    assert 'pending' not in memory,'truncation leaked hypothetical bootstrap action'
    rng=Draws([0.1]);memory={}
    close(module.target(memory,0,'RISK',[99,6],[False,True],1,False,False,0.2,rng),6)
    assert module.act(memory,'RISK',[99,6],[False,True],0.2,rng)==1
    memory['pending']=('wrong',0)
    rejects(lambda:module.act(memory,'RISK',[6,-10],[True,True],0.2,Draws([0])))
    rejects(lambda:module.target({},0,'RISK',[],[],1,False,False,0.2,Draws([0])))
    rejects(lambda:module.target({},0,'RISK',[6],[True],2,False,False,0.2,Draws([0])))
''',
  'fixtures':{'risk_q':[6,-10],'sampled_slip_target':-10,'q_learning_target':6,'epsilon_02_behaviour':4.4,'epsilon_06_behaviour':1.2},
 },
 'p4-bins': {
  'signatures':['bin_index(x, edges)','table_size(bin_counts, actions=2)'],
  'functions':'''def bin_index(x, edges):
    import bisect
    import math
    if not math.isfinite(x) or not 0<=x<=1:raise ValueError('x must be in [0,1]')
    if len(edges)<2 or edges[0]!=0 or edges[-1]!=1 or any(not math.isfinite(e) or (i and e<=edges[i-1]) for i,e in enumerate(edges)):
        raise ValueError('edges must strictly increase from 0 to 1')
    return min(bisect.bisect_right(edges,x)-1,len(edges)-2)

def table_size(bin_counts, actions=2):
    import math
    if not bin_counts or any(type(n) is not int or n<1 for n in list(bin_counts)+[actions]):raise ValueError('positive integer counts required')
    states=math.prod(bin_counts);entries=states*actions
    return dict(states=states,entries=entries,bytes=entries*8)
''',
  'broken':'''def bin_index(x, edges):
    return min(int(x*len(edges)),len(edges)-1)  # Counts edges as bins; ignores nonuniform boundaries.

def table_size(bin_counts, actions=2):
    states=sum(bin_counts)
    return dict(states=states,entries=states*actions,bytes=states*actions*8)
''',
  'common':POLICY_HELPERS+'''def ceiling(edges):
    return sum(max(max(0,min(hi,0.5)-lo),max(0,hi-max(lo,0.5))) for lo,hi in zip(edges,edges[1:]))

def train(module,seed,episodes,edges,epsilon,alpha):
    import random
    q=[[0,0] for _ in edges[1:]];rng=random.Random(seed+303); observations=random.Random(seed+101);total=0
    for _ in range(episodes):
        x=observations.random();index=module.bin_index(x,edges)
        action=policy_select(q[index],[True,True],epsilon,rng)
        reward=int(action==(0 if x<0.5 else 1));total+=reward;q[index][action]+=alpha*(reward-q[index][action])
    frozen=[values[:] for values in q];evaluated=0
    for i in range(1000):
        x=(i+0.5)/1000;index=module.bin_index(x,edges)
        evaluated+=policy_probabilities(q[index],[True,True],0)[0 if x<0.5 else 1]
    assert q==frozen,'evaluation changed Q'
    return dict(q=q,edges=edges,training_mean=total/episodes,evaluation_mean=evaluated/1000,representation_ceiling=ceiling(edges),size=module.table_size([len(edges)-1]))

def comparison(module,seeds,episodes,epsilon,alpha):
    variants=[('coarse',[0,1]),('split',[0,0.5,1]),('nonuniform',[0,0.45,0.5,0.55,1])]
    runs=[dict(variant=label,seed=seed,**train(module,seed,episodes,edges,epsilon,alpha)) for seed in seeds for label,edges in variants]
    return report(runs,dict(episodes=episodes,transitions_per_seed=episodes,epsilon=epsilon,alpha=alpha,gamma=0,initial_q='all zeros',observations='uniform [0,1)'),
                  dict(observations=1000,epsilon=0,frozen_q=True,grid='paired midpoint grid',ties='exact uniform greedy action probabilities'))

def demo(module):
    return dict(encodings={str(x):module.bin_index(x,[0,0.5,1]) for x in (0,0.49,0.5,0.51,1)},size=module.table_size([4,4,4]))
''',
  'checks':'''def check(module):
    f=module.bin_index
    assert f(0.49,[0,1])==f(0.51,[0,1])==0
    for x,target in [(0,0),(0.49,0),(0.5,1),(0.51,1),(1,1)]:assert f(x,[0,0.5,1])==target,f'boundary failed at {x}'
    for x,target in [(0.1,0),(0.45,1),(0.49,1),(0.5,2),(0.55,3),(0.99,3),(1,3)]:
        assert f(x,[0,0.45,0.5,0.55,1])==target,'nonuniform edges ignored'
    assert module.table_size([4,4,4])==dict(states=64,entries=128,bytes=1024)
    assert module.table_size([8,8,8])['entries']/module.table_size([4,4,4])['entries']==8
    assert module.table_size([12,5,10,3,3,2,8,2],6)['states']==172800
    for x in (-0.1,1.1,float('nan')):rejects(lambda:f(x,[0,0.5,1]))
    for edges in [[],[0],[0,0.5,0.5,1],[0,0.8,0.5,1],[0.1,1],[0,0.9],[0,float('nan'),1]]:
        rejects(lambda:f(0.5,edges))
    for counts,actions in [([],2),([0],2),([1.5],2),([2],0),([True],2)]:rejects(lambda:module.table_size(counts,actions))
''',
  'fixtures':{'split_edges':[0,0.5,1],'witnesses':[[0,0],[0.49,0],[0.5,1],[0.51,1],[1,1]],'size':{'states':64,'entries':128,'bytes':1024}},
 },
}

REPORT = '''def report(runs,training,evaluation):
    labels=sorted(set(r['variant'] for r in runs))
    summary={label:{metric:sum(r[metric] for r in runs if r['variant']==label)/sum(r['variant']==label for r in runs)
                    for metric in ('training_mean','evaluation_mean')} for label in labels}
    return dict(training=training,evaluation=evaluation,random_generator='Python random.Random; independent policy/environment streams',
                warning='Finite sampled results illustrate learning, not correctness guarantees.',runs=runs,summary=summary)

'''
for key in ('p4-explore','p4-sarsa','p4-bins'):
    SPECS[key]['common']=REPORT+SPECS[key]['common']
    SPECS[key]['extras']={'compare.py':COMPARE}
    SPECS[key]['readmeExtra']=COMPARE_README

def outputs():return pack_outputs(SPECS,CONTENT)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    for path,content in outputs().items():
        if args.write:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8')
        elif not path.exists() or path.read_text(encoding='utf-8')!=content:
            raise SystemExit('Stale M3 pack. Run build_tabular_packs.py --write.')
    print('Four M3 packs '+('generated.' if args.write else 'are current.'))

if __name__=='__main__':main()
