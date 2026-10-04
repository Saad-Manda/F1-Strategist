import math
def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

def team_actions(actions):
    if set(actions)!= {'A','B'} or any(type(a) is not int or a not in (0,1) for a in actions.values()):raise ValueError("exactly A/B integer actions 0 or 1 required")
def demo(m):return dict(joint=m.joint_step({'A':1,'B':1}),differences=m.contributions({'A':1,'B':1}))

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

