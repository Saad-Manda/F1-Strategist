def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

def demo(module):
    import random
    rng=random.Random(7)
    return {"expectations": {str(p): module.expected_value([(p,10),(1-p,-2)]) for p in (0.25,0.5,1/3)},
            "seeded_risky_rewards_p_025": [10 if rng.random()<0.25 else -2 for _ in range(10)]}

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

