def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

def report(runs,training,evaluation):
    labels=sorted(set(r['variant'] for r in runs))
    summary={label:{metric:sum(r[metric] for r in runs if r['variant']==label)/sum(r['variant']==label for r in runs)
                    for metric in ('training_mean','evaluation_mean')} for label in labels}
    return dict(training=training,evaluation=evaluation,random_generator='Python random.Random; independent policy/environment streams',
                warning='Finite sampled results illustrate learning, not correctness guarantees.',runs=runs,summary=summary)

def legal_indices(values, legal):
    import math
    if len(values)!=len(legal) or any(not math.isfinite(v) for v in values):
        raise ValueError("finite values and matching mask required")
    indices=[i for i,allowed in enumerate(legal) if allowed]
    if not indices: raise ValueError("at least one legal action required")
    return indices

def policy_probabilities(values, legal, epsilon):
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

def validate_settings(episodes, epsilon, alpha):
    if type(episodes) is not int or not 1<=episodes<=5000:
        raise ValueError("episodes must be an integer from 1 to 5000")
    validate_distribution([epsilon,1-epsilon])
    validate_distribution([alpha,1-alpha])

def train(module,seed,episodes,epsilon,alpha,algorithm):
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

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

