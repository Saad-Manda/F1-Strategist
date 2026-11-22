# %% [markdown]
# # p9-cap report · Policy gradient on the toy race
#
# Given cells: nothing to write, about six minutes to run. Run it once your stages are green, or
# before, because it uses the reference learners in `labs/labkit/minipg.py`, not your file.
# Every number is an exact gap to the optimum (224.49 s), not a sampled race time.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np
import torch as th

from labs.labkit import minipg
from labs.labkit.racegym import TinyRaceEnv, gap_of_sb3

th.set_num_threads(1)

# %% [markdown]
# ## 1 · Four learners, one ladder (about 80 s)
#
# Pages 01 to 04 in order: REINFORCE, then a critic, then GAE with batches, epochs and the clip;
# and the same PPO without the clip. 2,000 races each, two seeds. The second plot is each learner's
# average policy entropy per race: how random its choices still are.

# %%
runs = {kind: [minipg.train(kind, 2000, seed) for seed in (0, 1)] for kind in ("reinforce", "ac", "ppo", "noclip")}
for kind, rs in runs.items():
    print(f"{kind:9s}  gaps {[round(minipg.gap(r.theta), 2) for r in rs]} s")

fig, ax = plt.subplots(1, 2, figsize=(11, 3.5))
for kind, rs in runs.items():
    ax[0].plot(np.convolve(rs[0].times, np.ones(50) / 50, mode="valid"), label=kind)
    ax[1].plot(rs[0].entropy, label=kind, lw=0.8)
ax[0].axhline(224.49, color="k", ls="--", lw=1); ax[0].set_ylim(222, 270)
ax[0].set_xlabel("race"); ax[0].set_ylabel("race time, 50-race mean (seed 0)")
ax[1].set_xlabel("race"); ax[1].set_ylabel("mean policy entropy per race"); ax[1].legend(); plt.show()

# %% [markdown]
# REINFORCE and the plain actor-critic **stall** well short of PPO, and more races do not rescue
# them: at 5,000 races, seeds 0 to 2, the build measured 8.3 / 8.2 / 3.5 s for REINFORCE and
# 7.2 / 9.4 / 9.2 for the actor-critic, against 1.93 s for PPO at 2,000. PPO without the clip is
# about as good as PPO here, at four epochs per batch; the clip only earns its keep when each batch
# is reused harder (section 2, and stage 7). The entropy plot shows why the first two stall. Their choices stop being random before the good pit
# lap has been found, and a policy that never tries a lap again cannot learn that it was good.
#
# The obvious fix is an entropy bonus, the `ent_coef` of page 10. On this race it does not reliably
# work. Measured at 5,000 races, three seeds: `ent_coef` 0.05 gave 3.4 / 1.7 / 8.3 s, 0.2 gave
# 8.8 / 6.1 / 7.5, 1.0 gave 9.6 / 0.9 / 3.0, and entropy still collapsed. What does work is what PPO
# adds: batches, standardised advantages, and several careful passes over each batch.

# %% [markdown]
# ## 2 · How far past the clip do ratios go? (about 15 s)
#
# Page 04 says the clip keeps the ratio within [0.8, 1.2]. Here is the largest ratio seen in each
# update of a PPO run with ten epochs per batch.

# %%
ten = minipg.train("ppo", 1000, 0, epochs=10)
plt.plot(ten.max_ratio, ".", ms=3); plt.axhline(1.2, color="r", lw=1, label="1 + ε")
plt.yscale("log"); plt.xlabel("update"); plt.ylabel("largest ratio in the update"); plt.legend(); plt.show()
print(f"updates whose largest ratio passed 1.2: {np.mean(np.array(ten.max_ratio) > 1.2):.0%};  the largest: {max(ten.max_ratio):.2f}")
print(f"gap after 1,000 races at ten epochs: {minipg.gap(ten.theta):.2f} s")

