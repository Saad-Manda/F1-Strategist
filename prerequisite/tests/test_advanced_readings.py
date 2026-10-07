"""R6 numerical, gradient, boundary and real API witnesses, without training runs."""
import itertools
import json
import math
import pickle
import subprocess
import sys
import threading

import numpy as np
import pytest
import torch

from test_foundations_readings import code, pack
from test_reading_shell import ROOT


@pytest.fixture(scope='module')
def advanced():
    course=json.loads((ROOT/'content/course-registry.json').read_text(encoding='utf-8'))
    result={}
    for module in ('multiple-agents','self-play','policy-gradients'):
        ns={'__name__':'reading_example'}
        for reading in course['readings']:
            if reading['module']==module:
                for block in code(reading['source'].removeprefix('content/')):
                    exec(compile(block,reading['source'],'exec'),ns)
        result[module]=ns
    previous=torch.get_num_threads();torch.set_num_threads(1)
    yield result
    torch.set_num_threads(previous)


def test_joint_reward_and_counterfactual_credit(advanced):
    ns=advanced['multiple-agents'];reference=pack('p6-credit')
    for a,b in itertools.product((0,1),repeat=2):
        actions={'A':a,'B':b}
        assert ns['joint_step'](actions)==reference.joint_step(actions)
        assert ns['contributions'](actions)=={'A':2*a,'B':b}==reference.contributions(actions)
        assert actions=={'A':a,'B':b}
    for actions in ({'A':True,'B':1},{'A':1},{'A':2,'B':0}):
        with pytest.raises(ValueError):ns['joint_step'](actions)


def test_shaping_routes_discount_and_boundary_counterexamples(advanced):
    ns=advanced['multiple-agents'];reference=pack('p6-shaping')
    routes=[([3],[2,0]),([0,4],[2,1,0]),([0,0],[2,1,0])]
    for gamma,expected in [(1,[1,2,-2]),(.5,[1,0,-2])]:
        actual=[ns['shaped_return'](r,p,gamma) for r,p in routes]
        assert actual==expected
        assert actual==[reference.shaped_return(r,p,gamma) for r,p in routes]
        for r,p in routes:
            base=sum(gamma**t*x for t,x in enumerate(r))
            assert ns['shaped_return'](r,p,gamma)-base==pytest.approx(-p[0]+gamma**len(r)*p[-1])
    assert ns['shaped_return']([0,0],[2,1,10],1)==8
    assert ns['shaped_return']([0,4],[2,1,0],.5,1)==.5
    for args in [([1],[2],1),([1],[2,0],1.1),([float('nan')],[2,0],1)]:
        with pytest.raises(ValueError):ns['shaped_return'](*args)


def test_connected_lane_and_physical_traffic_intervention(advanced):
    ns=advanced['multiple-agents'];reference=pack('p6-opponent')
    for p in (0,.2,.8,1):
        for blocking in (False,True):
            assert ns['expected_lane'](p,blocking)==reference.expected_lane(p,blocking)
    for action,occupied,blocking in itertools.product(('CROSS','WAIT'),(False,True),(False,True)):
        assert ns['lane_reward'](action,occupied,blocking)==reference.lane_reward(action,occupied,blocking)
    assert [ns['dirty_air'](x) for x in (0,.75,1.5)]==[.5,.25,0]
    assert ns['pass_probability'](-.5,.5,0)==.5
    assert ns['pass_probability'](-1,.5,0)==pytest.approx(.92414181998)
    assert ns['pass_probability'](-1.5,.5,0)==.95
    assert ns['pass_probability'](-.5,.5,2)==.7
    assert ns['pass_probability'](-1,1,3)==0
    assert ns['pass_probability'](0,.5,3)==0
    times,paces=[0,.5],[5,4.5]
    blocked=ns['traffic_step'](times,paces)
    assert blocked==pytest.approx([5,35/6])
    assert blocked[1]-blocked[0]>=times[1]-times[0]
    assert ns['traffic_step'](times,paces,pass_success=True)==[5,5]
    assert ns['traffic_step'](times,paces,blocking=False)==[5,5]
    assert times==[0,.5] and paces==[5,4.5]
    assert 30*4.5+20==155 and 30*5==150


def test_payoff_best_response_and_snapshot_coverage(advanced):
    ns=advanced['self-play'];game=pack('p8-game');pool=pack('p8-pool')
    for p,q in itertools.product(np.eye(3).tolist()+[[1/3]*3],repeat=2):
        assert ns['expected_payoff'](p,q)==pytest.approx(game.expected_payoff(p,q))
        assert ns['coverage'](p)==pytest.approx(pool.coverage(p))
    assert ns['best_response']([.5,.25,.25])==[1]
    assert ns['best_response']([1/3]*3)==[0,1,2]
    assert ns['action_update']([0,0,0],1,1,.1)==[0,.1,0]
    policy=np.array([1.,0.,0.]);snapshot=ns['snapshot'](policy)
    policy[:]=[0,1,0]
    assert snapshot.tolist()==[1,0,0] and not np.shares_memory(snapshot,policy)
    with pytest.raises(ValueError):snapshot[0]=0
    retained=[]
    for p in np.eye(3):retained=ns['add_snapshot'](retained,p,2)
    assert [p.tolist() for p in retained]==[[0,1,0],[0,0,1]]


