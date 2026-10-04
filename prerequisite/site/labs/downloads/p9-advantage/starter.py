from exercise_common import *

def advantages(returns, values):
    raise NotImplementedError("Complete advantages")

def actor_loss(log_probs, advantage):
    raise NotImplementedError("Complete actor_loss")

def critic_loss(values, targets):
    raise NotImplementedError("Complete critic_loss")

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
