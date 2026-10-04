"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def distribution(raw_priorities, alpha, beta):
    p=np.asarray(raw_priorities,dtype=float)
    if p.ndim!=1 or not len(p) or not np.isfinite(p).all() or (p<=0).any() or not math.isfinite(alpha) or not 0<=alpha<=1 or not math.isfinite(beta) or not 0<=beta<=1:raise ValueError("positive finite priorities, alpha/beta in [0,1] required")
    masses=p**alpha;probabilities=masses/masses.sum()
    weights=(len(p)*probabilities)**(-beta)
    return probabilities,weights/weights.max()
def new_priority(raw_priorities):
    p=np.asarray(raw_priorities,dtype=float)
    if p.ndim!=1 or not np.isfinite(p).all() or (p<=0).any():raise ValueError("invalid raw priorities")
    return float(p.max()) if len(p) else 1.
def update_priority(td_error, epsilon=1e-6):
    if not math.isfinite(td_error) or not math.isfinite(epsilon) or epsilon<=0:raise ValueError("finite error and positive epsilon required")
    return abs(td_error)+epsilon
def weighted_loss(losses, weights):
    losses=np.asarray(losses,dtype=float);weights=np.asarray(weights,dtype=float)
    if losses.ndim!=1 or not len(losses) or weights.shape!=losses.shape or not np.isfinite(losses).all() or not np.isfinite(weights).all() or (losses<0).any() or (weights<0).any() or (weights>1).any():raise ValueError("invalid losses/weights")
    return float(np.mean(weights*losses))

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