def test_pool_probabilities_one_entry_and_sample_stream(advanced):
    ns=advanced['self-play'];reference=pack('p8-pool')
    assert ns['pool_probabilities']([1,2,3])==pytest.approx([1/6,1/3,1/2])
    assert ns['pool_probabilities']([1e308,1e308])==pytest.approx([.5,.5])
    for seed in (7,19,31):
        actual=ns['sample_indices']([1,2,3],10000,seed)
        assert np.array_equal(actual,reference.sample_indices([1,2,3],10000,seed))
        assert np.bincount(actual,minlength=3)/len(actual)==pytest.approx([1/6,1/3,1/2],abs=.02)
    assert ns['recency_probabilities'](1).tolist()==[1]
    for n in (2,3,5,50):
        p=ns['recency_probabilities'](n)
        assert p.sum()==pytest.approx(1) and np.all(p>0)
    p=ns['recency_probabilities'](50)
    assert p[:40]==pytest.approx([.0075]*40)
    assert p[40:]==pytest.approx([.07]*10)
    for weights in ([],[0,1],[float('nan')],[-1,2]):
        with pytest.raises(ValueError):ns['pool_probabilities'](weights)


def test_identity_pairing_schedules_and_budget(advanced):
    ns=advanced['self-play'];reference=pack('p8-audit')
    a=[{'scenario_id':'s0','score':2},{'scenario_id':'s1','score':8}]
    b=[{'scenario_id':'s1','score':7},{'scenario_id':'s0','score':1}]
    assert ns['paired_scores'](a,b)==reference.paired_scores(a,b)
    assert [r['difference'] for r in ns['paired_scores'](a,b)]==[1,1]
    for bad in (b[:1],[*b,b[0]]):
        with pytest.raises(ValueError):ns['paired_scores'](a,bad)
    expected=reference.schedule(['s0','s1'],['rock','scissors'],7)
    assert ns['schedule'](['s0','s1'],['rock','scissors'],7)==expected
    assert ns['experience'](8,128)==1024
    assert np.std([1,2,3,4],ddof=1)/2==pytest.approx(math.sqrt(5/3)/2)


def test_actual_parallel_and_aec_lifecycle(advanced):
    # Load the unchanged real API fixture through the pack's isolated import.
    reference=pack('p8-audit');ns=advanced['self-play']
    env=reference.OneRound();env.reset(seed=7)
    result=ns['parallel_round'](env,{'A':1,'B':0})
    assert result['rewards']=={'A':1,'B':-1} and result['agents']==[]
    assert result['actions_consumed']==2 and result['joint_transitions']==1
    with pytest.raises(ValueError):ns['parallel_round'](env,{})
    aec=reference.parallel_to_aec(reference.OneRound());aec.reset(seed=7)
    trace=ns['aec_round'](aec,{'A':1,'B':0})
    assert [r['action'] for r in trace]==[1,0,None,None]
    assert trace[-2]['terminated'] and trace[-1]['terminated']
    assert aec.agents==[]
    env.close();aec.close()


def test_scores_expected_gradient_and_reinforce_sgd(advanced):
    ns=advanced['policy-gradients'];reference=pack('p9-reinforce')
    p,score=ns['score_vector']([1,0],0)
    assert p==pytest.approx([.7310585786,.2689414214])
    assert score==pytest.approx([1-p[0],-p[1]])
    mean=sum(p[a]*ns['score_vector']([1,0],a)[1] for a in range(2))
    assert mean==pytest.approx([0,0],abs=1e-14)
    logits=torch.zeros((1,2),dtype=torch.float64,requires_grad=True)
    actions=torch.tensor([0]);returns=torch.tensor([2.],requires_grad=True)
    loss=ns['reinforce_loss'](logits,actions,returns)
    assert loss.item()==pytest.approx(reference.reinforce_loss(logits,actions,returns).item())
    loss.backward();assert logits.grad.tolist()==[[-1,1]] and returns.grad is None
    updated=logits.detach()-.1*logits.grad
    assert torch.softmax(updated,1)[0,0].item()==pytest.approx(.5498339973)
    mask=torch.tensor([[True,True,False]])
    masked=torch.tensor([[0.,0.,100.]],dtype=torch.float64)
    assert ns['probabilities'](masked,mask).tolist()==[[.5,.5,0]]
    with pytest.raises(ValueError):ns['reinforce_loss'](masked,torch.tensor([2]),torch.ones(1),mask)


