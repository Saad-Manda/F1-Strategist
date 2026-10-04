import math
def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

import hashlib
import numpy as np
from gymnasium import spaces
from pettingzoo import ParallelEnv
from pettingzoo.utils.conversions import parallel_to_aec

class OneRound(ParallelEnv):
    metadata={'name':'teaching_rps_v1','render_modes':[],'is_parallelizable':True}
    possible_agents=['A','B']
    def __init__(self):
        self.agents=[]
        self.render_mode=None
        self.observation_spaces={a:spaces.Box(0,1,(1,),dtype=np.int8) for a in self.possible_agents}
        self.action_spaces={a:spaces.Discrete(3) for a in self.possible_agents}
    def observation_space(self,agent):return self.observation_spaces[agent]
    def action_space(self,agent):return self.action_spaces[agent]
    def reset(self,seed=None,options=None):
        self.agents=list(self.possible_agents)
        for i,a in enumerate(self.agents):self.action_spaces[a].seed(None if seed is None else seed+i)
        return {a:np.array([0],dtype=np.int8) for a in self.agents},{a:{} for a in self.agents}
    def step(self,actions):
        if not self.agents:
            if actions:raise ValueError('no live agents')
            return {},{},{},{},{}
        validate_actions(actions,self.agents)
        a,b=int(actions['A']),int(actions['B'])
        reward=0 if a==b else (1 if (a-b)%3==1 else -1)
        live=list(self.agents);self.agents=[]
        return ({agent:np.array([1],dtype=np.int8) for agent in live},
                {'A':reward,'B':-reward},{agent:True for agent in live},
                {agent:False for agent in live},{agent:{} for agent in live})
    def render(self):return None
    def close(self):pass

def validate_actions(actions,agents):
    if set(actions)!=set(agents) or any(not isinstance(v,(int,np.integer)) or isinstance(v,(bool,np.bool_)) or not 0<=v<3 for v in actions.values()):raise ValueError('exact live-agent integer actions 0,1,2 required')

def ids(values):
    if not values or any(not isinstance(v,str) or not v for v in values) or len(set(values))!=len(values):raise ValueError('nonempty distinct IDs required')
def stable_seed(master,label):
    return int.from_bytes(hashlib.sha256(f'{master}:{label}'.encode()).digest()[:4],'big')

def demo(m):
    env=OneRound();env.reset(seed=7)
    parallel=m.parallel_round(env,{'A':1,'B':0})
    aec=parallel_to_aec(OneRound());aec.reset(seed=7)
    trace=m.aec_round(aec,{'A':1,'B':0})
    return dict(paired=m.paired_scores([{'scenario_id':'s0','score':2},{'scenario_id':'s1','score':8}],[{'scenario_id':'s1','score':7},{'scenario_id':'s0','score':1}]),schedule=m.schedule(['s0','s1'],['rock','scissors'],7),transitions=m.experience(8,128),parallel=parallel,aec=trace,aec_live_agents=list(aec.agents))

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

