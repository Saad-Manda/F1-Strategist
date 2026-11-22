# %% [markdown]
# # Lab p9-01 · The log-gradient trick
#
# **Goes with:** Phase 9, page 01 — Policy gradients, REINFORCE · **Time:** about 20 minutes
#
# Page 01 derived one formula, ∇log π(a), and one algorithm built on it. Here you write the
# formula, check it against brute-force finite differences, then use it to train a policy on a
# problem built to embarrass anything that picks one action deterministically.
#
# **Environment:** the short corridor with switched actions (Sutton & Barto, Example 13.1). Four
# cells, start in cell 0, reach cell 3 to finish, −1 per step. In cell 1 the actions are
# reversed. The policy cannot tell the cells apart: it chooses one probability of pressing
# "right", used everywhere. It is in `labs/labkit/corridor.py`.
#
# Stuck? Run `python -m labs hint p9-01` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import corridor, predict

LAB = "p9-01"

# %% [markdown]
# ## Part A — softmax and its log-gradient
#
# **TODO 1.** `softmax(z)`: probabilities from logits. Subtract the largest logit before
# exponentiating, so a logit of 1000 does not overflow.
#
# **TODO 2.** `log_softmax_grad(z, a)`: the vector ∂ log π(a) / ∂z_b for every b. Page 01 gives it:
# 1 − π(a) for the action taken, −π(b) for every other.

# %%
def softmax(z):
    """Probabilities from a vector of logits."""
    # >>> SOLUTION: e = np.exp(z - z.max()); return e / e.sum()
    e = np.exp(z - np.max(z))
    return e / e.sum()
    # <<< SOLUTION


def log_softmax_grad(z, a):
    """d log softmax(z)[a] / dz, a vector the size of z."""
    # >>> SOLUTION: start from -softmax(z) and add 1 at index a
    g = -softmax(z)
    g[a] += 1.0
    return g
    # <<< SOLUTION


checks.gradient(softmax, log_softmax_grad)

# %% [markdown]
# Why do the components sum to zero? Add the same number to every logit and no probability
# changes, so the gradient can have no component along "all logits together".

# %% [markdown]
# ## Part B — REINFORCE on the corridor
#
# The policy's two logits are (0 for left, θ for right), so π(right) = `corridor.p_right(θ)`, and
# by TODO 2:
#
# ∂ log π(right) / ∂θ = 1 − p  and  ∂ log π(left) / ∂θ = −p.
#
# **TODO 3.** `episode_gradient(theta, ep)`: page 01's estimate from one episode,
# Σ_t G_t · ∂ log π(a_t) / ∂θ, where G_t is the return from step t to the end. `ep` is a list of
# `(cell, action, reward)`. Use the p of the θ the episode was played with.

# %%
def episode_gradient(theta, ep):
    """REINFORCE's gradient estimate from one episode played at theta."""
    p = corridor.p_right(theta)
    rewards = np.array([r for _, _, r in ep])
    # >>> SOLUTION: G = reversed cumulative sum of rewards; sum G_t times (1 - p if right else -p)
    G = np.cumsum(rewards[::-1])[::-1]
    return float(sum(((1 - p) if a == corridor.RIGHT else -p) * g for (_, a, _), g in zip(ep, G)))
    # <<< SOLUTION


def reinforce(alpha, episodes, seed, theta=-1.5):
    """Plain REINFORCE. Returns the exact start value after every episode."""
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(episodes):
        ep = corridor.episode(theta, rng)
        theta += alpha * episode_gradient(theta, ep)
        values.append(corridor.true_value(corridor.p_right(theta)))
    return np.array(values)


values = np.array([reinforce(2**-12, 1000, seed) for seed in range(20)])
plt.plot(values.mean(axis=0), label="REINFORCE, α = 2⁻¹², mean of 20 seeds")
plt.axhline(corridor.best_p()[1], color="k", ls="--", label="best possible, −11.66")
plt.xlabel("episode"); plt.ylabel("exact value of the start cell"); plt.legend(); plt.show()
checks.reinforce_works(values)

# %% [markdown]
# Each point is the policy's *exact* value (`corridor.true_value`), not a noisy episode return,
# so what wobbles is the policy itself. The learner starts preferring left (θ = −1.5, about one
# press of "right" in five) and drifts towards a mix.

# %% [markdown]
# ## Part C — predict, then compute: the best fixed action
#
# A Q-learner from Phase 4, given these observations, ends up with one greedy action used in
# every cell. What is the best such fixed policy worth?

# %%
CHOICES = {
    "close": "always-right is a little worse than the best mix",
    "far": "always-right is much worse, but finishes",
    "never": "no fixed action ever reaches the goal",
}
my_prediction = "never"  # >>> ANSWER
predict.commit(LAB, "fixed", my_prediction, CHOICES)

# %%
always_right = corridor.true_value(1.0)
always_left = corridor.true_value(0.0)
best = corridor.best_p()
print(f"always right: {always_right}   always left: {always_left}   best mix: p = {best[0]:.3f}, value {best[1]:.2f}")
ps = np.linspace(0.02, 0.98, 200)
plt.plot(ps, [corridor.true_value(p) for p in ps]); plt.ylim(-100, 0)
plt.xlabel("probability of pressing right"); plt.ylabel("value of the start cell"); plt.show()
predict.reveal(LAB, "fixed", "both fixed policies hit the 1,000-step cut-off", correct="never")
checks.fixed_policies(always_right, always_left, best)

# %% [markdown]
# Always-right goes 0 → 1 → 0 → 1 forever (cell 1 sends "right" back left); always-left never
# leaves cell 0. When different states look the same, the best policy can be a *random* one, and
# a method that learns probabilities directly can represent it. An argmax over values cannot.
# That is one reason, among page 01's, to learn a policy directly.