def test_start_discounted_score_identity():
    # Exact enumeration: shared Bernoulli policy, rewards a0 and a1.
    p=.3;gamma=.5;gradient=0.;missing_time_weight=0.
    for a0,a1 in itertools.product((0,1),repeat=2):
        probability=(p if a0 else 1-p)*(p if a1 else 1-p)
        g0=a0+gamma*a1;g1=a1
        gradient+=probability*((a0-p)*g0+gamma*(a1-p)*g1)
        missing_time_weight+=probability*((a0-p)*g0+(a1-p)*g1)
    assert gradient==pytest.approx((1+gamma)*p*(1-p))
    assert missing_time_weight!=pytest.approx(gradient)


def test_baseline_expected_score_and_variance():
    scores=np.array([.5,-.5]);returns=np.array([8,2])
    raw=scores*returns;good=scores*(returns-5);bad=scores*(returns-20)
    assert raw.mean()==good.mean()==bad.mean()==1.5
    assert (raw.var(),good.var(),bad.var())==(6.25,0,56.25)
    assert np.mean(scores*np.array([1,0]))==.25


def test_separate_actor_critic_gradients(advanced):
    ns=advanced['policy-gradients'];reference=pack('p9-advantage')
    logs=torch.full((2,),math.log(.5),requires_grad=True)
    values=torch.tensor([5.,5.],requires_grad=True)
    targets=torch.tensor([8.,2.],requires_grad=True)
    advantage=ns['advantages'](targets,values)
    assert advantage.tolist()==[3,-3] and not advantage.requires_grad
    loss=ns['actor_loss'](logs,advantage)
    assert loss.item()==0;loss.backward()
    assert logs.grad.tolist()==[-1.5,1.5] and values.grad is None and targets.grad is None
    critic=ns['critic_loss'](values,targets)
    assert critic.item()==reference.critic_loss(values,targets).item()==9
    critic.backward();assert values.grad.tolist()==[-3,3] and targets.grad is None
    with pytest.raises(ValueError):ns['actor_loss'](logs,advantage[:,None])


def test_gae_examples_recursion_and_reset_barrier(advanced):
    ns=advanced['policy-gradients'];reference=pack('p9-gae')
    for terminated,next_values,lam,expected in [([False,True],[1,999],1,[2.3,1]),
                                               ([False,False],[1,3],1,[4.73,3.7]),
                                               ([False,False],[1,3],.5,[3.065,3.7])]:
        args=([1,2],[.5,1],next_values,np.array(terminated),np.array([True,False]),.9,lam)
        a,target=ns['gae'](*args)
        assert a==pytest.approx(expected)
        assert a==pytest.approx(reference.gae(*args)[0])
        assert target==pytest.approx(a+np.array([.5,1]))
    args=([-3,-2,-3,-2],[-10,-6,-5,-1],[-6,-5,-1,0],np.array([False,False,False,True]),np.array([True,True,True,False]),1,.95)
    assert ns['gae'](*args)[0]==pytest.approx([.095125,-.9525,.05,-1])
    a,_=ns['gae']([2,100],[1,0],[3,0],np.array([False,True]),np.array([False,False]),.9,1)
    assert a.tolist()==pytest.approx([3.7,100])
    with pytest.raises(ValueError):ns['gae']([1],[0],[0],np.array([True]),np.array([True]))


def test_ppo_frozen_storage_branches_and_diagnostics(advanced):
    ns=advanced['policy-gradients'];reference=pack('p9-ppo')
    old=torch.zeros(4,dtype=torch.float64,requires_grad=True);saved=ns['frozen'](old)
    with torch.no_grad():old.add_(9)
    assert saved.tolist()==[0]*4 and not saved.requires_grad and saved.data_ptr()!=old.data_ptr()
    new=torch.tensor([1.3,.7,.7,1.3],dtype=torch.float64).log().requires_grad_()
    advantage=torch.tensor([1.,1.,-1.,-1.],dtype=torch.float64,requires_grad=True)
    loss=ns['ppo_loss'](new,saved,advantage)
    assert loss.item()==pytest.approx(.05)==pytest.approx(reference.ppo_loss(new,saved,advantage).item())
    loss.backward();assert new.grad.tolist()==pytest.approx([0,-.175,0,.325])
    assert advantage.grad is None and old.grad is None
    for index,objective in enumerate([1.2,.7,-.8,-1.3]):
        assert -ns['ppo_loss'](new[index:index+1],saved[index:index+1],advantage[index:index+1]).item()==pytest.approx(objective)
    diagnostic=ns['diagnostics'](new,saved,advantage)
    assert diagnostic['clip_fraction']==1
    assert diagnostic['approx_kl']==pytest.approx(np.mean(np.array([1.3,.7,.7,1.3])-1-np.log([1.3,.7,.7,1.3])))
    assert ns['ppo_loss'](new,saved,advantage,0).isfinite()
    with pytest.raises(ValueError):ns['ppo_loss'](torch.tensor([1000.]),torch.zeros(1),torch.ones(1))


