"""Optional real MaskablePPO and spawn exercise; core checks need no RL library."""
import argparse,json,platform,pickle,threading
import numpy as np
import torch
from checks import check,load_candidate

def make_chain(cap=8,resource=None):
    import gymnasium as gym
    class Chain(gym.Env):
        render_mode=None
        def __init__(self):
            self.observation_space=gym.spaces.Box(0,3,(1,),dtype=np.float32)
            self.action_space=gym.spaces.Discrete(3);self.total_steps=0
        def reset(self,seed=None,options=None):
            super().reset(seed=seed);self.pos=0;self.elapsed=0
            return np.array([0],dtype=np.float32),{}
        def action_masks(self):return np.array([True,True,False])
        def step(self,action):
            if int(action)==2:raise ValueError('masked illegal action selected')
            self.pos=self.pos+1 if int(action)==0 else 0
            self.elapsed+=1;self.total_steps+=1;terminal=self.pos==3
            return np.array([self.pos],dtype=np.float32),float(terminal),terminal,self.elapsed>=cap and not terminal,{}
    return Chain()

def integration():
    import sys,faulthandler
    faulthandler.dump_traceback_later(45)
    import gymnasium,stable_baselines3,sb3_contrib
    from stable_baselines3.common.vec_env import SubprocVecEnv,DummyVecEnv
    from sb3_contrib import MaskablePPO
    factory=lambda:make_chain()
    try:pickle.dumps(factory);ordinary='unexpected success'
    except (AttributeError,pickle.PicklingError) as e:ordinary=type(e).__name__
    # Check the actual factory serializer before creating a process: a failed
    # Windows Process.start can otherwise leave a child awaiting its payload.
    from stable_baselines3.common.vec_env.base_vec_env import CloudpickleWrapper
    lock=threading.Lock()
    try:pickle.dumps(CloudpickleWrapper(lambda:make_chain(resource=lock)));captured='unexpected success'
    except TypeError as e:captured=str(e)
    print('Starting actual spawn workers',file=sys.stderr,flush=True)
    env=SubprocVecEnv([lambda:make_chain(),lambda:make_chain()],start_method='spawn')
    try:
        model=MaskablePPO('MlpPolicy',env,seed=7,n_steps=16,batch_size=32,n_epochs=2,learning_rate=.001,policy_kwargs=dict(net_arch=[8]),device='cpu',verbose=0)
        print('Collecting 128 masked PPO transitions',file=sys.stderr,flush=True)
        model.learn(total_timesteps=128)
        counts=env.get_attr('total_steps');actual=model.num_timesteps
        evaluation=[]
        for seed in (101,102,103,104):
            test=make_chain();obs,_=test.reset(seed=seed);score=0;steps=0
            while True:
                action,_=model.predict(obs,deterministic=True,action_masks=test.action_masks())
                obs,reward,term,trunc,_=test.step(action);score+=reward;steps+=1
                if term or trunc:break
            test.close();evaluation.append(dict(seed=seed,return_=score,transitions=steps))
    finally:env.close()
    auto=DummyVecEnv([lambda:make_chain(cap=2)])
    try:
        auto.reset();auto.step([0]);reset_obs,reward,done,info=auto.step([0])
        boundary=dict(done=bool(done[0]),time_limit_truncated=bool(info[0]['TimeLimit.truncated']),final_observation=info[0]['terminal_observation'].tolist(),reset_observation=reset_obs[0].tolist())
    finally:auto.close()
    faulthandler.cancel_dump_traceback_later()
    return dict(python=platform.python_version(),platform=platform.system(),device='cpu',versions=dict(numpy=np.__version__,torch=torch.__version__,gymnasium=gymnasium.__version__,stable_baselines3=stable_baselines3.__version__,sb3_contrib=sb3_contrib.__version__),factories=dict(ordinary_pickle_lambda=ordinary,sb3_cloudpickle_lambda_spawn='passed',captured_lock_failure=captured),settings=dict(seed=7,n_envs=2,n_steps=16,batch_size=32,n_epochs=2,threads=1),requested_transitions=128,actual_transitions=actual,worker_transition_counts=counts,rollout_transitions=32,evaluation=evaluation,auto_reset_boundary=boundary)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',default='starter.py');p.add_argument('--integration',action='store_true');args=p.parse_args()
    torch.set_num_threads(1);check(load_candidate(args.candidate))
    print(json.dumps(integration() if args.integration else dict(core_checks='passed',integration='Use --integration after installing gymnasium stable-baselines3 sb3-contrib'),indent=2))
