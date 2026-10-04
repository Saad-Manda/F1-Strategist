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

def ceiling(edges):
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

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

