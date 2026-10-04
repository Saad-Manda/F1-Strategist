def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

def legal_indices(values, legal):
    import math
    if len(values)!=len(legal) or any(not math.isfinite(v) for v in values):
        raise ValueError("finite values and matching mask required")
    indices=[i for i,allowed in enumerate(legal) if allowed]
    if not indices: raise ValueError("at least one legal action required")
    return indices

def demo(module):
    return {label:module.update(2,1,[4,8,99],[True,True,False],0.25,0.5,terminal,truncated)
            for label,terminal,truncated in [('ongoing',False,False),('terminal',True,False),('truncated',False,True)]}

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

