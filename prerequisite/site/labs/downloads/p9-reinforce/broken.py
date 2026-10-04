from exercise_common import *

def probabilities(logits, legal=None):return torch.softmax(logits,dim=1)
def reinforce_loss(logits, actions, returns, legal=None):
    return (torch.log_softmax(logits,dim=1)[torch.arange(len(logits)),actions]*returns).mean()

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
