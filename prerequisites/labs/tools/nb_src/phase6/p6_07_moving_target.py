# %% [markdown]
# # Lab p6-07 · A target that moves
#
# **Goes with:** Phase 6, page 07 — Non-stationarity · **Time:** about 15 minutes
#
# Page 07 says that everything through Phase 5 assumes the environment holds still, and that a
# fixed-script rival keeps that assumption true while a learning one would not. Here you watch
# the difference in the smallest game that shows it.
#
# **The game.** Each round you choose to pit EARLY (0) or LATE (1), and so does the opponent.
# Choosing differently from the opponent scores +1 (you get clean air); choosing the same scores
# −1. You keep one value per choice and update it after every round, choosing ε-greedily
# (ε = 0.1). 4,000 rounds.
#
# Two opponents. The **fixed** one pits late 30% of the time, every round, whatever you do: a
# script. The **adapting** one watches what you have mostly been doing lately and copies it,
# 90% of the time, which is the move that hurts you most.
#
# Stuck? Run `python -m labs hint p6-07` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import predict

LAB = "p6-07"
EARLY, LATE = 0, 1
ROUNDS = 4000


def opponent_late_chance(kind, recent):
    """How likely the opponent is to pit LATE this round. recent = your recent choice shares (EARLY, LATE)."""
    if kind == "fixed":
        return 0.3
    return 0.05 + 0.9 * (recent[LATE] > recent[EARLY])  # copy your more frequent recent choice, 90% of the time


def true_values(p_late):
    """What each of your choices is worth this round, given the opponent's current LATE chance."""
    return np.array([p_late - (1 - p_late), (1 - p_late) - p_late])  # EARLY scores when they go LATE, and vice versa

# %% [markdown]
# ## Part A — against a script
#
# **TODO 1.** `step_size_update`: move the chosen action's value a fixed fraction `alpha` of the
# way toward the reward just received (Phase 4's update with nothing after it: each round is a
# whole episode). **TODO 2.** `average_update`: the same with `alpha = 1 / n`, where `n` counts
# how many times this action has been chosen, including now. That makes the value the exact
# average of every reward the action has ever received. `counts` is changed in place too.

# %%
def step_size_update(values, counts, a, r, alpha=0.05):
    """Constant step size: values[a] moves alpha of the way toward r."""
    # >>> SOLUTION: values[a] += alpha * (r - values[a])
    values[a] += alpha * (r - values[a])
    # <<< SOLUTION


def average_update(values, counts, a, r, alpha=None):
    """Sample average: counts[a] += 1, then values[a] moves 1 / counts[a] of the way toward r."""
    # >>> SOLUTION: counts[a] += 1; values[a] += (r - values[a]) / counts[a]
    counts[a] += 1
    values[a] += (r - values[a]) / counts[a]
    # <<< SOLUTION


checks.updates(step_size_update, average_update)


def play(kind, update, seed, eps=0.1):
    """Given. Returns the values after every round, the greedy choice, and the true values."""
    rng = np.random.default_rng(seed)
    values, counts, recent = np.zeros(2), np.zeros(2), np.array([0.5, 0.5])
    history, greedy_choice, truth = [], [], []
    for _ in range(ROUNDS):
        g = int(rng.choice(np.flatnonzero(values == values.max())))
        a = int(rng.integers(2)) if rng.random() < eps else g
        p_late = opponent_late_chance(kind, recent)
        o = int(rng.random() < p_late)
        update(values, counts, a, 1.0 if a != o else -1.0)
        recent = 0.98 * recent
        recent[a] += 0.02
        history.append(values.copy())
        greedy_choice.append(g)
        truth.append(true_values(p_late))
    return np.array(history), np.array(greedy_choice), np.array(truth)


def flips(greedy_choice):
    """How often the greedy choice changes in the second half."""
    second = greedy_choice[ROUNDS // 2 :]
    return int(np.sum(second[1:] != second[:-1]))


history, choice, truth = play("fixed", step_size_update, seed=0)
fig, ax = plt.subplots(figsize=(7, 3))
ax.plot(history[:, EARLY], label="value of EARLY")
ax.plot(history[:, LATE], label="value of LATE")
ax.axhline(0.4, ls=":", color="grey")
ax.axhline(-0.4, ls=":", color="grey")
ax.set_xlabel("round")
ax.legend(fontsize=8)
ax.set_title("against the fixed script")
plt.show()
fixed_flips = [flips(play("fixed", step_size_update, s)[1]) for s in range(5)]
print("greedy flips in the second half, five seeds:", fixed_flips)
checks.settles(fixed_flips)

# %% [markdown]
# The values settle near their true worth (EARLY +0.4, LATE −0.4: the dotted lines) and wobble
# around it. The greedy choice stops changing. This is the world Phases 4 and 5 assume.
#
# ## Part B — against an opponent that adapts
#
# **Predict first.** Same learner, same 4,000 rounds, the adapting opponent. In the second half,
# how often does your greedy choice flip?

# %%
CHOICES = {
    "never": "never: the values settle, just at different numbers",
    "a-few": "a handful of times while it settles",
    "dozens": "dozens of times: it never settles",
}
my_prediction = "dozens"  # >>> ANSWER

predict.commit(LAB, "flips", my_prediction, CHOICES)

# %%
history, choice, truth = play("adapting", step_size_update, seed=0)
fig, ax = plt.subplots(figsize=(7, 3))
ax.plot(history[:, EARLY], label="value of EARLY")
ax.plot(history[:, LATE], label="value of LATE")
ax.set_xlabel("round")
ax.legend(fontsize=8)
ax.set_title("against the adapting opponent")
plt.show()
adapting_flips = [flips(play("adapting", step_size_update, s)[1]) for s in range(5)]
print("greedy flips in the second half, five seeds:", adapting_flips)
predict.reveal(LAB, "flips", f"between {min(adapting_flips)} and {max(adapting_flips)} flips in 2,000 rounds", correct="dozens")
checks.chases(adapting_flips)

# %% [markdown]
# As soon as one choice looks better and you start making it, the opponent starts copying it,
# and it becomes the worse one. Nothing about the game's rules changed; the thing you were
# estimating moved because of what you did.
#
# ## Part C — the right tool for a world that holds still
#
# The sample average is the textbook estimate: with a fixed opponent it converges to the exact
# true value, and a constant step size never quite does. Measure both rules against both
# opponents: the mean distance between your values and the true values in the second half.

# %%
def tracking_error(kind, update):
    errs = []
    for s in range(5):
        history, _, truth = play(kind, update, s)
        errs.append(np.abs(history[ROUNDS // 2 :] - truth[ROUNDS // 2 :]).mean())
    return float(np.mean(errs))


table = {(kind, name): tracking_error(kind, fn) for kind in ("fixed", "adapting") for name, fn in (("step size 0.05", step_size_update), ("sample average", average_update))}
for (kind, name), err in table.items():
    print(f"{kind:9s} {name:15s} mean error {err:.3f}")
checks.tracking(table)

# %% [markdown]
# Against the script the sample average is nearly exact (about 0.02) and the constant step
# size wobbles (about 0.10): when the world holds still, averaging everything is the right
# thing to do, and the convergence results of Phases 4 and 5 apply. Against the adapting
# opponent neither rule gets close (both about 0.9): there is no fixed number to converge to.
#
# That is page 07's argument in two numbers. Phase 6's rivals are scripts, so the first row is
# the world the agent learns in and all of the earlier theory still applies. Phase 8 is where
# the second row begins.
