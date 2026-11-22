# %% [markdown]
# # Lab p5-01 · One update, many states
#
# **Goes with:** Phase 5, page 01 — From a table cell to a function · **Time:** about 15 minutes
#
# The page says a table update changes one cell, and a network update changes every
# prediction the network makes, because every prediction comes from the same weights. Here
# you make one update of each kind and look at what moved. Then you find out what that
# sharing buys and what it costs.
#
# **Environment:** the 1000-state random walk from lab p4-05 (Sutton & Barto, Example 9.1).
# States 1 to 1000, start at 500, jumps of 1 to 100 left or right, −1 for falling off the left
# end and +1 off the right end. True values run from about −0.92 to +0.92.
#
# The network is page 02's kind, at toy size: one input (the state, rescaled to run from −1
# to +1), two hidden layers of 32 ReLU units, one output.
#
# Stuck? Run `python -m labs hint p5-01` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn

import checks
from labs.labkit import envs, predict
from labs.labkit.envs import WALK_START, WALK_STATES

torch.set_num_threads(1)  # tiny networks run faster on one thread
LAB = "p5-01"
STATES = np.arange(1, WALK_STATES + 1)
TRUE_VALUES = envs.walk_true_values()  # index 0 is state 1


def make_net(seed):
    """A fresh network. The same seed always gives the same starting weights."""
    torch.manual_seed(seed)
    return nn.Sequential(nn.Linear(1, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))


def features(states):
    """States 1..1000 as a column of inputs from -1 to +1. Networks train best on inputs centred on 0."""
    return torch.as_tensor((np.asarray(states, dtype=np.float32).reshape(-1, 1) - 500.5) / 500.0)


def values_of(net, states=STATES):
    """The network's current value for each state, as a NumPy array. No learning happens here."""
    with torch.no_grad():
        return net(features(states)).squeeze(1).numpy()

# %% [markdown]
# ## Part A — one update of each kind
#
# The table update is Phase 4's, and it is given.
#
# **TODO 1.** Implement `net_update`: one gradient-descent step that moves the network's
# outputs at `states` toward `targets`. Four lines, page 02's four steps:
#
# 1. forward: `predictions = net(features(states)).squeeze(1)`
# 2. loss: the mean of `(predictions − targets)²`, with `targets` turned into a tensor
# 3. backward: `optimizer.zero_grad()`, then `loss.backward()`
# 4. update: `optimizer.step()`
#
# Return the loss as a plain float (`loss.item()`).

# %%
def table_update(table, state, target, alpha):
    """Phase 4's update: one cell moves a fraction alpha of the way toward the target."""
    table[state - 1] += alpha * (target - table[state - 1])


def net_update(net, optimizer, states, targets):
    """One gradient step on the mean squared error between net(states) and targets. Returns the loss."""
    # >>> SOLUTION: forward pass, mean squared error against torch.as_tensor(targets), zero_grad, backward, step, return loss.item()
    predictions = net(features(states)).squeeze(1)
    loss = ((predictions - torch.as_tensor(np.asarray(targets, dtype=np.float32))) ** 2).mean()
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    return loss.item()
    # <<< SOLUTION


checks.update(net_update, make_net, values_of)

# %% [markdown]
# Now one update at state 500, toward a target of 1.0, applied to a table that starts at zero
# and to a fresh network.
#
# **TODO — predict before you run.** After the network's single update at state 500, how
# much has its value for **state 1** moved, compared with the move at state 500?

# %%
CHOICES = {
    "none": "not at all: state 1 was not part of the update",
    "little": "a little: under a fifth of the move at state 500",
    "most": "most of it: more than half of the move at state 500",
}
my_prediction = "most"  # >>> ANSWER

predict.commit(LAB, "spread", my_prediction, CHOICES)

# %%
table = np.zeros(WALK_STATES)
table_update(table, 500, 1.0, alpha=0.1)

net = make_net(0)
before = values_of(net)
net_update(net, torch.optim.SGD(net.parameters(), lr=0.05), [500], [1.0])
moved = values_of(net) - before

fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(STATES, table, label="table: change in each cell")
ax.plot(STATES, moved, label="network: change in each prediction")
ax.axvline(500, color="gray", linestyle="--")
ax.set_xlabel("state")
ax.set_ylabel("change")
ax.legend()
plt.show()

ratio = moved[0] / moved[499]
print(f"table:   state 500 moved {table[499]:.3f}, state 1 moved {table[0]:.3f}")
print(f"network: state 500 moved {moved[499]:.3f}, state 1 moved {moved[0]:.3f} ({ratio:.0%} of the move at 500)")
predict.reveal(LAB, "spread", f"state 1 moved {ratio:.0%} as much as state 500", correct="most")
checks.spread(table, moved)

# %% [markdown]
# A fresh network has not yet learned that state 1 and state 500 are different, so one
# update moves the whole line, the far ends by about as much as state 500 itself. That is generalization in its crudest form. Training is what
# shapes how far each update reaches: after a while, an update at state 500 moves its
# neighbours a lot and the far end much less. It never stops moving them entirely.
#
# ## Part B — what the sharing buys
#
# Learn the walk's values from finished walks. Every state visited in a walk is moved toward
# the walk's final reward (−1 or +1): with γ = 1 and no reward along the way, that is each
# state's return. This is the Monte Carlo update, the simplest kind there is, so the only
# thing that differs between the two learners is the table versus the network.
#
# **TODO 2.** Finish `learn_from_walks`. The walk loop and the table's update are given. Add
# the network's update: one call to `net_update` per walk, with every state the walk visited
# and the walk's final reward as the target for each of them.

