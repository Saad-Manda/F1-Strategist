"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def double_targets(online_values, target_values, rewards, terminated, legal, gamma):
    if not math.isfinite(gamma) or not 0<=gamma<=1:raise ValueError("gamma in [0,1] required")
    if online_values.ndim!=2 or target_values.shape!=online_values.shape or legal.shape!=online_values.shape or rewards.shape!=(online_values.shape[0],) or terminated.shape!=rewards.shape or legal.dtype!=torch.bool or terminated.dtype!=torch.bool:raise ValueError("invalid batch shapes or flags")
    if not all(finite(t) for t in (online_values,target_values,rewards)):raise ValueError("finite values required")
    active=~terminated
    if bool((~legal[active].any(dim=1)).any()):raise ValueError("no legal next action")
    with torch.no_grad():
        result=rewards.clone()
        selected=online_values[active].masked_fill(~legal[active],-torch.inf).argmax(dim=1)
        result[active]+=gamma*target_values[active].gather(1,selected[:,None]).squeeze(1)
        return result
def dueling(value, advantage):
    if advantage.ndim!=2 or advantage.shape[1]==0 or value.shape!=(advantage.shape[0],1) or not all(finite(t) for t in (value,advantage)):raise ValueError("expected V[B,1], A[B,actions], finite")
    return value+advantage-advantage.mean(dim=1,keepdim=True)

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
