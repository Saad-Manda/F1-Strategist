from exercise_common import *

def advantages(returns, values):
    vectors(returns,values)
    return (returns-values).detach()
def actor_loss(log_probs, advantage):
    vectors(log_probs,advantage)
    return -(log_probs*advantage.detach()).mean()
def critic_loss(values, targets):
    vectors(values,targets)
    return ((values-targets.detach())**2).mean()

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
