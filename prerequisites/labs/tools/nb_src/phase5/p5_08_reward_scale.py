# %% [markdown]
# # Lab p5-08 · Speed limits
#
# **Goes with:** Phase 5, page 08 — The reward-scale trap · **Time:** about 20 minutes
#
# Page 08 names three safeguards in the real training step, Huber loss, gradient clipping and
# Adam, and says each one is also a speed limit. Here you write the first two, then measure
# what all three together cost a fresh network that has to reach −4,940 instead of −250.
# Last, you practise the check page 08 says to make before reading anything into a flat
# reward curve.
#
# Stuck? Run `python -m labs hint p5-08` in a terminal.

# %%
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
LAB = "p5-08"

# %% [markdown]
# ## Part A — two of the limits, as code
#
# **TODO 1.** `huber_slope`: the slope of the Huber loss with respect to the prediction, for an
# error `e = prediction − target`. Page 08's table: it equals `e` while `|e| ≤ 1` and is
# capped at ±1 beyond. (`np.clip` does it.)
#
# **TODO 2.** `clip_by_norm`: given a list of gradient arrays, compute their overall norm (the
# square root of the sum of every squared entry, across all arrays). If it is above
# `max_norm`, scale every array by `max_norm / norm`. Return `(clipped list, norm)`.

# %%
def squared_slope(e):
    """Given: the slope of (prediction - target)², which is 2e."""
    return 2.0 * np.asarray(e, dtype=float)


def huber_slope(e):
    """The slope of the Huber loss: e for |e| <= 1, otherwise +1 or -1."""
    # >>> SOLUTION: np.clip(e, -1, 1)
    return np.clip(np.asarray(e, dtype=float), -1.0, 1.0)
    # <<< SOLUTION


def clip_by_norm(grads, max_norm):
    """Scale every gradient array by the same factor so that the overall norm is at most max_norm."""
    # >>> SOLUTION: norm = sqrt of the sum of squares over all arrays; scale = min(1, max_norm / norm)
    norm = float(np.sqrt(sum(float(np.sum(np.asarray(g, dtype=float) ** 2)) for g in grads)))
    scale = min(1.0, max_norm / norm) if norm > 0 else 1.0
    return [np.asarray(g, dtype=float) * scale for g in grads], norm
    # <<< SOLUTION


for e in (0.5, 250, 5000):
    print(f"error {e:>6}: squared-error slope {squared_slope(e):>7.0f}   Huber slope {huber_slope(e):.1f}")
checks.limits(huber_slope, clip_by_norm)

# %% [markdown]
# ## Part B — the distance, measured
#
# A fresh network, the shape page 08 describes at toy size (two inputs, two hidden layers of
# 64), trained with the real agent's three safeguards: Huber loss, gradient norm clipped to
# 10, Adam at a learning rate of 0.001. Its one job is to output a single constant
# everywhere. This is the easiest case there is: the target never moves, and there is no
# bootstrapping and no strategy to learn. The only question is how long the distance takes.
#
# - centred: the target is **−250**
# - uncentred: the target is **−4,940**
#
# "Arrived" means every one of 256 test inputs is within **1 second** of the target, the
# accuracy page 08 says a strategy needs.
#
# **TODO — predict before you run.** The uncentred target is about 20 times further away. How
# many times as many updates will it take to arrive?

# %%
CHOICES = {
    "same": "about the same: Adam adapts its step size, so distance does not matter",
    "few": "a few times as many",
    "twenty": "about twenty times as many, in proportion to the distance",
}
my_prediction = "few"  # >>> ANSWER

predict.commit(LAB, "distance", my_prediction, CHOICES)

# %%
TEST_INPUTS = torch.as_tensor(np.random.default_rng(99).uniform(0, 1, (256, 2)).astype(np.float32))


def fit_constant(target, updates=2500, seed=0):
    """Train a fresh network toward `target` everywhere. Returns the worst error over the test inputs after each update."""
    torch.manual_seed(seed)
    net = nn.Sequential(nn.Linear(2, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 1))
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    rng = np.random.default_rng(seed)
    worst = []
    for _ in range(updates):
        x = torch.as_tensor(rng.uniform(0, 1, (32, 2)).astype(np.float32))
        prediction = net(x).squeeze(1)
        loss = F.smooth_l1_loss(prediction, torch.full_like(prediction, target))
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(net.parameters(), 10.0)
        opt.step()
        with torch.no_grad():
            worst.append(float((net(TEST_INPUTS).squeeze(1) - target).abs().max()))
    return np.array(worst)


