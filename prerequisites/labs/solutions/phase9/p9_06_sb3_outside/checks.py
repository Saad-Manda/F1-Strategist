"""Checks for lab p9-06. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import passed, require

LAB = "p9-06"


def arithmetic(rollout_numbers):
    plan = rollout_numbers(n_steps=256, n_envs=4, batch_size=64, n_epochs=10, total=2_000_000)
    require(plan["transitions"] == 1024, "The real config collects 256 steps in each of 4 environments: 1,024 transitions per update.")
    require(plan["minibatches"] == 16 and plan["gradient_steps"] == 160, "1,024 / 64 = 16 minibatches per epoch, 10 epochs: 160 gradient steps per update.")
    require(plan["updates"] == 1954, f"2,000,000 / 1,024 = 1,953.1, and learn() keeps going until it has at least 2M steps: 1,954 updates. Got {plan['updates']}.")
    require(plan["steps_taken"] == 2_000_896, "So it actually takes 1,954 × 1,024 = 2,000,896 steps.")
    single = rollout_numbers(n_steps=2048, n_envs=1, batch_size=64, n_epochs=10, total=2_000_000)
    require((single["minibatches"], single["updates"]) == (32, 977), "SB3's defaults (2,048 steps, one environment): 32 minibatches, 977 updates.")
    odd = rollout_numbers(n_steps=256, n_envs=4, batch_size=96, n_epochs=10, total=2_000_000)
    require(odd["minibatches"] == 11, f"1,024 / 96 = 10.7: ten full minibatches and one of 64, so 11. Got {odd['minibatches']}.")
    passed(LAB, "A", "Part A: 1,024 transitions, 160 gradient steps, 1,954 updates, and 2,000,896 steps for a budget of 2M.")


def logs(values):
    for key in ("train/clip_fraction", "train/approx_kl", "train/entropy_loss", "train/n_updates"):
        require(key in values, f"{key} is missing: read model.logger.name_to_value after learn().")
    require(0.0 <= values["train/clip_fraction"] <= 1.0, "clip_fraction is the share of samples whose ratio left [1 − ε, 1 + ε]: a number between 0 and 1.")
    require(values["train/n_updates"] > 0, "n_updates counts gradient steps so far.")
    passed(LAB, "B", f"Part B: clip_fraction {values['train/clip_fraction']:.3f}, approx_kl {values['train/approx_kl']:.4f} after the last update.")


def det_vs_sampled(det, sampled):
    require(len(det) == 20 and len(sampled) == 20, "Play 20 episodes each, as the cell does.")
    require(np.mean(det) > np.mean(sampled) + 50, f"Deterministic play should score well above sampled play here (measured about 375 vs 134); got {np.mean(det):.0f} vs {np.mean(sampled):.0f}.")
    passed(LAB, "C", f"Part C: the same policy scores {np.mean(det):.0f} played deterministically and {np.mean(sampled):.0f} sampled.")


def masking(bad, logp, mask):
    require(bad == 0, f"{bad} masked actions were chosen in 2,000 sampled steps: MaskablePPO must never pick one.")
    require(np.all(logp[~mask] < -1e6), f"A masked action's log-probability should be about −1e8 (the library sets its logit there); got {logp[~mask]}.")
    require(np.isclose(np.exp(logp[mask]).sum(), 1.0, atol=1e-5), "The legal actions' probabilities must sum to 1 on their own.")
    passed(LAB, "D", "Part D: masked actions get a logit of −1e8 before the softmax, so they are never sampled and the ratio never sees them.")


def batch_truth(warnings_ppo, warnings_maskable, sizes_ppo, sizes_maskable):
    require(warnings_ppo == 1 and warnings_maskable == 0, f"PPO should warn once and MaskablePPO not at all; got {warnings_ppo} and {warnings_maskable}.")
    require(sizes_ppo == [64, 36] and sizes_maskable == [64, 36], "Both train on a full minibatch of 64 and a short one of 36: nothing is dropped.")
    passed(LAB, "E", "Part E: no error from either class, one warning from PPO, silence from MaskablePPO, and a short last minibatch in both.")
