from exercise_common import *

def probabilities(logits, legal=None):
    raise NotImplementedError("Complete probabilities")

def reinforce_loss(logits, actions, returns, legal=None):
    raise NotImplementedError("Complete reinforce_loss")

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
