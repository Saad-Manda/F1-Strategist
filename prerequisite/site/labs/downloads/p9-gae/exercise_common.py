import math
import numpy as np
def demo(m):
    a,target=m.gae([1,2],[.5,1],[1,3],np.array([False,True]),np.array([True,False]))
    return dict(advantages=a.tolist(),targets=target.tolist())
def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

