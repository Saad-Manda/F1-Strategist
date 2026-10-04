from exercise_common import *

def probabilities(logits, legal=None):
    if logits.ndim!=2 or not logits.numel() or not torch.isfinite(logits).all():raise ValueError("finite logits[B,A] required")
    if legal is not None:
        if legal.shape!=logits.shape or legal.dtype!=torch.bool or not legal.any(1).all():raise ValueError("valid boolean legal mask required")
        logits=logits.masked_fill(~legal,-torch.inf)
    return torch.softmax(logits,dim=1)
def reinforce_loss(logits, actions, returns, legal=None):
    probabilities(logits,legal)
    if actions.shape!=(len(logits),) or actions.dtype!=torch.long or returns.shape!=actions.shape or not torch.isfinite(returns).all():raise ValueError("invalid samples")
    if ((actions<0)|(actions>=logits.shape[1])).any():raise ValueError("invalid action")
    if legal is not None and not legal[torch.arange(len(logits)),actions].all():raise ValueError("illegal action")
    masked=logits if legal is None else logits.masked_fill(~legal,-torch.inf)
    logs=torch.log_softmax(masked,dim=1)[torch.arange(len(logits)),actions]
    return -(logs*returns.detach()).mean()

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
