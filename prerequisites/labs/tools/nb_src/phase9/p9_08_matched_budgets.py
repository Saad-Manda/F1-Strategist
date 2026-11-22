# %% [markdown]
# # Lab p9-08 · Matched budgets
#
# **Goes with:** Phase 9, page 08 — "Same timesteps" isn't "same experience" · **Time:** about 15 minutes
#
# Page 08 found that the plan's "fair" comparison gives PPO about 7.7 times DQN's experience. Here
# the same mistake is made on purpose, on the toy race, with two learners whose distance from the
# optimum is known exactly at every checkpoint. You compare them the plan's way, then at matched
# experience, and measure how much of the first answer was the budget.
#
# **Learners:** an off-policy table Q-learner (`labs/labkit/qtable.py`, the p4-cap learner) and an
# on-policy mini PPO (`labs/labkit/minipg.py`). Three seeds each. Every race is 20 laps, so
# 20 environment steps; a checkpoint is the exact gap of the greedy policy to the optimum, in
# seconds.
#
# A note on axes, before anything is plotted: every race here has the same length, as every real
# race has 52 laps. So "per race" and "per step" are the same axis scaled by 20, and re-plotting
# cannot change which curve is ahead. What changes a comparison is **where on the axis each learner
# is read**.
#
# Stuck? Run `python -m labs hint p9-08` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import minipg, predict, qtable

LAB = "p9-08"

# %% [markdown]
# ## Training (given, about a minute and a half)
#
# The PPO learner gets 2,000 races (40,000 steps), the Q-learner 3,000 (60,000 steps).

# %%
ppo = [minipg.train("ppo", 2000, seed, checkpoint_every=200).curve for seed in range(3)]
q = [qtable.train(3000, seed, checkpoint_every=100)[1] for seed in range(3)]

for curves, name, colour in ((ppo, "mini PPO (on-policy)", "C0"), (q, "table Q-learner (off-policy)", "C1")):
    for i, c in enumerate(curves):
        plt.plot(*zip(*c), color=colour, alpha=0.6, label=name if i == 0 else None)
plt.yscale("symlog", linthresh=1); plt.xlabel("environment steps"); plt.ylabel("exact gap to the optimum, s")
plt.legend(); plt.show()

# %% [markdown]
# ## Part A — reading a curve
#
# **TODO 1.** `gap_at(curve, steps)`: the gap at the last checkpoint at or before a budget.
#
# **TODO 2.** `window_mean(curve, lo, hi)`: the mean gap over the checkpoints between `lo` and `hi`
# steps, both included.

# %%
def gap_at(curve, steps):
    # >>> SOLUTION: the gap of the last (s, g) with s <= steps
    return [g for s, g in curve if s <= steps][-1]
    # <<< SOLUTION


def window_mean(curve, lo, hi):
    # >>> SOLUTION: mean of g over the checkpoints with lo <= s <= hi
    return float(np.mean([g for s, g in curve if lo <= s <= hi]))
    # <<< SOLUTION


checks.readers(gap_at, window_mean)

# %% [markdown]
# ## Part B — the plan's comparison, then a fair one
#
# The plan's mistake, made the other way round so it is easy to see: the PPO learner is read at
# its full 40,000 steps, the Q-learner at 5,000, eight times less. Then both are read over the same
# window of experience, 30,000 to 40,000 steps, averaged over the checkpoints in it.
#
# Before running: how much of the unmatched margin survives?

# %%
CHOICES = {
    "all": "most of it: PPO is simply better here",
    "quarter": "about a quarter: most of the margin was the budget",
    "none": "none: at matched budgets they are level",
}
my_prediction = "quarter"  # >>> ANSWER
predict.commit(LAB, "margin", my_prediction, CHOICES)

# %%
unfair = np.mean([gap_at(c, 5_000) for c in q]) - np.mean([gap_at(c, 40_000) for c in ppo])
matched = np.mean([window_mean(c, 30_000, 40_000) for c in q]) - np.mean([window_mean(c, 30_000, 40_000) for c in ppo])
print(f"unmatched (Q at 5k, PPO at 40k): Q is {unfair:.1f} s further from the optimum")
print(f"matched (both over 30k-40k):      Q is {matched:.1f} s further from the optimum")
predict.reveal(LAB, "margin", f"{unfair:.1f} s shrank to {matched:.1f} s", correct="quarter")
checks.margins(unfair, matched)

# %% [markdown]
# The ranking survived; the size of the win did not. On this toy the on-policy learner really is
# ahead at matched experience, by a few seconds. The unmatched comparison reported about four
# times that, and nothing in its numbers would have told you. In the real plan the unmatched side
# is DQN at 260,000 steps against PPO at 2,000,000: the same shape, and a headline number that
# cannot be taken at face value until the budgets are matched or the curves are read at the same
# point.

# %% [markdown]
# ## Part C — one checkpoint is a sample
#
# The Q-learner's curve jumps around: with a constant step size and exploration still on, its
# greedy policy keeps switching between nearby plans. So what is its "final result" worth?
#
# The cell lists, for each seed, the smallest and largest single checkpoint inside the same
# 30,000–40,000 window.

# %%
spread = []
for seed, c in enumerate(q):
    inside = [g for s, g in c if 30_000 <= s <= 40_000]
    spread.append(max(inside) - min(inside))
    print(f"Q-learner seed {seed}: single checkpoints from {min(inside):.2f} to {max(inside):.2f} s;  final checkpoint at 60k: {c[-1][1]:.2f} s")
checks.single_checkpoints(spread)

# %% [markdown]
# Report one checkpoint and you could have reported almost anything in that range. This is why
# the plan's comparison notebook should show curves on a shared step axis, with seeds, rather than
# one final number per algorithm, and why Phase 3's paired-seed evaluation is necessary but not
# sufficient: it controls evaluation luck, not *which* point of training is being evaluated.
