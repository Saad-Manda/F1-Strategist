"""Standalone evaluation contracts and real PettingZoo lifecycle scaffolding."""
COMMON='''import hashlib
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
'''
SPEC=dict(
 signatures=['schedule(scenarios, opponents, master_seed)','paired_scores(rows_a, rows_b)','experience(vector_envs, vector_steps)','parallel_round(env, actions)','aec_round(env, actions)'],
 functions='''def schedule(scenarios, opponents, master_seed):
    ids(scenarios);ids(opponents)
    if type(master_seed) is not int or master_seed<0:raise ValueError('nonnegative integer seed required')
    return [dict(scenario_id=s,opponent_id=o,scenario_seed=stable_seed(master_seed,'scenario:'+s),opponent_seed=stable_seed(master_seed,'opponent:'+o),exploration=0) for s in scenarios for o in opponents]
def paired_scores(rows_a, rows_b):
    def indexed(rows):
        ids([r['scenario_id'] for r in rows])
        if any(not math.isfinite(r['score']) for r in rows):raise ValueError('finite scores required')
        return {r['scenario_id']:r['score'] for r in rows}
    a,b=indexed(rows_a),indexed(rows_b)
    if a.keys()!=b.keys():raise ValueError('scenario coverage differs')
    return [dict(scenario_id=s,difference=a[s]-b[s]) for s in sorted(a)]
def experience(vector_envs, vector_steps):
    if type(vector_envs) is not int or vector_envs<1 or type(vector_steps) is not int or vector_steps<0:raise ValueError('positive env count and nonnegative step count required')
    return vector_envs*vector_steps
def parallel_round(env, actions):
    live=list(env.agents);validate_actions(actions,live)
    if not live:raise ValueError('reset before a round')
    obs,rewards,terminations,truncations,infos=env.step(dict(actions))
    return dict(actions_consumed=len(live),joint_transitions=1,rewards=rewards,terminations=terminations,truncations=truncations,agents=list(env.agents))
def aec_round(env, actions):
    validate_actions(actions,env.agents)
    trace=[]
    for agent in env.agent_iter():
        observation,reward,terminated,truncated,info=env.last()
        chosen=None if terminated or truncated else actions[agent]
        trace.append(dict(agent=agent,action=chosen,reward=float(reward),terminated=bool(terminated),truncated=bool(truncated),observation=np.asarray(observation).tolist()))
        env.step(chosen)
    return trace
''',
 broken='''def schedule(scenarios, opponents, master_seed):
    return [dict(scenario_id=s,opponent_id=o,scenario_seed=master_seed+i,opponent_seed=master_seed,exploration=.2) for i,s in enumerate(scenarios) for o in opponents]
def paired_scores(rows_a, rows_b):return [dict(scenario_id=a['scenario_id'],difference=a['score']-b['score']) for a,b in zip(rows_a,rows_b)]
def experience(vector_envs, vector_steps):return vector_steps
def parallel_round(env, actions):
    obs,rewards,terminations,truncations,infos=env.step(actions)
    return dict(actions_consumed=len(actions),joint_transitions=1,rewards=rewards,terminations=terminations,truncations=truncations,agents=list(env.agents))
def aec_round(env, actions):
    trace=[]
    for agent in env.agent_iter():
        obs,reward,term,trunc,info=env.last()
        chosen=None if all(env.terminations.values()) else actions[agent]
        trace.append(dict(agent=agent,action=chosen,reward=float(reward),terminated=bool(term),truncated=bool(trunc),observation=np.asarray(obs).tolist()))
        env.step(chosen)
    return trace
''',
 common=COMMON,
 checks='''def check(m):
    from exercise_common import OneRound,parallel_to_aec
    a=[dict(scenario_id='s0',score=2),dict(scenario_id='s1',score=8)]
    b=[dict(scenario_id='s1',score=7),dict(scenario_id='s0',score=1)]
    assert m.paired_scores(a,b)==[dict(scenario_id='s0',difference=1),dict(scenario_id='s1',difference=1)]
    rejects(lambda:m.paired_scores(a,b[:1]));rejects(lambda:m.paired_scores(a,a+a))
    original=m.schedule(['s0','s1'],['rock','scissors'],7);reordered=m.schedule(['s1','s0'],['scissors','rock'],7)
    keyed=lambda rows:{(r['scenario_id'],r['opponent_id']):(r['scenario_seed'],r['opponent_seed'],r['exploration']) for r in rows}
    assert keyed(original)==keyed(reordered) and len(original)==4
    assert all(r['exploration']==0 for r in original)
    assert original==m.schedule(['s0','s1'],['rock','scissors'],7)
    assert keyed(original)!=keyed(m.schedule(['s0','s1'],['rock','scissors'],19)),"changing the seed must change scenario streams"
    extended=m.schedule(['s0','s1','s2'],['rock','scissors','paper'],7)
    assert all(keyed(extended)[key]==value for key,value in keyed(original).items()),"adding scenarios/opponents changed existing streams"
    assert m.experience(8,128)==1024 and m.experience(1,0)==0
    rejects(lambda:m.experience(0,128));rejects(lambda:m.schedule(['s0','s0'],['rock'],7))
    for x in range(3):
        for y in range(3):
            env=OneRound();env.reset(seed=7);r=m.parallel_round(env,{'A':x,'B':y})
            expected=0 if x==y else (1 if (x-y)%3==1 else -1)
            assert r['rewards']=={'A':expected,'B':-expected} and r['agents']==[]
            assert r['actions_consumed']==2 and r['joint_transitions']==1
            env=parallel_to_aec(OneRound());env.reset(seed=7)
            trace=m.aec_round(env,{'A':x,'B':y})
            assert not env.agents and len(trace)==4
            assert [r['action'] for r in trace]==[x,y,None,None]
            assert trace[0]['observation']==trace[1]['observation']==[0],"pending action leaked"
            assert trace[2]['reward']==expected and trace[3]['reward']==-expected
    env=OneRound();env.reset();rejects(lambda:m.parallel_round(env,{'A':1}))
    # Mixed selected-agent flags: global all(done) is wrong even though RPS ends both together.
    class Mixed:
        agents=['A','B'];terminations={'A':True,'B':False}
        def agent_iter(self):yield 'A';self.agents=[]
        def last(self):return [0],0,True,False,{}
        def step(self,a):assert a is None,"use selected agent's own done flag"
    m.aec_round(Mixed(),{'A':1,'B':0})
''',
 fixtures=dict(paired=[1,1],wrong_pairing=[-5,7],joint_transitions=1024,parallel_live_after=[],aec_actions=[1,0,None,None]))
