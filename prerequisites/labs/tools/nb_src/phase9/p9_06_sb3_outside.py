# %% [markdown]
# # Lab p9-06 · The library, from the outside
#
# **Goes with:** Phase 9, page 06 — Stable-Baselines3 and sb3-contrib's API surface · **Time:** about 20 minutes
#
# Page 06 described what `.learn()` and `.predict()` do. Here you drive them: the rollout
# arithmetic first, then a short run you read through the library's own logs, the same policy
# played two ways, masking checked from inside the distribution, and one claim on page 06 put to
# the test.
#
# **Environments:** `CartPole-v1`, and the toy race as a masked Gymnasium environment
# (`labs/labkit/racegym.py`). The notebook runs in about a minute and a half.
#
# Stuck? Run `python -m labs hint p9-06` in a terminal.

# %%
import math
import pathlib
import sys
import warnings

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import gymnasium as gym
import numpy as np
import torch as th
from sb3_contrib import MaskablePPO
from stable_baselines3 import PPO

import checks
from labs.labkit import predict
from labs.labkit.racegym import TinyRaceEnv

LAB = "p9-06"
th.set_num_threads(1)  # tiny networks run faster on one thread

# %% [markdown]
# ## Part A — the rollout arithmetic
#
# **TODO 1.** `rollout_numbers`: for one configuration, how many transitions each rollout holds,
# minibatches per epoch, gradient steps per update, how many updates `learn(total)` runs, and how
# many environment steps it actually takes. Two details page 06 does not spell out: the last
# minibatch of an epoch may be short (so minibatches round **up**), and `learn()` keeps collecting
# whole rollouts until it has **at least** `total` steps (so updates round up too).

# %%
def rollout_numbers(n_steps, n_envs, batch_size, n_epochs, total):
    # >>> SOLUTION: transitions = n_steps * n_envs; minibatches and updates round up with math.ceil
    transitions = n_steps * n_envs
    minibatches = math.ceil(transitions / batch_size)
    updates = math.ceil(total / transitions)
    return dict(transitions=transitions, minibatches=minibatches, gradient_steps=minibatches * n_epochs,
                updates=updates, steps_taken=updates * transitions)
    # <<< SOLUTION


print(rollout_numbers(256, 4, 64, 10, 2_000_000))
checks.arithmetic(rollout_numbers)

# %% [markdown]
# ## Part B — a short run, read through its logs
#
# About 30 seconds of PPO on CartPole. SB3 records what happened in the last update in
# `model.logger.name_to_value`.
#
# **TODO 2.** Pick out the four values the check asks for. Two of them come straight from page 04:
# `train/clip_fraction` (the share of samples whose ratio left [1 − ε, 1 + ε]) and `train/approx_kl`
# (an estimate of how far the update moved the policy).

# %%
model = PPO("MlpPolicy", "CartPole-v1", n_steps=512, batch_size=128, n_epochs=5, seed=0, verbose=0)
model.learn(10_000)

# >>> SOLUTION: a dict of the four keys from model.logger.name_to_value
values = {k: float(model.logger.name_to_value[k]) for k in ("train/clip_fraction", "train/approx_kl", "train/entropy_loss", "train/n_updates")}
# <<< SOLUTION
print(values)
checks.logs(values)

# %% [markdown]
# ## Part C — the same policy, played two ways
#
# `predict(obs, deterministic=True)` takes the most likely action; `False` samples from the
# policy's distribution, the way training does. Before running: how will sampled play compare?

# %%
CHOICES = {
    "same": "about the same score: it is the same policy",
    "lower": "clearly lower: sampling still takes the policy's unlikely actions",
    "higher": "higher: sampling explores",
}
my_prediction = "lower"  # >>> ANSWER
predict.commit(LAB, "sampled", my_prediction, CHOICES)

# %% [markdown]
# **TODO 3.** `play`: run `episodes` CartPole episodes with `model.predict` and return their total
# rewards. Seeds 1000, 1001, … so both modes face the same starts.

# %%
def play(model, deterministic, episodes=20):
    env = gym.make("CartPole-v1")
    totals = []
    for ep in range(episodes):
        obs, _ = env.reset(seed=1000 + ep)
        done, total = False, 0.0
        while not done:
            # >>> SOLUTION: action from model.predict(obs, deterministic=deterministic); step; add the reward
            action, _ = model.predict(obs, deterministic=deterministic)
            obs, reward, terminated, truncated, _ = env.step(action)
            total += reward
            done = terminated or truncated
            # <<< SOLUTION
        totals.append(total)
    return totals


