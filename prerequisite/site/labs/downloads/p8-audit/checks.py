"""Behaviour checks. No reference-solution import; alternate correct implementations welcome."""
import argparse
import importlib.util
import math
from pathlib import Path
import sys

def close(actual,expected):
    assert math.isfinite(actual) and math.isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-9), f"expected {expected}, got {actual}"

def close_list(actual,expected):
    assert len(actual)==len(expected), "wrong result length"
    for a,b in zip(actual,expected): close(a,b)

def rejects(call):
    try: call()
    except ValueError: return
    raise AssertionError("invalid input must raise ValueError")

def load_candidate(path):
    path=Path(path).resolve()
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location("candidate",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def check(m):
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

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate",default="starter.py")
    args=parser.parse_args()
    try:
        check(load_candidate(args.candidate))
    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}")
        raise SystemExit(1)
    print("PASS: all behavioural and boundary checks")

if __name__=="__main__": main()
