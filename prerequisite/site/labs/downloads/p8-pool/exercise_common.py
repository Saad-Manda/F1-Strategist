import math
def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

import numpy as np
MATRIX=((0,-1,1),(1,0,-1),(-1,1,0))
def action(a):
    if type(a) is not int or a not in (0,1,2):raise ValueError("action must be integer 0,1,2")
def policy(p):
    if len(p)!=3:raise ValueError("three probabilities required")
    validate_distribution(p)
validate_action=action
validate_policy=policy
def validate_policy(p):
    values=np.asarray(p,dtype=float)
    if values.ndim!=1 or len(values)!=3:raise ValueError("length-three policy vector required")
    policy(values.tolist())
def demo(m):
    learner=np.array([.2,.3,.5]);saved=m.snapshot(learner);learner[:]=[1,0,0]
    return dict(saved=saved.tolist(),current=learner.tolist(),weights=m.pool_probabilities([1,2,3]).tolist(),paper_coverage=list(m.coverage([0,1,0])))

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

