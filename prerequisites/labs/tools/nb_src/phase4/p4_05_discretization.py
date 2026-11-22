# %% [markdown]
# # Lab p4-05 · How many bins?
#
# **Goes with:** Phase 4, page 05 — State discretization: the general tradeoff · **Time:** about 20 minutes
#
# The page says too few bins cannot represent the answer and too many cannot be learned in
# the time available. Here you measure both failures on one problem, and find that the best
# bin count is not a fixed number.
#
# **Environment:** the 1000-state random walk from Sutton & Barto, Example 9.1. States are
# numbered 1 to 1000 and the walk starts at 500. Each step it jumps 1 to 100 states left or
# right at random. Falling off the left end pays −1, off the right end +1, and everything
# else pays 0. There are no actions: the task is only to estimate each state's value, which
# runs from about −0.92 at state 1 to +0.92 at state 1000.
#
# A thousand states is too many to learn one by one from a few hundred walks, so neighbouring
# states are grouped into bins that share one number. That is exactly what `discretize_obs`
# does to tyre age.
#
# Stuck? Run `python -m labs hint p4-05` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import envs, predict
from labs.labkit.envs import WALK_START, WALK_STATES

LAB = "p4-05"
TRUE_VALUES = envs.walk_true_values()  # exact, from the known model; index 0 is state 1
print("true value of states 1, 500, 1000:", np.round(TRUE_VALUES[[0, 499, 999]], 3))

# %% [markdown]
# ## Part A — the binning function
#
# **TODO 1.** Implement `group_of`: which of `n_groups` equal-width bins a state falls in.
# States are 1 to 1000, bins are numbered from 0. With 10 groups, states 1–100 are bin 0,
# states 101–200 are bin 1, and so on. Use whole-number arithmetic (`//`), and make sure
# state 1000 lands in the last bin and not one past it.

# %%
def group_of(state, n_groups):
    """The bin (0 .. n_groups - 1) that `state` (1 .. 1000) belongs to."""
    # >>> SOLUTION: (state - 1) * n_groups // WALK_STATES, capped at n_groups - 1
    return min((state - 1) * n_groups // WALK_STATES, n_groups - 1)
    # <<< SOLUTION


checks.grouping(group_of)

# %% [markdown]
# ## Part B — learn a value per bin
#
# **TODO 2.** Implement `learn_values`. Keep one number per bin in `values` (start at zero).
# Run `episodes` walks. In each walk, start at `WALK_START` and repeat until the walk ends:
#
# 1. `next_state, reward, done = envs.walk_step(state, rng)`
# 2. `target = reward` if `done`, otherwise `reward + values[bin of next_state]`
# 3. move `values[bin of state]` a fraction `alpha` of the way toward `target`
# 4. `state = next_state`
#
# This is page 01's TD update with a bin where the table cell used to be.

# %%
def learn_values(n_groups, episodes, rng, alpha=0.1):
    """TD learning of one value per bin. Returns an array of length n_groups."""
    # >>> SOLUTION: for each episode walk from WALK_START with envs.walk_step, nudging values[group_of(state)] toward reward + values[group_of(next_state)] (or just reward at the end)
    values = np.zeros(n_groups)
    for _ in range(episodes):
        state, done = WALK_START, False
        while not done:
            next_state, reward, done = envs.walk_step(state, rng)
            target = reward if done else reward + values[group_of(next_state, n_groups)]
            g = group_of(state, n_groups)
            values[g] += alpha * (target - values[g])
            state = next_state
    return values
    # <<< SOLUTION


def rms_error(values, n_groups):
    """How far the binned estimate is from the truth, over all 1000 states."""
    estimate = np.array([values[group_of(s, n_groups)] for s in range(1, WALK_STATES + 1)])
    return float(np.sqrt(np.mean((estimate - TRUE_VALUES) ** 2)))


checks.learning(learn_values, rms_error)

# %% [markdown]
# ## Part C — too few, too many
#
# A fixed budget of **200 walks**, and three bin counts: 2, 20 and 1000 (one bin per state,
# which is no binning at all).
#
# **TODO — predict before you run.** Which gives the smallest error?

# %%
CHOICES = {
    "2": "2 bins: each one sees the most data",
    "20": "20 bins",
    "1000": "1000 bins: nothing is lost to binning",
}
my_prediction = "20"  # >>> ANSWER

predict.commit(LAB, "bins", my_prediction, CHOICES)

# %%
def average_error(n_groups, episodes, seeds=(0, 1, 2)):
    return float(np.mean([rms_error(learn_values(n_groups, episodes, np.random.default_rng(s)), n_groups) for s in seeds]))


errors_200 = {n: average_error(n, 200) for n in (2, 20, 1000)}
for n, e in errors_200.items():
    print(f"{n:>4} bins, 200 walks: RMS error {e:.3f}")

fig, axes = plt.subplots(1, 3, figsize=(12, 3.2), sharey=True)
states = np.arange(1, WALK_STATES + 1)
for ax, n in zip(axes, (2, 20, 1000)):
    values = learn_values(n, 200, np.random.default_rng(0))
    ax.plot(states, TRUE_VALUES, color="gray", label="true value")
    ax.plot(states, [values[group_of(s, n)] for s in states], label="learned")
    ax.set_title(f"{n} bins")
    ax.set_xlabel("state")
axes[0].set_ylabel("value")
axes[0].legend()
plt.show()

best = min(errors_200, key=errors_200.get)
predict.reveal(LAB, "bins", f"{best} bins had the smallest error", correct="20")
checks.tradeoff(errors_200)

# %% [markdown]
# Read the three pictures.
#
# - **2 bins** is a staircase with two steps. Each step is learned well. The staircase simply
#   cannot follow the line: 500 different states are forced to share one number. More walks
#   would not help. This is the failure page 06 finds in the real plan's tyre-age bins.
# - **1000 bins** could follow the line perfectly and has barely started to. Most states were
#   visited a handful of times or never, and are still at zero. Nothing is wrong with the
#   representation. There is not enough experience to fill it.
# - **20 bins** loses a little to the staircase and learns each step well.
#
# ## Part D — the best count depends on the budget
#
# Give the learner five times as much experience, **1000 walks**, and compare 20, 50 and 200
# bins at both budgets.

# %%
table = {}
for episodes in (200, 1000):
    table[episodes] = {n: average_error(n, episodes) for n in (20, 50, 200)}
    row = "   ".join(f"{n} bins: {e:.3f}" for n, e in table[episodes].items())
    print(f"{episodes:>4} walks   {row}")
checks.budget(table)

# %% [markdown]
# With 200 walks, 20 bins is best. With 1000 walks, 50 bins is. More experience can fill a
# finer table, so the right resolution moves with the training budget.
#
# So a bin count is a claim about two things at once: how fine the decision is, and how much
# experience there will be. The real plan fixed its bins before either was measured. Page 06
# shows what that cost.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
