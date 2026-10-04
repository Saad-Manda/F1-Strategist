from exercise_common import *

def frozen(log_probs):
    raise NotImplementedError("Complete frozen")

def ppo_loss(new_log_probs, old_log_probs, advantage, epsilon=.2):
    raise NotImplementedError("Complete ppo_loss")

def diagnostics(new_log_probs, old_log_probs, advantage, epsilon=.2):
    raise NotImplementedError("Complete diagnostics")

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
