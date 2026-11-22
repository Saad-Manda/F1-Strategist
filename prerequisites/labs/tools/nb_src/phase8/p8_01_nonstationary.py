# %% [markdown]
# # Lab p8-01 · When the opponent learns too
#
# **Goes with:** Phase 8, page 01 — Non-stationarity, revisited · **Time:** about 15 minutes
#
# Page 01 makes two claims. Once the opponent learns, the thing each learner is trying to learn
# keeps moving. And a replay buffer filled against an old opponent describes a game that no
# longer exists. Part A watches the first happen; Part B measures the second.
#
# **Environment:** matching pennies. Two players each show heads (H) or tails (T). The row player
# wins 1 on a match, the column player wins 1 on a mismatch. No choice is best against everything:
# whatever one player does, the other has a reply that beats it.
#
# Stuck? Run `python -m labs hint p8-01` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import games, predict

LAB = "p8-01"
U = games.MATCHING_PENNIES  # U[row action, column action], row player's payoff; H = 0, T = 1

# %% [markdown]
# ## Part A — two learners, each the other's environment
#
# Each player keeps one number per action: Q[a], its running estimate of the payoff of a.
# There is no state, so this is Phase 4's update with nothing after the reward.
#
# **TODO 1.** `update(q, a, reward, alpha)`: move q[a] a fraction alpha of the way towards the
# reward, in place.
#
# **TODO 2.** `choose(q, eps, rng)`: with probability eps a uniformly random action, otherwise
# the action with the larger Q (break ties at random).

# %%
def update(q, a, reward, alpha):
    # >>> SOLUTION: q[a] += alpha * (reward - q[a])
    q[a] += alpha * (reward - q[a])
    # <<< SOLUTION


def choose(q, eps, rng):
    # >>> SOLUTION: explore with probability eps, else argmax with random tie-breaking
    if rng.random() < eps:
        return int(rng.integers(len(q)))
    best = np.flatnonzero(q == q.max())
    return int(rng.choice(best))
    # <<< SOLUTION


checks.update_and_choose(update, choose)

# %% [markdown]
# **Predict.** Both learners use α = 0.1 and ε = 0.1 for 5,000 rounds. Against a *fixed*
# opponent this learner would settle on one action within a few dozen rounds. Here?

# %%
CHOICES = {
    "settle": "both settle on one action each and stay there",
    "one": "one of them settles; the other keeps adjusting",
    "chase": "neither settles: each keeps switching as the other adapts",
}
my_prediction = "chase"  # >>> ANSWER
predict.commit(LAB, "settle", my_prediction, CHOICES)

# %%
def play(rounds=5000, alpha=0.1, eps=0.1, seed=0):
    rng = np.random.default_rng(seed)
    q = [np.zeros(2), np.zeros(2)]
    greedy = [[], []]
    for _ in range(rounds):
        a, b = choose(q[0], eps, rng), choose(q[1], eps, rng)
        r = U[a, b]
        update(q[0], a, r, alpha)
        update(q[1], b, -r, alpha)
        greedy[0].append(int(np.argmax(q[0])))
        greedy[1].append(int(np.argmax(q[1])))
    return np.array(greedy)


greedy = play()
flips = [int(np.sum(np.diff(g) != 0)) for g in greedy]
fig, ax = plt.subplots(figsize=(10, 2.6))
ax.step(range(400), greedy[0][:400], label="row's greedy action", where="post")
ax.step(range(400), greedy[1][:400] + 0.04, label="column's greedy action", where="post")
ax.set_yticks([0, 1], ["H", "T"]); ax.set_xlabel("round"); ax.legend(loc="upper right"); plt.show()
print(f"greedy action changed {flips[0]} times (row) and {flips[1]} times (column) in 5,000 rounds")
predict.reveal(LAB, "settle", f"neither settles: {flips[0]} and {flips[1]} switches", correct="chase")
checks.keeps_moving(flips)

# %% [markdown]
# Each learner is doing exactly what Phase 4 taught it to do: estimate the payoff of each action
# and pick the larger. The estimates are good, for the opponent of a few rounds ago. By the time a
# learner has switched to the reply that beats the opponent, the opponent has started switching too.
# Nothing is wrong with either learner; what they learn about has stopped holding still.

# %% [markdown]
# ## Part B — a replay buffer from an older game
#
# The column player used to show heads 80% of the time; it now shows heads 20% of the time. A
# replay buffer holds 2,000 rounds from the old days and 200 from the new. Against the new
# opponent, the row player's true values are Q(H) = 0.2 − 0.8 = −0.6 and Q(T) = +0.6.
#
# **TODO 3.** `fit_from_buffer(buffer, updates, alpha, rng)`: start from Q = (0, 0) and make
# `updates` updates, each on one (my action, their action) pair drawn uniformly from the buffer,
# with reward U[my action, their action]. Return Q.

# %%
def fit_from_buffer(buffer, updates, alpha, rng):
    q = np.zeros(2)
    # >>> SOLUTION: sample a pair uniformly, then the TODO 1 update with reward U[a, o]
    for _ in range(updates):
        a, o = buffer[int(rng.integers(len(buffer)))]
        update(q, a, U[a, o], alpha)
    # <<< SOLUTION
    return q


rng = np.random.default_rng(1)
old = [(int(rng.integers(2)), int(rng.random() >= 0.8)) for _ in range(2000)]  # opponent: H 80% of the time
new = [(int(rng.integers(2)), int(rng.random() >= 0.2)) for _ in range(200)]  # opponent: H 20% of the time
true_q = np.array([-0.6, 0.6])

replayed = fit_from_buffer(old + new, 2000, 0.05, np.random.default_rng(2))
fresh = fit_from_buffer(new, 2000, 0.05, np.random.default_rng(2))
for name, q in (("whole buffer", replayed), ("new rounds only", fresh)):
    print(f"{name:16s} Q(H) = {q[0]:+.2f}  Q(T) = {q[1]:+.2f}   error {np.abs(q - true_q).mean():.2f}   greedy {'HT'[int(np.argmax(q))]}")
checks.stale_replay(replayed, fresh, true_q)

# %% [markdown]
# The whole-buffer learner is confidently wrong: it prefers H, the right reply to the opponent
# that no longer exists. Phase 5 replayed transitions to break up correlation, and that still holds.
# With a learning opponent there is a second reason to care how old a transition is. Page 03's
# checkpoint pool changes what the opponent *is* (a mixture of past selves), which is one way the
# real plan keeps the buffer's game and the current game closer together.