def first_arrival(worst, tol=1.0):
    hits = np.flatnonzero(worst < tol)
    return int(hits[0]) + 1 if len(hits) else None


runs = {target: fit_constant(target) for target in (-250.0, -4940.0)}
arrive = {target: first_arrival(w) for target, w in runs.items()}
plt.figure(figsize=(8, 3.5))
for target, worst in runs.items():
    plt.plot(worst, label=f"target {target:,.0f}")
plt.axhline(1.0, color="gray", linestyle="--", label="1 second")
plt.yscale("log")
plt.xlabel("updates")
plt.ylabel("worst error (log scale)")
plt.legend()
plt.show()
for target, worst in runs.items():
    print(f"target {target:>7,.0f}: within 1 s everywhere after {arrive[target]} updates; worst error over the last 300 updates {worst[-300:].max():.2f}")
ratio = arrive[-4940.0] / arrive[-250.0]
predict.reveal(LAB, "distance", f"the uncentred target took {ratio:.1f} times as many updates", correct="few")
checks.distance(runs, arrive)

# %% [markdown]
# Twenty times the distance cost a few times the updates, not twenty. Adam moves every one of
# the network's few thousand weights at once, and their effects on the output add up, so the
# output can travel much further per update than any single weight does. The limits are real,
# and they are not a strict "so many seconds per update".
#
# Now look at the right-hand end of the two curves. Centred, the network arrives and stays
# within a second of the target. Uncentred, it arrives and then keeps wobbling, by several
# seconds at a time over the last 300 updates. Every Adam step moves each weight by about the
# learning rate, and with weights large enough to produce −4,940, steps of that size move the
# output further. That wobble is the size of the strategy differences the network is meant to
# resolve.
#
# This was the easy case. In real training the target is built from the network's own slowly
# moving copy (page 08's "fourth limit") and is not handed over. A quick experiment for this
# lab, training a 52-lap chain by bootstrapping, did not converge at either scale with these
# settings, which is page 06's deadly triad showing up and a reason to watch the next part's
# numbers in any real run.
#
# ## Part C — read the run, not the reward curve
#
# Page 08's table says what to compare when the reward curve is flat: the average Q-value the
# network outputs, against the scale the true values must have. Here are four runs, each
# logged every 500 races. The expected scale is about **−250**, the centred race. Rewards are
# flat in all four.
#
# **TODO 3.** For each run, choose the row of page 08's table it matches.

# %%
EXPECTED = -250.0
RUNS = {
    "run 1": {"reward": [-251, -250, -252, -251, -250], "avg_q": [-0.3, -0.1, -0.4, -0.2, -0.3]},
    "run 2": {"reward": [-251, -251, -250, -251, -251], "avg_q": [-38, -77, -118, -152, -190]},
    "run 3": {"reward": [-250, -252, -251, -250, -251], "avg_q": [-260, -410, -690, -1150, -1890]},
    "run 4": {"reward": [-251, -250, -251, -251, -250], "avg_q": [-236, -247, -251, -249, -250]},
}
ROWS = {
    "travelling": "still travelling: the algorithm works and has a long way to go",
    "broken": "something is broken: no updates are happening, or the targets are wrong",
    "differences": "the scale is learned and the fine differences between actions are not",
    "runaway": "runaway estimates: look at the target computation",
}

fig, axes = plt.subplots(1, 4, figsize=(13, 2.8), sharey=True)
for ax, (name, log) in zip(axes, RUNS.items()):
    ax.plot(log["avg_q"], marker="o")
    ax.axhline(EXPECTED, color="gray", linestyle="--")
    ax.set_title(name)
    ax.set_xlabel("check (every 500 races)")
axes[0].set_ylabel("average Q-value")
plt.show()

run_1 = "broken"  # >>> ANSWER
run_2 = "travelling"  # >>> ANSWER
run_3 = "runaway"  # >>> ANSWER
run_4 = "differences"  # >>> ANSWER

checks.diagnosis({"run 1": run_1, "run 2": run_2, "run 3": run_3, "run 4": run_4}, ROWS)

# %% [markdown]
# Four flat reward curves, four different situations, and the reward curve could not tell any
# of them apart. One number did: the average Q-value against the scale it has to reach. Page
# 11 notes that the real training loop does not log it. It is the first thing to add.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
