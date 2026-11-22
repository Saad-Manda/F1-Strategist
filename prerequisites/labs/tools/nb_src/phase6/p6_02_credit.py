# %% [markdown]
# # Lab p6-02 · Sparse, dense, and farmed
#
# **Goes with:** Phase 6, page 02 — Credit assignment · **Time:** about 20 minutes
#
# Page 02 makes two claims. A reward that arrives only at the end gives a learner very little to
# work with on every other step. A denser stand-in fixes that, but becomes something an agent
# can optimise instead of the goal. Here you measure both: first how much slower a learner is
# when the only reward is at the finish, then the point at which a helpful little bonus turns
# into the thing the agent does instead of finishing.
#
# **Environments:** a 1-D corridor (start at one end, the episode ends at the other), and a 5×5
# grid with a goal worth +10 and a bonus tile that comes back three steps after it is taken.
# Both are in `labs/labkit/envs.py`.
#
# Stuck? Run `python -m labs hint p6-02` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import envs, predict

LAB = "p6-02"

# %% [markdown]
# ## Part A — a learner for the corridor
#
# **TODO 1.** `td_update`: the Q-learning update from Phase 4, for one transition. The target is
# `r` when the step ended the episode, and `r + γ·max Q[s2]` otherwise; move `Q[s, a]` a fraction
# `alpha` of the way toward it. Change `Q` in place.
#
# **TODO 2.** `greedy`: the best action of one row of Q, with **random** tie-breaks. At the start
# every value is 0. If ties always went to action 0 (left), the sparse learner would push into
# the wall forever and never see its one reward.

# %%
def td_update(Q, s, a, r, s2, done, alpha, gamma):
    """One Q-learning update of Q[s, a], in place."""
    # >>> SOLUTION: target = r if done else r + gamma * Q[s2].max(); Q[s, a] += alpha * (target - Q[s, a])
    target = r if done else r + gamma * Q[s2].max()
    Q[s, a] += alpha * (target - Q[s, a])
    # <<< SOLUTION


def greedy(q_row, rng):
    """Index of the largest value in q_row; ties broken uniformly at random with rng."""
    # >>> SOLUTION: rng.choice over np.flatnonzero(q_row == q_row.max())
    return int(rng.choice(np.flatnonzero(q_row == q_row.max())))
    # <<< SOLUTION


checks.update_and_tiebreak(td_update, greedy)

# %% [markdown]
# The loop is given. It counts **steps**, not episodes: what the learner pays for is experience,
# and an episode with a sparse reward can be very long before anything is learned from it.
# Learning is "done" when the greedy action points right in every cell.

# %%
GAMMA = {"dense": 1.0, "sparse": 0.95}  # with only +1 at the end, a discount is what makes shorter better


def run_corridor(n, kind, seed, eps=0.1, alpha=0.5, max_steps=400_000):
    rng = np.random.default_rng(seed)
    Q = np.zeros((n, 2))
    steps = 0
    while steps < max_steps:
        s, done = 0, False
        while not done:
            a = int(rng.integers(2)) if rng.random() < eps else greedy(Q[s], rng)
            s2, r, done = envs.corridor_step(s, a, n, kind)
            td_update(Q, s, a, r, s2, done, alpha, GAMMA[kind])
            s, steps = s2, steps + 1
        if all(Q[i, 1] > Q[i, 0] for i in range(n - 1)):
            return steps
    return steps


print("dense, n = 10:", [run_corridor(10, "dense", s) for s in range(5)], "steps")
print("sparse, n = 10:", [run_corridor(10, "sparse", s) for s in range(5)], "steps")

# %% [markdown]
# ## Part B — as the corridor grows
#
# At n = 5 the two rewards need about the same number of steps. **Predict first:** at n = 40,
# how many times as many steps does the sparse learner need?

# %%
CHOICES = {
    "about-1": "about the same: both learn the same policy",
    "2-to-3": "two or three times as many",
    "more-than-3": "more than three times as many, and the ratio keeps growing with n",
}
my_prediction = "more-than-3"  # >>> ANSWER

