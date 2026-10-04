"""Author the standalone standard-library M2 packs; check without --write for drift."""
import argparse
import json
from build_catalog import LABS
from build_foundation_pages import CONTENT

# Each pack carries its own model/CLI and behavioural oracle; never imports the repository.
SPECS = {
 'p1-state': {
  'functions': '''def encode_state(mode, remaining=None):
    if type(mode) is not int or mode not in (0, 1):
        raise ValueError("mode must be 0 or 1")
    if remaining is not None and (type(remaining) is not int or remaining < 0):
        raise ValueError("remaining must be a nonnegative integer")
    return mode if remaining is None else (mode, remaining)
''',
  'broken': '''def encode_state(mode, remaining=None):
    return 0
''',
  'signatures': ['encode_state(mode, remaining=None)'],
  'common': '''def rollout(encoder, actions, mode=0, seed=7):
    if mode is None:
        import random
        mode = random.Random(seed).randrange(2)
    trace = []
    for action in actions:
        if action not in ("FLIP", "CLAIM"):
            raise ValueError("unknown action")
        before = encoder(mode)
        if action == "FLIP":
            mode = 1 - mode
            reward, terminated = 0, False
        else:
            reward, terminated = (1 if mode == 1 else -1), True
        trace.append(dict(action=action, before=before, observation=encoder(mode),
                          reward=reward, terminated=terminated))
        if terminated:
            break
    return trace

def demo(module):
    return {"claim": rollout(module.encode_state, ["CLAIM"]),
            "flip_claim": rollout(module.encode_state, ["FLIP", "CLAIM"]),
            "horizon_state": module.encode_state(0, 2),
            "seeded_reset_claim": rollout(module.encode_state,["CLAIM"],mode=None,seed=7)}
''',
  'checks': '''def check(module):
    f = module.encode_state
    assert f(0) == 0 and f(1) == 1, "encoder aliases modes"
    assert f(1, 2) == (1, 2) and f(1, 1) == (1, 1), "remaining time is missing"
    from exercise_common import rollout
    a = rollout(f, ["CLAIM"])
    b = rollout(f, ["FLIP", "CLAIM"])
    assert a[-1]["reward"] == -1 and b[-1]["reward"] == 1
    assert a[-1]["before"] != b[-1]["before"], "different futures share an observation"
    for args in [(2,), (True,), (0, -1), (0, 1.5)]:
        rejects(lambda: f(*args))
''',
  'fixtures': {'claim_reward': -1, 'flip_claim_reward': 1, 'finite_state': [1, 2]},
 },
 'p1-return': {
  'functions': '''def returns(rewards, gamma):
    import math
    if not math.isfinite(gamma) or not 0 <= gamma <= 1:
        raise ValueError("gamma must be finite and in [0,1]")
    if any(not math.isfinite(r) for r in rewards):
        raise ValueError("rewards must be finite")
    result, tail = [], 0.0
    for reward in reversed(rewards):
        tail = reward + gamma * tail
        result.append(tail)
    return list(reversed(result))
''',
  'broken': '''def returns(rewards, gamma):
    return [gamma * sum(rewards[t:]) for t in range(len(rewards))]
''',
  'signatures': ['returns(rewards, gamma)'],
  'common': '''def demo(module):
    return {str(gamma): module.returns([2, -1, 4], gamma) for gamma in (0, 0.5, 1)}
''',
  'checks': '''def check(module):
    f = module.returns
    for gamma, target in [(0, [2,-1,4]), (0.5, [2.5,1,4]), (1, [5,3,4])]:
        close_list(f([2,-1,4], gamma), target)
    assert f([], 0.5) == []
    # Independent forward sum, including negative-only and longer trajectories.
    for rewards in [[-3], [1,0,-2,7], [-2,-1,-3], [0,0]]:
        for gamma in (0,0.2,0.8,1):
            target = [sum(gamma**(k-t)*rewards[k] for k in range(t,len(rewards)))
                      for t in range(len(rewards))]
            close_list(f(rewards,gamma),target)
    for gamma in (-0.1,1.1,float("nan"),float("inf")):
        rejects(lambda: f([1],gamma))
    rejects(lambda: f([float("nan")],0.5))
''',
  'fixtures': {'rewards':[2,-1,4], 'returns':{'0':[2,-1,4],'0.5':[2.5,1,4],'1':[5,3,4]}},
 },
 'p1-values': {
  'functions': '''def backup(action_values, policy, legal):
    import math
    if not (len(action_values) == len(policy) == len(legal)) or not any(legal):
        raise ValueError("matching arrays and at least one legal action required")
    if any(not math.isfinite(q) for q in action_values):
        raise ValueError("values must be finite")
    validate_distribution(policy)
    if any(p != 0 for p, allowed in zip(policy, legal) if not allowed):
        raise ValueError("policy has mass on illegal actions")
    return (sum(p*q for p,q,allowed in zip(policy,action_values,legal) if allowed),
            max(q for q,allowed in zip(action_values,legal) if allowed))

def branch_values(gamma, via_probability):
    validate_distribution([via_probability, 1-via_probability])
    validate_distribution([gamma, 1-gamma])
    return backup([3, 1+gamma*4, 99], [1-via_probability, via_probability, 0], [True,True,False])
''',
  'broken': '''def backup(action_values, policy, legal):
    return max(action_values), max(action_values)

def branch_values(gamma, via_probability):
    return backup([3, 1+gamma*4, 99], [1-via_probability, via_probability, 0], [True,True,False])
''',
  'signatures': ['backup(action_values, policy, legal)', 'branch_values(gamma, via_probability)'],
  'common': '''def demo(module):
    return {str(g): module.branch_values(g, 0.5) for g in (0.5,1)}
''',
  'checks': '''def check(module):
    close_list(module.branch_values(0.5,0.5),[3,3])
    close_list(module.branch_values(1,0.5),[4,5])
    close_list(module.branch_values(1,0),[3,5])
    close_list(module.branch_values(1,1),[5,5])
    f=module.backup
    close_list(f([-8,-2,99],[0.25,0.75,0],[True,True,False]),[-3.5,-2])
    close_list(f([999,7],[0,1],[False,True]),[7,7])
    for args in [([1],[1],[False]), ([1,2],[0.5,0.4],[True,True]),
                 ([1,2],[0.5,0.5],[True,False]), ([1],[1,0],[True]),
                 ([1,2],[-1,2],[True,True])]:
        rejects(lambda: f(*args))
    rejects(lambda: module.branch_values(2,0.5))
''',
  'fixtures': {'gamma_half':[3,3], 'gamma_one':[4,5], 'illegal_value':99},
 },
 'p35-backward': {
  'functions': '''def solve(horizon, gamma):
    if type(horizon) is not int or not 0 <= horizon <= 10:
        raise ValueError("horizon must be an integer from 0 to 10")
    validate_distribution([gamma,1-gamma])
    rows=[dict(A=0.0,B=0.0,T=0.0,action=None)]
    for h in range(1,horizon+1):
        previous=rows[-1]
        values={s: {a: reward + gamma*previous[next_state]
                    for a,(next_state,reward) in actions.items()}
                for s,actions in MODEL.items()}
        action=max(values["A"],key=values["A"].get)
        rows.append(dict(A=values["A"][action], B=max(values["B"].values()), T=0.0,action=action))
    return rows
''',
  'broken': '''def solve(horizon, gamma):
    rows=[dict(A=0.0,B=0.0,T=0.0,action=None)]
    for h in range(1,horizon+1):
        via=1+gamma*4  # Uses the eventual B value even with no time to collect it.
        rows.append(dict(A=max(3,via),B=4,T=0,action="VIA" if via>3 else "DIRECT"))
    return rows
''',
  'signatures': ['solve(horizon, gamma)'],
  'common': '''MODEL={"A":{"DIRECT":("T",3),"VIA":("B",1)},"B":{"FINISH":("T",4)}}

def demo(module):
    return module.solve(2,1)
''',
  'checks': '''def paths(state, remaining, rewards=()):
    # Exhaustive trajectories on an independently specified tiny world.
    if state == "T" or remaining == 0:
        return [rewards]
    edges = {"A": [("T",3),("B",1)], "B": [("T",4)]}[state]
    return [path for successor,reward in edges
            for path in paths(successor,remaining-1,rewards+(reward,))]

def check(module):
    for horizon in range(6):
        for gamma in (0,0.25,0.5,0.75,1):
            rows=module.solve(horizon,gamma)
            assert len(rows)==horizon+1, "one row per remaining horizon required"
            for h,values in enumerate(rows):
                for state in ("A","B","T"):
                    target=max(sum(gamma**i*r for i,r in enumerate(path)) for path in paths(state,h))
                    close(values[state],target)
                if h == 0:
                    assert values["action"] is None
                else:
                    assert values["action"] in ("DIRECT","VIA")
                    # Accept either action in an exact tie.
                    action_value=3 if values["action"]=="DIRECT" else 1+gamma*(4 if h>1 else 0)
                    close(action_value,values["A"])
    assert module.solve(1,1)[1]["action"]=="DIRECT"
    assert module.solve(2,1)[2]["action"]=="VIA"
    for args in [(-1,1),(1.5,1),(11,1),(2,-0.1),(2,float("nan"))]:
        rejects(lambda: module.solve(*args))
''',
  'fixtures': {'gamma':1,'horizon_values':[0,3,5],'actions':[None,'DIRECT','VIA']},
 },
 'p35-stochastic': {
  'functions': '''def expected_value(outcomes):
    import math
    if not outcomes:
        raise ValueError("outcomes must not be empty")
    validate_distribution([p for p,r in outcomes])
    if any(not math.isfinite(r) for p,r in outcomes):
        raise ValueError("rewards must be finite")
    return sum(p*r for p,r in outcomes)
''',
  'broken': '''def expected_value(outcomes):
    return max(outcomes,key=lambda outcome: outcome[0])[1]
''',
  'signatures': ['expected_value(outcomes)'],
  'common': '''def demo(module):
    import random
    rng=random.Random(7)
    return {"expectations": {str(p): module.expected_value([(p,10),(1-p,-2)]) for p in (0.25,0.5,1/3)},
            "seeded_risky_rewards_p_025": [10 if rng.random()<0.25 else -2 for _ in range(10)]}
''',
  'checks': '''def check(module):
    f=module.expected_value
    for p,target in [(0.25,1),(0.5,4),(1/3,2),(0,-2),(1,10)]:
        close(f([(p,10),(1-p,-2)]),target)
    close(f([(0.2,-5),(0.3,0),(0.5,8)]),3)
    close(f([(1,2)]),2)
    close(f([(0,999),(1,-3)]),-3)
    for outcomes in [[],[(-0.1,2),(1.1,3)],[(0.4,2),(0.4,3)],
                     [(float("nan"),1)],[(1,float("inf"))]]:
        rejects(lambda: f(outcomes))
''',
  'fixtures': {'win_reward':10,'loss_reward':-2,'risk_values':{'0.25':1,'0.5':4,'1/3':2}},
 },
 'p35-markov': {
  'functions': '''def advance(distribution, matrix):
    validate_matrix(matrix)
    validate_distribution(distribution)
    if len(distribution)!=len(matrix):
        raise ValueError("distribution dimension mismatch")
    return [sum(p*matrix[i][j] for i,p in enumerate(distribution)) for j in range(len(matrix))]

def sample_next(state, rng, matrix):
    validate_matrix(matrix)
    if type(state) is not int or not 0 <= state < len(matrix):
        raise ValueError("invalid state")
    draw=rng.random()
    if not 0 <= draw < 1:
        raise ValueError("random() must return a value in [0,1)")
    cumulative=0.0
    for next_state,probability in enumerate(matrix[state]):
        cumulative+=probability
        if draw<cumulative:
            return next_state
    return len(matrix)-1  # Floating-point roundoff only.

def decision_values(state, matrix):
    validate_matrix(matrix)
    if len(matrix)!=2 or type(state) is not int or state not in (0,1):
        raise ValueError("prediction task needs two states")
    return dict(NONE=matrix[state][0],UMBRELLA=matrix[state][1])
''',
  'broken': '''def advance(distribution, matrix):
    return [sum(distribution[j]*matrix[i][j] for j in range(len(matrix))) for i in range(len(matrix))]

def sample_next(state, rng, matrix):
    return max(range(len(matrix)),key=lambda j:matrix[state][j])

def decision_values(state, matrix):
    return dict(NONE=1,UMBRELLA=1)
''',
  'signatures': ['advance(distribution, matrix)','sample_next(state, rng, matrix)','decision_values(state, matrix)'],
  'common': '''WEATHER=[[0.8,0.2],[0.3,0.7]]

def validate_matrix(matrix):
    if not matrix or any(len(row)!=len(matrix) for row in matrix):
        raise ValueError("matrix must be nonempty and square")
    for row in matrix:
        validate_distribution(row)

def demo(module):
    import random
    distribution=[1,0]
    state=0
    rng=random.Random(7)
    trace=[]
    for step in range(1,11):
        distribution=module.advance(distribution,WEATHER)
        state=module.sample_next(state,rng,WEATHER)
        trace.append(dict(step=step,distribution=distribution,sample=state,
                          terminated=False,truncated=step==10))
    return dict(trace=trace,prediction_values=module.decision_values(0,WEATHER),foresight_bound=1)
''',
  'checks': '''class Draw:
    def __init__(self,value): self.value=value
    def random(self): return self.value

def check(module):
    import random
    matrix=[[0.8,0.2],[0.3,0.7]]
    close_list(module.advance([1,0],matrix),[0.8,0.2])
    close_list(module.advance([0.8,0.2],matrix),[0.7,0.3])
    close_list(module.advance([0.6,0.4],matrix),[0.6,0.4])
    close_list(module.advance([0,1],matrix),[0.3,0.7])
    close_list(module.advance([1,0,0],[[0,1,0],[0,0,1],[1,0,0]]),[0,1,0])
    for state,draw,target in [(0,0,0),(0,0.799,0),(0,0.8,1),(0,0.999,1),(1,0.299,0),(1,0.3,1)]:
        assert module.sample_next(state,Draw(draw),matrix)==target, "categorical interval mismatch"
    for state,probability in [(0,0.8),(1,0.3)]:
        # Independent one-step draws, not a continuing-chain stationary-frequency test.
        for seed in (7,31,89):
            rng=random.Random(seed)
            frequency=sum(module.sample_next(state,rng,matrix)==0 for _ in range(10000))/10000
            assert abs(frequency-probability)<0.02, "seeded sample frequency exceeds explicit 0.02 tolerance"
    rng1,rng2=random.Random(9),random.Random(9)
    assert [module.sample_next(0,rng1,matrix) for _ in range(20)]==[module.sample_next(0,rng2,matrix) for _ in range(20)]
    for state,expected in [(0,{"NONE":0.8,"UMBRELLA":0.2}),(1,{"NONE":0.3,"UMBRELLA":0.7})]:
        values=module.decision_values(state,matrix)
        for action,target in expected.items(): close(values[action],target)
        assert max(values.values())<1, "model knowledge is not perfect foresight"
    close_list(module.advance([1],[[1]]),[1])
    for invalid in [[],[[0.8,0.1],[0.3,0.7]],[[-0.1,1.1],[0.3,0.7]],[[1,0],[0,1,0]]]:
        rejects(lambda: module.advance([1,0],invalid))
    rejects(lambda: module.sample_next(2,Draw(0.5),matrix))
    rejects(lambda: module.sample_next(0,Draw(1),matrix))
    rejects(lambda: module.advance([1],matrix))
''',
  'fixtures': {'matrix':[[0.8,0.2],[0.3,0.7]],'two_step':[0.7,0.3],'stationary':[0.6,0.4], 'attainable_dry':0.8,'foresight':1},
 },
}

