def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

WEATHER=[[0.8,0.2],[0.3,0.7]]

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

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

