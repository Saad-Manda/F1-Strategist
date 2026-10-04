"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def schedule(scenarios, opponents, master_seed):
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

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