det, sampled = play(model, True), play(model, False)
print(f"deterministic {np.mean(det):.0f} ± {np.std(det):.0f}    sampled {np.mean(sampled):.0f} ± {np.std(sampled):.0f}")
predict.reveal(LAB, "sampled", f"{np.mean(det):.0f} against {np.mean(sampled):.0f}", correct="lower")
checks.det_vs_sampled(det, sampled)

# %% [markdown]
# A policy trained for a few seconds is still quite uncertain, and sampling pays for every unlikely
# action it takes. This is page 10's point about evaluation modes (Finding D) seen on a policy that
# is random by construction: evaluate the way you mean to deploy, and evaluate every agent in a
# comparison the same way.

# %% [markdown]
# ## Part D — masking, from inside the distribution
#
# A short MaskablePPO run on the toy race. It is barely trained; that is fine, because the claim
# being checked is about the mechanism.
#
# **TODO 4.** First count how often a sampled action is illegal in 2,000 steps. Then read the
# log-probability the policy gives each action in the first state of a race.

# %%
race = MaskablePPO("MlpPolicy", TinyRaceEnv(), n_steps=256, batch_size=64, seed=0, verbose=0)
race.learn(2048)

env = TinyRaceEnv()
obs, _ = env.reset(seed=0)
bad = 0
for _ in range(2000):
    mask = env.action_masks()
    action, _ = race.predict(obs, action_masks=mask, deterministic=False)
    # >>> SOLUTION: count the step if mask[action] is False, then step and reset when done
    bad += int(not mask[action])
    obs, _, done, _, _ = env.step(action)
    if done:
        obs, _ = env.reset()
    # <<< SOLUTION

obs, _ = env.reset(seed=0)
mask = env.action_masks()
obs_tensor, _ = race.policy.obs_to_tensor(obs)
# >>> SOLUTION: the policy's distribution with the mask, then log_prob of each of the three actions
dist = race.policy.get_distribution(obs_tensor, action_masks=mask)
logp = dist.log_prob(th.arange(3)).detach().numpy()
# <<< SOLUTION
print("legal:", mask, "  log-probabilities:", logp)
checks.masking(bad, logp, mask)

# %% [markdown]
# On lap 1 the car is on compound A, so `PIT_A` is illegal, and its log-probability is −1e8: the
# library replaces masked logits with −1e8 *before* the softmax. Page 04's ratio uses these same
# log-probabilities, so an illegal action can never enter it.

# %% [markdown]
# ## Part E — what if `batch_size` does not divide the buffer?
#
# Page 06 says SB3 then "raises a configuration error rather than silently dropping leftover
# transitions". Test it: a buffer of 100 transitions and a `batch_size` of 64, once with `PPO` and
# once with `MaskablePPO`. Predict first.

# %%
CHOICES = {
    "error": "both raise an error, as page 06 says",
    "warn": "PPO warns, MaskablePPO says nothing; both use every transition",
    "drop": "both silently drop the 36 leftover transitions",
}
my_prediction = "warn"  # >>> ANSWER
predict.commit(LAB, "warn", my_prediction, CHOICES)

# %% [markdown]
# **TODO 5.** For each class, count the warnings about the mini-batch size while building the
# model, then after one `learn(100)` list the sizes of the minibatches its rollout buffer yields.

# %%
def batch_behaviour(cls, env):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model = cls("MlpPolicy", env, n_steps=100, batch_size=64, verbose=0, seed=0)
    model.learn(100)
    # >>> SOLUTION: count warnings mentioning "mini-batch"; list len(b.actions) for b in model.rollout_buffer.get(64)
    count = sum("mini-batch" in str(w.message) for w in caught)
    sizes = [len(b.actions) for b in model.rollout_buffer.get(64)]
    # <<< SOLUTION
    return count, sizes


w_ppo, s_ppo = batch_behaviour(PPO, "CartPole-v1")
w_mask, s_mask = batch_behaviour(MaskablePPO, TinyRaceEnv())
print(f"PPO: {w_ppo} warning(s), minibatches {s_ppo}    MaskablePPO: {w_mask} warning(s), minibatches {s_mask}")
predict.reveal(LAB, "warn", "PPO warned once, MaskablePPO said nothing, and both trained on 64 + 36", correct="warn")
checks.batch_truth(w_ppo, w_mask, s_ppo, s_mask)

# %% [markdown]
# Nothing is raised and nothing is dropped. The class this project uses says nothing at all, so a
# config comment like "must divide n_steps × n_envs" is a convention you have to keep yourself,
# not something the library enforces. Page 06 has been corrected to say so.
