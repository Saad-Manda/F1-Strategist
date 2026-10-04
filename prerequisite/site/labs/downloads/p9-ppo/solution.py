from exercise_common import *

def frozen(log_probs):
    vectors(log_probs)
    return log_probs.detach().clone()
def ratio_data(new_log_probs, old_log_probs, advantage, epsilon):
    vectors(new_log_probs,old_log_probs,advantage);clip_value(epsilon)
    lr=new_log_probs-old_log_probs.detach();ratio=lr.exp()
    if not torch.isfinite(ratio).all():raise ValueError("ratio overflow")
    return ratio,lr,advantage.detach()
def ppo_loss(new_log_probs, old_log_probs, advantage, epsilon=.2):
    r,lr,a=ratio_data(new_log_probs,old_log_probs,advantage,epsilon)
    return -torch.minimum(r*a,r.clamp(1-epsilon,1+epsilon)*a).mean()
def diagnostics(new_log_probs, old_log_probs, advantage, epsilon=.2):
    r,lr,a=ratio_data(new_log_probs,old_log_probs,advantage,epsilon)
    return dict(ratios=r.detach(),clip_fraction=float(((r-1).abs()>epsilon).double().mean()),approx_kl=float((r-1-lr).detach().mean()))

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