VALIDATION = '''def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

'''
RUNNER = '''def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

'''
CHECK_HELPERS = '''"""Behaviour checks. No reference-solution import; alternate correct implementations welcome."""
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

'''
CHECK_MAIN = '''
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
'''


def outputs(specs=None, content_data=None):
    specs = SPECS if specs is None else specs
    content_data = CONTENT if content_data is None else content_data
    result={}
    for key,spec in specs.items():
        folder=LABS/'downloads'/key
        common=VALIDATION+spec['common']+'\n'+RUNNER
        prefix='"""Standalone RL exercise. Standard library only."""\nfrom exercise_common import *\n\n'
        suffix='\nif __name__ == "__main__":\n    import sys\n    run(sys.modules[__name__])\n'
        starter='\n\n'.join(f'def {signature}:\n    # TODO: implement the contract described in README.md.\n    raise NotImplementedError("Complete {signature.split("(")[0]}")' for signature in spec['signatures'])+'\n'
        files={'solution.py':prefix+spec['functions']+suffix,'broken.py':prefix+spec['broken']+suffix,
               'starter.py':prefix+starter+suffix,'exercise_common.py':common,
               'checks.py':CHECK_HELPERS+spec['checks']+CHECK_MAIN,
               'fixtures.json':json.dumps(spec['fixtures'],indent=2)+'\n',
               'requirements.txt':'# Python 3.10+ standard library only. No packages to install.\n'}
        c=content_data[key]
        signatures='\n'.join(f'- `{s}`' for s in spec['signatures'])
        sampling_note = ('The weather checker uses 10,000 independent draws for each of three seeds per row,\n'
                         'with explicit frequency tolerance 0.02; it also checks categorical boundaries exactly.\n') if key=='p35-markov' else ''
        files['README.md']=f'''# {key}: {c['question']}

Python 3.10+; standard library only. Tested with Python 3.12.7.
Extract this archive anywhere. Open PowerShell or another terminal in this folder:

```text
python broken.py
python checks.py --candidate broken.py
python starter.py
python checks.py --candidate starter.py
```

`broken.py` runs but intentionally fails checks. Fix a copy or complete the TODOs in
`starter.py`. The untouched starter exits with “Exercise incomplete”; this is expected.
Pass your own filename to `--candidate`. Tests import only that file and this pack's
helpers; they never import the reference solution or the F1 repository.

## Contract

{c['task']}

Functions to implement:

{signatures}

Inputs are Python lists/numbers as described. Invalid inputs raise `ValueError`.
`exercise_common.py` supplies only validation, model data, and the demo CLI, so focus on
the RL concept. `fixtures.json` holds small hand-calculated examples; checks also use
additional cases. Floating-point comparisons use absolute/relative tolerance 1e-9;
probability normalization uses tolerance 1e-10. Tied optimal actions are both accepted.

Browser computations and Python should agree on exact mathematics. Seeded sampled
paths are reproducible within each implementation: browser uses an LCG, Python uses
`random.Random`, so matching numeric seeds do not imply identical cross-language paths.
{sampling_note}

## Optional help

Return to the webpage to request individual hints. The file `solution.py` contains the
reference answer; open it only when you want it. To check the reference explicitly:

```text
python checks.py --candidate solution.py
```

Explain and transfer: {c['reflect']}

Optional extension: change one model reward or transition probability. Calculate the
new expected results before running your implementation. Original checks still target
the original model; update your extension's independent witnesses separately.
'''
        files.update(spec.get('extras', {}))
        files['README.md'] += spec.get('readmeExtra', '')
        for filename,content in files.items(): result[folder/filename]=content
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    for path,content in outputs().items():
        if args.write:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content,encoding='utf-8')
        elif not path.exists() or path.read_text(encoding='utf-8')!=content:
            raise SystemExit(f'Stale pack file: {path}. Run build_foundation_packs.py --write.')
    print('Six M2 packs '+('generated.' if args.write else 'are current.'))


if __name__=='__main__': main()
