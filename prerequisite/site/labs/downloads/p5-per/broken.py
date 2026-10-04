"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def distribution(raw_priorities, alpha, beta):
    masses=np.asarray(raw_priorities,dtype=float)**alpha
    return masses/masses.sum(),np.ones(len(masses))
def new_priority(raw_priorities):return float(np.sqrt(max(raw_priorities))) if len(raw_priorities) else 1.
def update_priority(td_error, epsilon=1e-6):return td_error
def weighted_loss(losses, weights):return float(np.sum(np.asarray(losses)*weights)/np.sum(weights))

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
