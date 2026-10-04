from exercise_common import *

def advantages(returns, values):return returns-values
def actor_loss(log_probs, advantage):return -(log_probs*advantage).mean()
def critic_loss(values, targets):return ((values-targets)**2).mean()

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
