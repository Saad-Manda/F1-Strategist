"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def push(buffer, item, capacity):
    if type(capacity) is not int or capacity<1:raise ValueError("positive integer capacity required")
    buffer.append(item)
    del buffer[:-capacity]
def sample(buffer, batch_size, rng):
    if not buffer or type(batch_size) is not int or batch_size<1:raise ValueError("nonempty buffer and positive batch size required")
    return [rng.choice(buffer) for _ in range(batch_size)]
def make_target(online):
    target=copy.deepcopy(online).eval()
    for p in target.parameters():p.requires_grad_(False)
    return target
def sync_target(target, online, step, interval):
    if type(step) is not int or step<1 or type(interval) is not int or interval<1:raise ValueError("positive integer step/interval required")
    if step%interval==0:target.load_state_dict(online.state_dict())
def targets(target, next_states, rewards, terminated, gamma):
    if not math.isfinite(gamma) or not 0<=gamma<=1:raise ValueError("gamma in [0,1] required")
    if rewards.ndim!=1 or terminated.shape!=rewards.shape or next_states.shape[0]!=len(rewards) or terminated.dtype!=torch.bool:
        raise ValueError("invalid batch shapes or flags")
    if not all(finite(t) for t in (next_states,rewards)):raise ValueError("finite batch required")
    with torch.no_grad():
        values=target(next_states).max(dim=1).values
        return rewards+gamma*torch.where(terminated,torch.zeros_like(values),values)

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