predict.commit(LAB, "ratio", my_prediction, CHOICES)

# %%
SIZES = [5, 10, 20, 40]
medians = {kind: [float(np.median([run_corridor(n, kind, s) for s in range(10)])) for n in SIZES] for kind in ("dense", "sparse")}
fig, ax = plt.subplots(figsize=(5.5, 3.4))
for kind, marker in (("dense", "o-"), ("sparse", "s-")):
    ax.loglog(SIZES, medians[kind], marker, label=kind)
ax.set_xlabel("corridor length n")
ax.set_ylabel("steps until the policy is right (median of 10)")
ax.legend()
plt.show()
for n, d, s in zip(SIZES, medians["dense"], medians["sparse"]):
    print(f"n = {n:2d}: dense {d:7.0f}   sparse {s:7.0f}   ratio {s / d:4.1f}")
predict.reveal(LAB, "ratio", f"at n = 40 the sparse learner needed {medians['sparse'][-1] / medians['dense'][-1]:.1f} times as many steps", correct="more-than-3")
checks.growth(SIZES, medians)

# %% [markdown]
# The two lines spread apart as n grows (at n = 80, not run here, the ratio is about 10:
# 19,000 steps against 180,000). The dense learner is told something on every step, and its
# all-zero start makes every untried action look better than one it has paid for, which pushes
# it along. The sparse learner wanders without information until it first stumbles on the end,
# and then the news travels back one cell per visit. Final position in a race is this kind of
# reward: one number, fifty laps after the decisions it judges.

# %% [markdown]
# ## Part C — when the stand-in becomes the goal
#
# The 5×5 grid: the goal is worth +10 and ends the episode, and the tile in the middle pays `b`
# whenever it is entered and available. Once taken it comes back after 3 steps, so an agent that
# loops on it collects `b` every 4 steps. γ = 0.95, episodes capped at 40 steps.
#
# **TODO 3.** `loop_value(b, gamma, period)`: what looping is worth from the moment you take the
# tile, `b + γ^period·b + γ^(2·period)·b + …`, a geometric series. **TODO 4.** `break_even`: the
# `b` at which that loop is worth as much as the goal's 10.

# %%
def loop_value(b, gamma, period=4):
    """Discounted value of collecting b now and every `period` steps forever."""
    # >>> SOLUTION: b / (1 - gamma ** period)
    return b / (1 - gamma**period)
    # <<< SOLUTION


def break_even(gamma, goal=10.0, period=4):
    """The bonus b at which loop_value(b) equals goal."""
    # >>> SOLUTION: goal * (1 - gamma ** period)
    return goal * (1 - gamma**period)
    # <<< SOLUTION


print(f"the loop beats the goal once b > {break_even(0.95):.2f}")
checks.closed_form(loop_value, break_even)

# %% [markdown]
# That ignores the walk to the tile and the 40-step cap, so it is only a rough threshold. Now
# train a learner (given, `envs.farm_learn`) at four values of `b`, three seeds each, and look at
# what its greedy policy does. About 15 seconds.

# %%
results = {b: [envs.farm_learn(b, seed) for seed in range(3)] for b in (0.0, 0.5, 1.0, 2.0)}
for b, runs in results.items():
    print(
        f"b = {b}: finish rate {np.mean([r['finish_rate'] for r in runs]):.2f}, "
        f"steps {np.mean([r['steps'] for r in runs]):4.1f}, bonuses per episode {np.mean([r['bonuses'] for r in runs]):4.1f}"
    )
checks.farming(results)

# %% [markdown]
# Below the threshold the bonus bends the route (at b = 1 the agent detours over the tile once)
# but it still finishes. Above it, the agent never finishes: it collects the bonus about ten
# times an episode, every episode. Nothing is wrong with the learner. It is doing exactly what
# its reward asks, and the reward stopped meaning "finish".
#
# That is the shape page 02 warns about. Page 03 returns to this grid: the same "this way is
# better" hint, written as a **potential**, cannot be farmed.
