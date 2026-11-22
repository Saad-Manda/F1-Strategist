# %% [markdown]
# # Lab p5-02 · The four steps, written out
#
# **Goes with:** Phase 5, page 02 — Neural networks in four steps · **Time:** about 20 minutes
#
# Page 02 ran a forward pass and one gradient by hand on a 2-2-1 network. Here you write both
# in NumPy for a whole batch at once, check every gradient against PyTorch's autograd, and
# then train the network with nothing but your own code. Training shows something the page
# did not need to mention: whether a small network learns can depend on where it starts.
#
# **The network,** exactly the page's shape, no biases:
#
#     h_pre = X · W1ᵀ        X is a batch, one row per example, 2 columns
#     h     = ReLU(h_pre)    W1 has one row per hidden unit and 2 columns
#     y     = h · W2         W2 has one number per hidden unit
#     loss  = mean over the batch of (y − target)²
#
# Stuck? Run `python -m labs hint p5-02` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import numpy as np

import checks
from labs.labkit import predict

LAB = "p5-02"

# page 02's worked example
PAGE_W1 = np.array([[1.0, -1.0], [0.5, 0.5]])
PAGE_W2 = np.array([2.0, -1.0])
PAGE_X = np.array([[2.0, 1.0]])  # a batch of one

# %% [markdown]
# ## Part A — forward
#
# **TODO 1.** Implement `forward`. It returns all three intermediate results, because the
# backward pass needs them. The page's example must give `y = 0.5`.

# %%
def forward(W1, W2, X):
    """Returns (h_pre, h, y): shapes (batch, units), (batch, units), (batch,)."""
    # >>> SOLUTION: h_pre = X @ W1.T; h = np.maximum(0, h_pre); y = h @ W2
    h_pre = X @ W1.T
    h = np.maximum(0.0, h_pre)
    y = h @ W2
    return h_pre, h, y
    # <<< SOLUTION


checks.forward(forward, PAGE_W1, PAGE_W2, PAGE_X)

# %% [markdown]
# ## Part B — backward
#
# **TODO 2.** Implement `backward`: the loss and its gradient with respect to every weight.
# Apply the chain rule from the loss back to the inputs, one line per step:
#
#     dy     = 2 · (y − target) / batch size       ∂loss/∂y, one number per example
#     dW2    = hᵀ · dy                             page 02's ∂L/∂W2, summed over the batch
#     dh     = outer(dy, W2)                       how each hidden unit's output moved the loss
#     dh_pre = dh where h_pre > 0, else 0          ReLU passes a gradient only where it was active
#     dW1    = dh_preᵀ · X
#
# With the page's example and a target of 0, `dW2[0]` must be the page's 1.0.

# %%
def backward(W1, W2, X, targets):
    """Returns (loss, dW1, dW2), with dW1 and dW2 the same shapes as W1 and W2."""
    h_pre, h, y = forward(W1, W2, X)
    loss = float(np.mean((y - targets) ** 2))
    # >>> SOLUTION: the five lines above, from dy back to dW1
    dy = 2.0 * (y - targets) / len(X)
    dW2 = h.T @ dy
    dh = np.outer(dy, W2)
    dh_pre = dh * (h_pre > 0)
    dW1 = dh_pre.T @ X
    # <<< SOLUTION
    return loss, dW1, dW2


checks.backward(backward, PAGE_W1, PAGE_W2, PAGE_X)

# %% [markdown]
# The check above compared your gradients with PyTorch's on random networks and batches.
# That comparison is what `loss.backward()` does for you in every later lab: the same
# chain rule, applied automatically to every weight.
#
# ## Part C — train it
#
# The task: learn `y = |x₁ − x₂|` from 64 random points. A 2-2-1 network can represent this
# exactly. With `W1 = [[1, −1], [−1, 1]]` and `W2 = [1, 1]` one hidden unit computes
# `ReLU(x₁ − x₂)`, the other `ReLU(x₂ − x₁)`, and their sum is the distance.
#
# **TODO 3.** Finish `train`: 2,000 steps of plain gradient descent,
# `W ← W − lr · dW`, on both weight matrices.

