# %% [markdown]
# # Lab p8-05 · The first opponent
#
# **Goes with:** Phase 8, page 05 — Why the pool's first member matters · **Time:** about 15 minutes
#
# The real plan seeds its pool with an untrained network and plays it with ε = 0. Page 05 says
# that is not a random opponent but a fixed one. Here you measure how fixed, on the plan's own
# architecture, and put a number on "how varied is a policy": the entropy of the actions it picks.
#
# **Networks:** `labs/labkit/netinit.py`, the Phase 5 plan's `DuelingDQN` (19 inputs, 6 actions,
# 128 hidden units), freshly initialised and never trained.
#
# Stuck? Run `python -m labs hint p8-05` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np
import torch

import checks
from labs.labkit import netinit, predict

LAB = "p8-05"
torch.set_num_threads(1)
N_NETS = 30

# %% [markdown]
# ## Part A — one race, thirty untrained opponents
#
# `netinit.race_trajectory(52, seed)` is the observation sequence of one 52-lap race: lap and tyre
# age move from 0 to 1, everything else stays put. Each of 30 untrained networks plays it greedily.
#
# **Predict.** Six actions. In how many of the 30 networks is the greedy action the *same on all
# 52 laps*?

# %%
CHOICES = {
    "few": "a few at most: the observation changes every lap, so the action will too",
    "some": "about a third of them",
    "most": "most of them",
}
my_prediction = "most"  # >>> ANSWER
predict.commit(LAB, "same", my_prediction, CHOICES)

# %% [markdown]
# **TODO 1.** `modal_share(actions)`: the fraction of entries equal to the most common value.

# %%
def modal_share(actions):
    # >>> SOLUTION: the largest count over the total
    counts = np.bincount(np.asarray(actions), minlength=netinit.N_ACTIONS)
    return float(counts.max() / counts.sum())
    # <<< SOLUTION


race_shares, random_shares = [], []
for s in range(N_NETS):
    net = netinit.untrained(s)
    race_shares.append(modal_share(netinit.greedy_actions(net, netinit.race_trajectory(52, s))))
    random_shares.append(modal_share(netinit.greedy_actions(net, netinit.random_observations(2000, 0))))
same_all_race = int(np.sum(np.isclose(race_shares, 1.0)))
print(f"networks with the same action on all 52 laps: {same_all_race} of {N_NETS}")
print(f"over 2,000 random observations, the most common action's share: median {np.median(random_shares):.2f}, lowest {min(random_shares):.2f}")
predict.reveal(LAB, "same", f"{same_all_race} of {N_NETS}", correct="most")
checks.part_a(modal_share, same_all_race, random_shares)

# %% [markdown]
# A freshly initialised network's Q values differ across actions by a fraction of a unit (about
# 0.18 here) and move only a little as the input moves, so one action tends to stay on top almost
# everywhere. "Untrained" says how good the policy is. It says nothing about how varied it is.
# The plan's `step` then replaces an illegal action with the first legal one, so a network stuck on
# "pit for the compound I already have" alternates between two things rather than one. That is
# still a fixed, exploitable script.

# %% [markdown]
# ## Part B — a number for "varied"
#
# **TODO 2.** `action_entropy(actions)`: the entropy, in nats, of the empirical distribution of
# the actions (−Σ p log p over the actions that occur). A uniform choice over 6 actions has log 6 ≈
# 1.79; a policy that always does the same thing has 0.

# %%
def action_entropy(actions):
    # >>> SOLUTION: frequencies, drop zeros, -sum p log p
    p = np.bincount(np.asarray(actions), minlength=netinit.N_ACTIONS) / len(actions)
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())
    # <<< SOLUTION


obs = netinit.random_observations(2000, 1)
rng = np.random.default_rng(0)
policies = {
    "untrained, greedy (the plan's seed)": [action_entropy(netinit.greedy_actions(netinit.untrained(s), obs)) for s in range(N_NETS)],
    "uniformly random (epsilon = 1)": [action_entropy(rng.integers(0, netinit.N_ACTIONS, len(obs))) for _ in range(N_NETS)],
    "a rule: pit for compound 1 once tyre age > 0.6": [action_entropy(np.where(obs[:, 1] > 0.6, 1, 0))] * N_NETS,
}
for name, e in policies.items():
    print(f"{name:48s} entropy: median {np.median(e):.2f}")
plt.boxplot(list(policies.values()), orientation="horizontal", tick_labels=["untrained greedy", "random", "rule"]); plt.xlabel("action entropy, nats"); plt.show()
checks.part_b(action_entropy, policies)

# %% [markdown]
# Page 05's two fixes, measured: ε = 1 gives the most variety and no competence; a rule (Phase
# 3's baselines are rules) gives a little variety and some competence. The untrained greedy network
# gives neither.
#
# ## Part C — what happens first in the real plan
#
# Run the plan as written and this lab's problem never shows up, because something else stops it
# first. The plan's pool holds one checkpoint for episodes 0 to 999, and its `sample()` raises a
# `ValueError` about seven times in ten on a one-entry pool (lab p8-03). The first opponent only
# matters once that is fixed. Fix the crash, then fix the seed.
