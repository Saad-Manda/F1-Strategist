"""Actual fixed-budget CPU bandit learning; scores are observations, not gates."""
import argparse,json,platform
import numpy as np
import torch
from checks import check,load_candidate

def experiment(candidate,seed):
    policy_rng=np.random.default_rng(seed);reward_rng=np.random.default_rng(seed+1000)
    logits=torch.zeros((1,2),dtype=torch.float64,requires_grad=True)
    optimizer=torch.optim.SGD([logits],lr=.05)
    for _ in range(256):
        p=candidate.probabilities(logits).detach().numpy()[0]
        action=int(policy_rng.choice(2,p=p));reward=float(reward_rng.random()<[.4,.8][action])
        optimizer.zero_grad();candidate.reinforce_loss(logits,torch.tensor([action]),torch.tensor([reward],dtype=torch.float64)).backward();optimizer.step()
    p=candidate.probabilities(logits).detach().numpy()[0]
    return dict(seed=seed,transitions=256,optimizer_steps=256,probabilities=p.tolist(),exact_frozen_expected_return=float(p@np.array([.4,.8])),evaluation_transitions=0)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',default='starter.py');parser.add_argument('--seed',type=int,default=7);args=parser.parse_args()
    torch.set_num_threads(1);m=load_candidate(args.candidate);check(m)
    print(json.dumps(dict(device='cpu',python=platform.python_version(),torch=torch.__version__,numpy=np.__version__,runs=[experiment(m,s) for s in (args.seed,args.seed+12,args.seed+24)]),indent=2))
