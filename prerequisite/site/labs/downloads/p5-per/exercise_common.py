import math
import numpy as np
def demo(m):
    p,w=m.distribution([1,4,9],.5,1)
    return dict(probabilities=p.tolist(),weights=w.tolist(),new_raw=m.new_priority([1,4,9]),weighted_loss=m.weighted_loss([1,4,9],w))

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

