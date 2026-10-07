"""Execute teaching examples and independent numerical/contract witnesses."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest
from test_reading_shell import Elements, ROOT


def code(path):
    parser=Elements();parser.feed((ROOT/'content'/path).read_text(encoding='utf-8'))
    return [block for block in parser.code if '\n' in block]


def pack(lab):
    path=ROOT/f'site/labs/downloads/{lab}/solution.py'
    spec=importlib.util.spec_from_file_location(lab.replace('-','_')+'_witness',path)
    module=importlib.util.module_from_spec(spec)
    previous=sys.modules.pop('exercise_common',None)
    sys.path.insert(0,str(path.parent))
    try: spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
        sys.modules.pop('exercise_common',None)
        if previous is not None:sys.modules['exercise_common']=previous
    return module


def test_state_return_and_value_examples_agree_with_delivered_contracts():
    ns={}
    for name in ['state-observation','markov-property','missing-information']:
        for block in code(f'readings/p1-state/{name}.html'):exec(block,ns)
    reference=pack('p1-state')
    for mode in [0,1]:
        for remaining in [None,0,2]:assert ns['encode_state'](mode,remaining)==reference.encode_state(mode,remaining)
    for bad in [(True,None),(2,None),(0,-1),(1,2.5)]:
        with pytest.raises(ValueError):ns['encode_state'](*bad)
    for block in code('readings/p1-return/return-calculation.html'):exec(block,ns)
    reference=pack('p1-return')
    for gamma,expected in [(0,[2,-1,4]),(.5,[2.5,1,4]),(1,[5,3,4])]:
        assert ns['returns']([2,-1,4],gamma)==expected==reference.returns([2,-1,4],gamma)
    for name in ['probability-outcomes','weighted-expectation']:
        for block in code(f'readings/p1-probability/{name}.html'):exec(block,ns)
    for bad in [[.7,.1],[1.1,-.1],[float('nan'),1],[]]:
        with pytest.raises(ValueError):ns['validate_distribution'](bad)
    for name in ['policies-legal-actions','bellman-backup','expectation-maximization','bellman-fixed-points']:
        for block in code(f'readings/p1-values/{name}.html'):exec(block,ns)
    reference=pack('p1-values')
    assert ns['backup']([3,5,99],[.5,.5,0],[True,True,False])==(4,5)==reference.backup([3,5,99],[.5,.5,0],[True,True,False])
    assert ns['outcome_backup']([(1,-7,10,True)],.5)==-7
    assert ns['outcome_backup']([(1,-7,10,False)],.5)==-2


def application_namespace():
    ns={}
    for name in ['environment-contract','race-dynamics','reward-units','environment-verification']:
        for block in code(f'applications/foundations/{name}.html'):exec(block,ns)
    return ns


def test_race_pit_order_cliff_components_and_safety_car_witnesses():
    ns=application_namespace()
    assert ns['toy_wear']('A',8)==pytest.approx(2.8)
    assert ns['toy_wear']('A',10)==pytest.approx(4.5)
    assert ns['toy_wear']('A',16)==pytest.approx(4.8)
    assert ns['toy_wear']('A',100)==pytest.approx(9.0)
    state=dict(remaining=4,age=8,compound='A',weather=0,safety_car=False)
    before=dict(state)
    after,reward,done=ns['toy_transition'](state,2)
    assert state==before
    assert reward==pytest.approx(-5.8064) and not done
    assert (after['compound'],after['age'],after['remaining'])==('B',1,3)
    assert ns['toy_lap_time'](after)==pytest.approx(1.9248)
    state['safety_car']=True
    assert ns['toy_transition'](state,2)[1]==pytest.approx(-8.8)
    assert ns['sample_safety_cars'](np.random.default_rng(7),52)==ns['sample_safety_cars'](np.random.default_rng(7),52)
    assert ns['sample_safety_cars'](np.random.default_rng(7),10,hazard=0)==[False]*10
    assert ns['sample_safety_cars'](np.random.default_rng(7),10,hazard=1)==[True]*10


def test_centering_preserves_physics_flags_and_only_common_horizon_rankings():
    ns=application_namespace()
    env=ns['CenteredReward'](ns['ToyRaceEnv'](),offset=2)
    env.reset(seed=7)
    raw=centered=time=0
    for _ in range(10):
        obs,reward,terminated,truncated,info=env.step(0)
        centered+=reward;raw+=info['raw_reward'];time+=info['lap_time']
    assert terminated and not truncated
    assert raw==pytest.approx(-time)
    assert centered-raw==pytest.approx(20)
    env.close()
    import gymnasium as gym
    env=gym.wrappers.TimeLimit(ns['ToyRaceEnv'](),max_episode_steps=2)
    env.reset(seed=7);env.step(0)
    assert env.step(0)[2:4]==(False,True)
    env.close()
    assert -10 > -11 and -10+2 < -11+4  # variable length changes rank
    assert sum([-93,-97]) < sum([-97,-92])
    assert -93-.5*97 > -97-.5*92  # discount reverses physical ranking
