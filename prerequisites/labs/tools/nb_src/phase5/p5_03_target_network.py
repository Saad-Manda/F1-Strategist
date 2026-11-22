# %% [markdown]
# # Lab p5-03 · Chasing your own target
#
# **Goes with:** Phase 5, page 03 — The target network · **Time:** about 20 minutes
#
# Page 03 says that when one network both makes the prediction and computes the target it is
# trained toward, every step that fixes the prediction also moves the target. Here you build
# the two ways of keeping a second, slower copy, watch a single update move a target, and
# then train the same network three ways on a problem where the difference is not subtle.
#
# **Environment:** a chain of 20 states, 0 to 19, walked left to right. Every step costs −1
# and stepping off state 19 ends the episode, so the true value of state `s` is `−(20 − s)`:
# −20 at the start, −1 at the end. No discount (γ = 1), like the real project. There are no
# actions to choose; the network only has to learn the 20 values, from transitions
# `(s, reward −1, s + 1)`.
#
# Stuck? Run `python -m labs hint p5-03` in a terminal.

# %%
import copy
import math
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import checks
from labs.labkit import predict

torch.set_num_threads(1)
LAB = "p5-03"
N = 20
STATES = np.arange(N)
TRUE_VALUES = -(N - STATES).astype(np.float32)


def encode(states):
    """States 0..20 as a column of inputs centred on 0. State 20 is 'after the end'; it is only ever a next state."""
    s = np.asarray(states, dtype=np.float32).reshape(-1, 1)
    return torch.as_tensor((s - (N - 1) / 2) / (N / 2))


def make_net(seed):
    torch.manual_seed(seed)
    return nn.Sequential(nn.Linear(1, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))


def values_of(net):
    with torch.no_grad():
        return net(encode(STATES)).squeeze(1).numpy()

# %% [markdown]
# ## Part A — the two updates
#
# **TODO 1.** `soft_update`: page 03's Polyak update, applied to every weight,
# `θ⁻ ← τ·θ + (1 − τ)·θ⁻`. Loop over `zip(target.parameters(), online.parameters())` and change
# each target tensor in place inside `torch.no_grad()`. (`t.mul_(1 - tau).add_(tau * o)` does
# it in one line.)
#
# **TODO 2.** `hard_update`: copy every online weight into the target. One line:
# `target.load_state_dict(online.state_dict())`. The target must stay a separate network: it
# receives the online network's numbers, not the network itself.

# %%
def soft_update(target, online, tau):
    """Move every target weight a fraction tau of the way toward the online weight."""
    # >>> SOLUTION: inside torch.no_grad(), for each (t, o) pair of parameters: t.mul_(1 - tau).add_(tau * o)
    with torch.no_grad():
        for t, o in zip(target.parameters(), online.parameters()):
            t.mul_(1.0 - tau).add_(tau * o)
    # <<< SOLUTION


def hard_update(target, online):
    """Copy the online weights into the target network."""
    # >>> SOLUTION: target.load_state_dict(online.state_dict())
    target.load_state_dict(online.state_dict())
    # <<< SOLUTION


checks.updates(soft_update, hard_update, make_net)

# %% [markdown]
# Page 03 worked out that at τ = 0.005 the target closes half a gap in about 139 updates.
# Measure it: hold the online network still, start the target somewhere else, and count.

# %%
def total_gap(target, online):
    with torch.no_grad():
        return sum(float((o - t).abs().sum()) for o, t in zip(online.parameters(), target.parameters()))


def updates_to_halve(tau):
    online, target = make_net(0), make_net(1)
    first, n = total_gap(target, online), 0
    while total_gap(target, online) > 0.5 * first:
        soft_update(target, online, tau)
        n += 1
    return n


for tau in (0.005, 0.05):
    print(f"tau = {tau}: half the gap closed after {updates_to_halve(tau)} updates; formula ln 0.5 / ln(1 - tau) = {math.log(0.5) / math.log(1 - tau):.1f}")
checks.halving(updates_to_halve)

# %% [markdown]
# ## Part B — one update, one target
#
# Take one transition, state 5 → state 6, and make one gradient step that moves the
# network's value of state 5 toward its target, `−1 + V(6)`. Do it twice: once computing the
# target with the network being trained, once with a frozen copy.
#
# **TODO — predict before you run.** After that one step, which targets have changed?

# %%
CHOICES = {
    "neither": "neither: the step was about state 5, and the target is about state 6",
    "same-net": "only the one computed by the network being trained",
    "both": "both",
}
my_prediction = "same-net"  # >>> ANSWER

predict.commit(LAB, "target-moves", my_prediction, CHOICES)

# %%
def one_step(target_is_online):
    online = make_net(2)
    target = online if target_is_online else copy.deepcopy(online)
    opt = torch.optim.SGD(online.parameters(), lr=0.01)
    with torch.no_grad():
        goal_before = -1.0 + target(encode([6])).item()
    loss = F.smooth_l1_loss(online(encode([5])).squeeze(), torch.tensor(goal_before))
    opt.zero_grad()
    loss.backward()
    opt.step()
    with torch.no_grad():
        goal_after = -1.0 + target(encode([6])).item()
    return goal_before, goal_after


