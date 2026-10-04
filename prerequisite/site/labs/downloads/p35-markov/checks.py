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

class Draw:
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
