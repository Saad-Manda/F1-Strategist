import math
def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

import random
def lane_settings(p,blocking):
    if not math.isfinite(p) or not 0<=p<=1 or type(blocking) is not bool:raise ValueError("p in [0,1] and boolean blocking required")
def demo(m):return dict(low=m.expected_lane(.2),high=m.expected_lane(.8),disconnected=m.expected_lane(.8,False),samples=m.sample_lane(.2,True,1000,7))

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