moves = {}
for name, same in (("same network", True), ("frozen copy", False)):
    before, after = one_step(same)
    moves[name] = after - before
    print(f"{name:<13} target before {before:+.4f}, after {after:+.4f}: moved {after - before:+.4f}")
predict.reveal(LAB, "target-moves", "the target moved only when the trained network computed it", correct="same-net")
checks.one_step(moves)

# %% [markdown]
# The step was about state 5 only. It moved the value of state 6 anyway, because the two
# share every weight (lab p5-01, Part A). When state 6's value is also the target, the target
# moved too. With a frozen copy, nothing the step did can reach it.
#
# ## Part C — train it three ways
#
# Train on random batches of 8 transitions from the chain, 600 updates, Huber loss, Adam:
#
# - **same network**: the target is computed by the network being trained (page 03's naive
#   idea)
# - **soft**: a target network, soft-updated with τ = 0.05 after every step
# - **hard**: a target network, copied over every 20 steps
#
# **TODO 3.** Finish `train_chain`: the line that builds the batch's targets. It is page 06's
# terminal cut-off: `−1 + (1 − done) · V⁻(next state)`, computed by `target_net` inside
# `torch.no_grad()`. In "same" mode `target_net` *is* `online`, and nothing else in the loop
# changes.

# %%
def train_chain(mode, seed=0, updates=600, tau=0.05, copy_every=20, batch=8):
    """Returns the worst error over the 20 states, recorded every 10 updates."""
    online = make_net(seed)
    target_net = online if mode == "same" else copy.deepcopy(online)
    opt = torch.optim.Adam(online.parameters(), lr=0.01)
    rng = np.random.default_rng(seed)
    worst = []
    for step in range(updates):
        s = rng.integers(N, size=batch)
        done = torch.as_tensor((s == N - 1).astype(np.float32))
        # >>> SOLUTION: with torch.no_grad(): goal = -1 + (1 - done) * target_net(encode(s + 1)).squeeze(1)
        with torch.no_grad():
            goal = -1.0 + (1.0 - done) * target_net(encode(s + 1)).squeeze(1)
        # <<< SOLUTION
        loss = F.smooth_l1_loss(online(encode(s)).squeeze(1), goal)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if mode == "soft":
            soft_update(target_net, online, tau)
        elif mode == "hard" and (step + 1) % copy_every == 0:
            hard_update(target_net, online)
        if step % 10 == 0 or step == updates - 1:
            worst.append(float(np.max(np.abs(values_of(online) - TRUE_VALUES))))
    return worst


checks.training_step(train_chain)

# %% [markdown]
# **TODO — predict.** Which of the three ends with the largest error?

# %%
CHOICES_C = {
    "same": "the same network",
    "soft": "the soft target network: it is always a little out of date",
    "hard": "the hard target network: it is up to 20 steps out of date",
}
my_prediction_c = "same"  # >>> ANSWER

predict.commit(LAB, "three-ways", my_prediction_c, CHOICES_C)

# %%
curves = {mode: train_chain(mode) for mode in ("same", "soft", "hard")}
labels = {"same": "same network", "soft": "soft, τ = 0.05", "hard": "hard, every 20"}
plt.figure(figsize=(8, 3.5))
for mode, worst in curves.items():
    plt.plot(np.arange(len(worst)) * 10, worst, label=labels[mode])
plt.yscale("log")
plt.xlabel("updates")
plt.ylabel("worst error over the 20 states (log scale)")
plt.legend()
plt.show()
for mode, worst in curves.items():
    print(f"{labels[mode]:<15} worst error: largest {max(worst):9.1f}, final {worst[-1]:7.2f}")

loser = max(curves, key=lambda m: curves[m][-1])
predict.reveal(LAB, "three-ways", f"{labels[loser]} ended with the largest error", correct="same")
checks.three_ways(curves)

# %% [markdown]
# Without a target network the values do not just converge slowly. They run away, to
# thousands, on a chain whose true values never go below −20. Each update pushes a state's
# value toward a target that the same update has also pushed, the next target is further out
# again, and with γ = 1 nothing shrinks the loop. Wherever the curve happens to be after 600
# updates, nothing about it looks like convergence. Both kinds of target network learn the
# chain: the hard one in visible steps, each time it is copied, the soft one smoothly.
#
# Whether the naive version blows up depends on the problem. On the 12-lap world of page 09
# it did not, and the target network showed up only as steadier training. That is the honest
# summary of page 03: a target network removes a feedback loop that sometimes merely adds
# noise and sometimes runs away, and you cannot tell in advance which you will get. Page 06
# names the larger pattern this is part of, the deadly triad.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
