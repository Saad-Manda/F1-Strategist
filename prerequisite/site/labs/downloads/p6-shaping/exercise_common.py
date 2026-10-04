import math
def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

def routes(failure_potential):
    return [('DIRECT',[3],[2,0],[3]),('VIA+FINISH',[0,4],[2,1,0],[0,4]),('VIA+WAIT',[0,0],[2,1,failure_potential],[0,5])]
def demo(m):return {'gamma_1':m.route_returns(),'gamma_half':m.route_returns(.5),'nonzero_failure':m.route_returns(1,10)}

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