# %%
def play_walk(rng):
    """One walk from WALK_START. Returns (the states visited, in order; the final reward)."""
    state, visited = WALK_START, []
    while True:
        visited.append(state)
        state, reward, done = envs.walk_step(state, rng)
        if done:
            return visited, reward


def learn_from_walks(walks, seed):
    """Monte Carlo learning from `walks` walks, by a table and by a network. Returns (table, net)."""
    rng = np.random.default_rng(seed)
    table = np.zeros(WALK_STATES)
    net = make_net(seed)
    optimizer = torch.optim.Adam(net.parameters(), lr=0.003)
    for _ in range(walks):
        visited, final_reward = play_walk(rng)
        for state in visited:
            table_update(table, state, final_reward, alpha=0.1)
        # >>> SOLUTION: one net_update call: every visited state, each with final_reward as its target
        net_update(net, optimizer, visited, [final_reward] * len(visited))
        # <<< SOLUTION
    return table, net


def rms_error(estimate):
    return float(np.sqrt(np.mean((np.asarray(estimate) - TRUE_VALUES) ** 2)))


checks.learning(learn_from_walks, values_of, rms_error)

# %% [markdown]
# **TODO — predict.** With only **50 walks**, which has the smaller error over all 1000
# states?

# %%
CHOICES_B = {
    "table": "the table: it makes no assumptions about states it has not seen",
    "network": "the network",
    "same": "about the same",
}
my_prediction_b = "network"  # >>> ANSWER

predict.commit(LAB, "few-walks", my_prediction_b, CHOICES_B)

# %%
results = {}
for walks in (20, 50, 200):
    errors = []
    for seed in (0, 1, 2):
        table, net = learn_from_walks(walks, seed)
        errors.append((rms_error(table), rms_error(values_of(net))))
    results[walks] = np.mean(errors, axis=0)
    print(f"{walks:>4} walks   table RMS error {results[walks][0]:.3f}   network {results[walks][1]:.3f}")

table, net = learn_from_walks(50, 0)
plt.figure(figsize=(8, 3))
plt.plot(STATES, TRUE_VALUES, color="gray", label="true value")
plt.plot(STATES, table, label="table, 50 walks")
plt.plot(STATES, values_of(net), label="network, 50 walks")
plt.xlabel("state")
plt.legend()
plt.show()
print(f"states never visited in those 50 walks: {np.mean(table == 0):.0%}")

winner = "network" if results[50][1] < results[50][0] else "table"
predict.reveal(LAB, "few-walks", f"after 50 walks the {winner} had the smaller error", correct="network")
checks.comparison(results)

# %% [markdown]
# The table's picture is a comb: states that were visited moved, states that were not are
# still at zero. A table has no opinion about a state until it has seen it. The network has an
# opinion everywhere, because every walk moved the whole line, and a smooth line is a good
# guess for this problem. That is page 01's case for a network, measured.
#
# With more walks the table catches up, because eventually it sees everything. In the real
# project it never would: page 01's 172,800 states, and Phase 6's dimensions on top, are far
# more than a training run can visit.
#
# ## Part C — what the sharing costs
#
# Take a network trained on 200 walks. Now show it only one region of the walk, states 1 to
# 100, with their **true** values as targets, 100 times in a row. Every target is correct.
# Measure how far the predictions for the far half of the walk, states 501 to 1000, move.

# %%
_, net = learn_from_walks(200, 0)
optimizer = torch.optim.Adam(net.parameters(), lr=0.003)
before = values_of(net)
region = np.arange(1, 101)
for _ in range(100):
    net_update(net, optimizer, region, TRUE_VALUES[region - 1])
after = values_of(net)

far_move = float(np.mean(np.abs(after[500:] - before[500:])))
near_before = float(np.sqrt(np.mean((before[:100] - TRUE_VALUES[:100]) ** 2)))
near_after = float(np.sqrt(np.mean((after[:100] - TRUE_VALUES[:100]) ** 2)))
print(f"states 1-100:    error now {near_after:.3f} (was {near_before:.3f})")
print(f"states 501-1000: moved by {far_move:.3f} on average and up to {np.max(np.abs(after[500:] - before[500:])):.3f}, though none of them was in the data")
print("A table given the same 100 updates would have moved states 501-1000 by exactly 0.")

plt.figure(figsize=(8, 3))
plt.plot(STATES, TRUE_VALUES, color="gray", label="true value")
plt.plot(STATES, before, label="before")
plt.plot(STATES, after, label="after 100 updates on states 1-100")
plt.axvspan(1, 100, alpha=0.15)
plt.xlabel("state")
plt.legend()
plt.show()
checks.interference(far_move)

# %% [markdown]
# A hundred correct updates about one end of the walk moved what the network believed about the
# other end, where nothing had been said. Whether that move helped or hurt there was luck.
# This is page 01's "catch, named up front", and it is why the order of training data matters
# for a network in a way it never did for a table. A race's laps arrive in order: lap 1, lap 2,
# lap 3, each one like the last. Page 04 is about not training on them in that order.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
