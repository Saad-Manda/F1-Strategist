"""Paired chain ablations. Curves are contextual evidence, never correctness gates."""
import argparse,json,platform,random
import torch,numpy as np
from checks import load_candidate

SETTINGS=dict(transitions=192,warmup=4,update_every=4,batch_size=4,capacity=4,target_interval=8,gamma=.9,learning_rate=.05,epsilon=.3,episode_cap=8,hidden=8,threads=1)
VARIANTS=('replay+target','latest+target','replay+online')

def observation(position):
    return torch.nn.functional.one_hot(torch.tensor(position),4).to(torch.float64)

def evaluate(model):
    # Frozen greedy evaluation, four identical starts, no RNG consumption.
    results=[]
    with torch.no_grad():
        for _ in range(4):
            pos=0;reward=0
            for step in range(8):
                action=int(model(observation(pos)[None]).argmax(1))
                pos=pos+1 if action==0 else 0
                if pos==3:reward=1;break
            results.append(reward)
    return sum(results)/len(results)

def experiment(m,seed,variant):
    if variant not in VARIANTS:raise ValueError('unknown variant')
    torch.set_num_threads(1);torch.manual_seed(seed)
    action_rng=random.Random(seed);sample_rng=random.Random(seed+1000)
    online=torch.nn.Sequential(torch.nn.Linear(4,8,dtype=torch.float64),torch.nn.ReLU(),torch.nn.Linear(8,2,dtype=torch.float64))
    target=m.make_target(online);optimizer=torch.optim.SGD(online.parameters(),lr=.05)
    buffer=[];pos=0;episode_step=0;updates=0;rows=[];terminations=0;truncations=0
    for collected in range(1,193):
        with torch.no_grad():greedy=int(online(observation(pos)[None]).argmax(1))
        action=action_rng.randrange(2) if action_rng.random()<.3 else greedy
        nxt=pos+1 if action==0 else 0;terminated=nxt==3;reward=float(terminated)
        episode_step+=1;truncated=not terminated and episode_step==8
        transition=(pos,action,reward,nxt,terminated,truncated)
        m.push(buffer,transition,4);pos=nxt
        terminations+=int(terminated);truncations+=int(truncated)
        if terminated or truncated:pos=0;episode_step=0
        if collected>=4 and collected%4==0:
            batch=m.sample(buffer,4,sample_rng) if variant!='latest+target' else [buffer[-1]]*4
            states=torch.stack([observation(t[0]) for t in batch]);actions=torch.tensor([t[1] for t in batch])
            rewards=torch.tensor([t[2] for t in batch],dtype=torch.float64)
            next_states=torch.stack([observation(t[3]) for t in batch]);done=torch.tensor([t[4] for t in batch])
            source=online if variant=='replay+online' else target
            y=m.targets(source,next_states,rewards,done,.9)
            optimizer.zero_grad();prediction=online(states).gather(1,actions[:,None]).squeeze(1)
            loss=((prediction-y)**2).mean();loss.backward();optimizer.step();updates+=1
            m.sync_target(target,online,updates,8)
            if collected%32==0:
                rows.append(dict(transitions=collected,optimizer_steps=updates,td_mse=float(loss.detach()),evaluation_return=evaluate(online),evaluation_episodes=4))
    return dict(seed=seed,variant=variant,transitions=192,optimizer_steps=updates,terminations=terminations,truncations=truncations,checkpoints=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',default='starter.py');p.add_argument('--seed',type=int,default=7)
    a=p.parse_args();m=load_candidate(a.candidate)
    print(json.dumps(dict(settings=SETTINGS,python=platform.python_version(),torch=torch.__version__,numpy=np.__version__,runs=[experiment(m,a.seed,v) for v in VARIANTS]),indent=2))
