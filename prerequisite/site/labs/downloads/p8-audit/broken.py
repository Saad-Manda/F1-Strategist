"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def schedule(scenarios, opponents, master_seed):
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

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
