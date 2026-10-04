"""Fixed-opponent action-value learning, followed by exact held-out coverage."""
import argparse,json,random,platform
from checks import load_candidate

def run(m,seed):
    rng=random.Random(seed);opponent=[.5,.25,.25];values=[0.,0.,0.];counts=[0,0,0]
    for _ in range(1000):
        learner=rng.randrange(3)  # uniform coverage during the fixed training budget
        u=rng.random();other=0 if u<.5 else 1 if u<.75 else 2
        counts[learner]+=1
        values=m.action_update(values,learner,m.payoff(learner,other),1/counts[learner])
    selected=max(range(3),key=lambda i:values[i]);policy=[int(i==selected) for i in range(3)]
    return dict(seed=seed,training_joint_transitions=1000,exploration='uniform',opponent_distribution=opponent,counts=counts,action_values=values,greedy_action=selected,evaluation='exact frozen policy against each pure opponent; no sampling or updates',coverage=[m.expected_payoff(policy,[int(i==j) for i in range(3)]) for j in range(3)])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',default='starter.py');p.add_argument('--seed',type=int,default=7);a=p.parse_args()
    m=load_candidate(a.candidate)
    print(json.dumps(dict(python=platform.python_version(),runs=[run(m,a.seed+i) for i in range(3)]),indent=2))
