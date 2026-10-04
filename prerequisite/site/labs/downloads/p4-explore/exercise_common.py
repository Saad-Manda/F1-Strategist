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

def validate_settings(episodes, epsilon, alpha):
    if type(episodes) is not int or not 1<=episodes<=5000:
        raise ValueError("episodes must be an integer from 1 to 5000")
    validate_distribution([epsilon,1-epsilon])
    validate_distribution([alpha,1-alpha])

def train(module, seed, episodes, epsilon, alpha):
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

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