# %%
rng = np.random.default_rng(0)
X_TRAIN = rng.uniform(-1, 1, size=(64, 2))
T_TRAIN = np.abs(X_TRAIN[:, 0] - X_TRAIN[:, 1])


def init(width, seed):
    """Random starting weights for a 2-width-1 network."""
    r = np.random.default_rng(seed)
    return r.normal(0, 1, (width, 2)), r.normal(0, 1, width) / np.sqrt(width)


def train(width, seed, steps=2000, lr=0.1):
    """Gradient descent from init(width, seed). Returns (final loss, W1, W2)."""
    W1, W2 = init(width, seed)
    for _ in range(steps):
        loss, dW1, dW2 = backward(W1, W2, X_TRAIN, T_TRAIN)
        # >>> SOLUTION: move each weight matrix against its gradient, scaled by lr
        W1 = W1 - lr * dW1
        W2 = W2 - lr * dW2
        # <<< SOLUTION
    return backward(W1, W2, X_TRAIN, T_TRAIN)[0], W1, W2


checks.training(train, init, backward, X_TRAIN, T_TRAIN)

# %% [markdown]
# **TODO — predict before you run.** Train the 2-2-1 network from 20 different random
# starts. In how many does the loss end below 0.001, so the network has found `|x₁ − x₂|`?

# %%
CHOICES = {
    "all": "all 20, or nearly: the network can represent the answer, so it finds it",
    "half": "around half",
    "few": "only a few",
}
my_prediction = "half"  # >>> ANSWER

predict.commit(LAB, "starts", my_prediction, CHOICES)

# %%
final = {seed: train(2, seed)[0] for seed in range(20)}
solved = [s for s, loss in final.items() if loss < 1e-3]
print(f"solved: {len(solved)} of 20 starts")
print("final loss of each start:", " ".join(f"{final[s]:.3f}" for s in range(20)))

stuck = next(s for s in range(20) if s not in solved)
loss, W1, W2 = train(2, stuck)
print(f"\nstart {stuck} got stuck at loss {loss:.3f}. Its weights after training:")
print("  W1 =", np.round(W1, 2).tolist(), "  W2 =", np.round(W2, 2).tolist())
print("  the answer would be W1 = [[1, -1], [-1, 1]] (up to scale), one unit per side of the V")

predict.reveal(LAB, "starts", f"{len(solved)} of 20 starts solved it", correct="half")
checks.starts(final)

# %% [markdown]
# Look at the stuck start's `W1`. Both rows point the same way, both close to `[1, −1]` up to
# scale, or one row has shrunk to almost nothing. Both units are drawing the same half of
# the V, so the network fits `x₁ > x₂` and gets the other half wrong.
#
# Why does gradient descent not fix it? To draw the other half, one unit has to swing from
# `[1, −1]` round to `[−1, 1]`. Every position along that swing fits the data worse than
# where it is now, and gradient descent only ever moves downhill. It has found a **local
# minimum**: no small step improves the loss, though a large rearrangement would.
#
# There is a second trap your backward pass makes visible. Where `h_pre ≤ 0`, ReLU passes back
# a gradient of 0 (the `dh_pre` line). A unit that is inactive on every input gets no gradient
# at all, so nothing ever moves it again. That is a **dead unit**. It did not happen in these
# 20 starts, and it is common in larger networks trained with large steps.
#
# ## Part D — the same task, a wider network
#
# Page 02 says the real network's width of 128 "just needs to be large enough". Here is a
# second reason to be generous.

# %%
by_width = {}
for width in (2, 4, 8):
    by_width[width] = sum(train(width, seed)[0] < 1e-3 for seed in range(20))
    print(f"width {width}: {by_width[width]} of 20 starts solved it")
checks.widths(by_width)

# %% [markdown]
# Width 4 can represent nothing that width 2 could not: the answer needs two units. The
# spare units make the search reliable. With four units, a start where two of them point the
# same way still has others free to cover the other half of the V. The real network has 128 units per hidden layer
# for a problem that a few dozen could represent, and that margin is part of why it trains.
#
# Everything here was plain gradient descent, `W ← W − lr · dW`. Page 02's table puts it next
# to Phase 4's `Q ← Q + α · δ`: one is the other with a table cell replaced by a gradient.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
