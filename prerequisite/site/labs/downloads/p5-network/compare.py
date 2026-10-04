"""Seeded supervised warm-up, not DQN. Fixed split and optimizer budget."""
import argparse,json,platform
import torch,numpy as np
from checks import load_candidate

def experiment(m,seed=7,steps=200):
    torch.set_num_threads(1);torch.manual_seed(seed)
    x=torch.linspace(0,1,21,dtype=torch.float64)[:,None]
    labels=torch.cat((x,1-x),dim=1)
    train=torch.arange(0,21,2);heldout=torch.arange(1,21,2)
    model=torch.nn.Linear(1,2,dtype=torch.float64)
    optimizer=torch.optim.SGD(model.parameters(),lr=.2)
    with torch.no_grad():initial=float(((model(x[heldout])-labels[heldout])**2).mean())
    for _ in range(steps):m.train_step(model,optimizer,x[train],labels[train])
    with torch.no_grad():final=float(((model(x[heldout])-labels[heldout])**2).mean())
    return dict(seed=seed,optimizer_steps=steps,train_indices=train.tolist(),heldout_indices=heldout.tolist(),initial_heldout_mse=initial,final_heldout_mse=final,python=platform.python_version(),torch=torch.__version__,numpy=np.__version__,threads=1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',default='starter.py');p.add_argument('--seed',type=int,default=7)
    a=p.parse_args();print(json.dumps(experiment(load_candidate(a.candidate),a.seed),indent=2))