# %% [markdown]
# The clip removes the *incentive* to push a ratio further, not the possibility. A step is taken
# while the ratio is still inside the band and can land well outside it, as stage 5 showed (1 → 4.95).
# What the clip guarantees is that the objective stops rewarding the push, so later steps leave that
# sample alone. That was enough, here, for ten epochs per batch to be safe (stage 7: 1.7 s with the
# clip, 7.2 s without). SB3 logs `train/clip_fraction` and `train/approx_kl` so you can see how often
# it happens, and its `target_kl` option stops an update early when the policy has moved too far.

# %% [markdown]
# ## 3 · The library on the same race (about three minutes, one run per cell)
#
# `MaskablePPO` on `TinyRaceEnv` for 20,000 steps (1,000 races), a small network, γ = 1. Its gap is
# measured exactly by asking the trained model for its action in every state. First with the
# reward centred (each lap −(lap time − 10)), as everything above.

# %%
from sb3_contrib import MaskablePPO  # noqa: E402

kwargs = dict(n_steps=400, batch_size=100, n_epochs=10, gamma=1.0, ent_coef=0.01, seed=0, verbose=0, policy_kwargs=dict(net_arch=[32, 32]))
centred = MaskablePPO("MlpPolicy", TinyRaceEnv(offset=10.0), **kwargs)
centred.learn(20_000)
print(f"MaskablePPO, centred reward: gap {gap_of_sb3(centred):.2f} s")

# %% [markdown]
# Then with the raw reward, −lap time, about −11 per lap and −225 over a race: the situation of
# audit finding J3, and of p9-02 part D.

# %%
raw = MaskablePPO("MlpPolicy", TinyRaceEnv(offset=0.0), **kwargs)
raw.learn(20_000)
print(f"MaskablePPO, raw reward: gap {gap_of_sb3(raw):.2f} s")

# %% [markdown]
# Measured in the build, seeds 0 to 2: **0.00 s** centred on every seed, and **38.48 s** uncentred on
# every seed, at 20,000 and at 60,000 steps. 38.48 s is the gap of a network that has learned
# nothing (the p5-cap log gives 38.5 s untrained). With γ = 1 the value head has to fit returns near
# −225 from a start near 0, and the policy's advantages are dominated by that error for the whole
# run. For the real race, with laps near −90 s over 52 laps, the targets are about −4,700. Centring
# (Finding C) is not an optimisation here; it is the difference between learning and not.

# %% [markdown]
# ## 4 · One ruler, five learners
#
# The same quiet toy race, the same exact ruler, across the capstones. Earlier rows are quoted from
# the labs plan's build log, not retrained here.

# %%
rows = [
    ("DP optimum (p35-cap)", "exact", "0.00"),
    ("table Q-learner, centred (p4-cap)", "5,000 races, 3 seeds", "2.2 mean"),
    ("network DQN learner (p5-cap)", "600 races, 2 seeds", "0.00 to 4.3"),
    ("mini PPO, this capstone", "2,000 races, 2 seeds", ", ".join(f"{minipg.gap(r.theta):.2f}" for r in runs["ppo"])),
    ("MaskablePPO, centred (this report)", "1,000 races", f"{gap_of_sb3(centred):.2f}"),
]
print(f"{'learner':40s} {'budget':24s} gap to the optimum, s")
for name, budget, g in rows:
    print(f"{name:40s} {budget:24s} {g}")

# %% [markdown]
# The library learner, with a neural network and every detail page 05 lists, finds the exact optimum
# in 1,000 races. The mini PPO, a table with the same core ideas and none of the polish, stops at a
# near-miss of about 1.8 s. The optimum is one stop, onto B on lap 8; the mini PPO's greedy plan
# (measured, seeds 0 to 2) adds an unnecessary second stop back onto A on lap 13 or 14, the same kind
# of near-miss the p5-cap network learner made. That gap, between "the
# algorithm in the paper" and "the algorithm that works", is page 05's argument for buying.
