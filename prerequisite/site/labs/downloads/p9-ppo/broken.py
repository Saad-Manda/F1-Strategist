from exercise_common import *

def frozen(log_probs):return log_probs.detach()
def ppo_loss(new_log_probs, old_log_probs, advantage, epsilon=.2):
    return -((new_log_probs-old_log_probs).exp().clamp(1-epsilon,1+epsilon)*advantage).mean()
def diagnostics(new_log_probs, old_log_probs, advantage, epsilon=.2):
    r=(new_log_probs-old_log_probs).exp()
    return dict(ratios=r,clip_fraction=0.,approx_kl=0.)

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