def test_ppo_clip_is_not_a_hard_ratio_bound(advanced):
    ns=advanced['policy-gradients']
    logits=torch.zeros((1,2),dtype=torch.float64,requires_grad=True)
    old=torch.tensor([math.log(.5)],dtype=torch.float64)
    new=torch.log_softmax(logits,1)[:,1]
    loss=ns['ppo_loss'](new,old,torch.tensor([8.],dtype=torch.float64))
    loss.backward()
    updated=logits.detach()-2*logits.grad
    assert updated.tolist()==[[-8,8]]
    ratio=float(torch.softmax(updated,1)[0,1]/.5)
    assert ratio>1.2 and ratio==pytest.approx(1.9999997749)


def test_worker_serializer_and_actual_ordinary_spawn(advanced,tmp_path):
    ns=advanced['policy-gradients']
    from stable_baselines3.common.vec_env.base_vec_env import CloudpickleWrapper
    factory=lambda:{'tag':0}
    with pytest.raises((pickle.PicklingError,AttributeError)):pickle.dumps(factory)
    assert pickle.loads(pickle.dumps(CloudpickleWrapper(factory))).var()=={'tag':0}
    lock=threading.Lock();captured=lambda:lock
    with pytest.raises(TypeError):pickle.dumps(CloudpickleWrapper(captured))
    source='\n\n'.join(code('applications/policy-gradients/workers.html'))
    script=tmp_path/'spawn_witness.py';script.write_text(source,encoding='utf-8')
    result=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,timeout=50)
    assert result.returncode==0,result.stdout+result.stderr
    assert result.stdout.strip()=='0'


def test_actual_vector_reset_masks_and_proposal_budgets(advanced):
    ns=advanced['policy-gradients']
    assert ns['rollout_budget'](2000000,256,4,64,10)==dict(rollout_transitions=1024,
        actual_transitions=2000896,minibatches_per_epoch=16,optimizer_steps_per_rollout=160)
    assert 2000000/(5000*52)==pytest.approx(7.6923076923)
    assert 16*128==2048
    import gymnasium as gym
    from stable_baselines3.common.vec_env import DummyVecEnv
    class Ending(gym.Env):
        observation_space=gym.spaces.Box(0,3,(1,),dtype=np.float32)
        action_space=gym.spaces.Discrete(3)
        def reset(self,seed=None,options=None):
            super().reset(seed=seed);self.t=0
            return np.array([0],dtype=np.float32),{}
        def action_masks(self):return np.array([True,True,False])
        def step(self,action):
            self.t+=1
            return np.array([self.t],dtype=np.float32),0.,False,self.t==2,{}
    env=DummyVecEnv([Ending])
    try:
        env.reset();env.step([0]);obs,rewards,dones,infos=env.step([0])
        assert obs.tolist()==[[0]] and dones.tolist()==[True]
        assert infos[0]['terminal_observation'].tolist()==[2]
        assert infos[0]['TimeLimit.truncated']
        assert env.env_method('action_masks')[0].tolist()==[True,True,False]
    finally:env.close()


def test_advanced_coverage_preserves_frozen_mapping_and_ppo_independence():
    original=json.loads((ROOT/'curriculum/coverage-map.json').read_text(encoding='utf-8'))
    frozen={s['id']:s for s in original['sections']}
    mapping=json.loads((ROOT/'content/advanced-coverage.json').read_text(encoding='utf-8'))
    course=json.loads((ROOT/'content/course-registry.json').read_text(encoding='utf-8'))
    advanced_ids={r['id'] for r in course['readings'] if r['module'] in ('multiple-agents','self-play','policy-gradients')}
    assert len(advanced_ids)==54 and len(mapping['sections'])==178
    assert advanced_ids<={d for s in mapping['sections'] for d in s['authoredDestinations']}
    for s in mapping['sections']:
        old=frozen[s['legacySection']]
        for key in ('destinations','disposition','rationale'):assert s[key]==old[key]
    prerequisites={l['id']:l['prerequisites'] for l in course['lessons']}
    def ancestors(id):
        return {p for p in prerequisites[id]}|{a for p in prerequisites[id] for a in ancestors(p)}
    for lesson in course['lessons']:
        if lesson['module']=='policy-gradients':
            assert not any(p.startswith(('p6-','p8-')) for p in ancestors(lesson['id']))
