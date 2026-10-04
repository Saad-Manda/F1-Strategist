import math
def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

MATRIX=((0,-1,1),(1,0,-1),(-1,1,0))
def action(a):
    if type(a) is not int or a not in (0,1,2):raise ValueError("action must be integer 0,1,2")
def policy(p):
    if len(p)!=3:raise ValueError("three probabilities required")
    validate_distribution(p)
validate_action=action
validate_policy=policy
def demo(m):return dict(paper_rock=m.payoff(1,0),paper_scissors=m.payoff(1,2),mixed=m.expected_payoff([0,1,0],[.5,.25,.25]),uniform=[m.expected_payoff([1/3]*3,[int(j==i) for j in range(3)]) for i in range(3)])

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

