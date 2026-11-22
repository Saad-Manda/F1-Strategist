"""Checks for lab p8-05. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import close, passed, require

LAB = "p8-05"


def part_a(modal_share, same_all_race, random_shares):
    require(close(modal_share([2, 2, 2, 5]), 0.75), "modal_share([2, 2, 2, 5]) is 3 / 4.")
    require(close(modal_share([0, 1, 2, 3, 4, 5]), 1 / 6), "Six different actions: 1 / 6.")
    require(same_all_race >= 18, f"Most untrained networks should pick one action on every lap (measured 23 of 30); got {same_all_race}.")
    require(np.median(random_shares) > 0.85, f"Over random observations the most common action should take most of them (measured median 0.95); got {np.median(random_shares):.2f}.")
    passed(LAB, "A", f"Part A: {same_all_race} of 30 untrained networks play one action for a whole race.")


def part_b(action_entropy, policies):
    require(close(action_entropy([3] * 50), 0.0), "A policy that always does the same thing has entropy 0.")
    require(close(action_entropy(list(range(6)) * 10), np.log(6)), "A uniform spread over 6 actions has entropy log 6.")
    require(close(action_entropy([0, 1]), np.log(2)), "Two actions, half each: log 2.")
    e = {k: float(np.median(v)) for k, v in policies.items()}
    untrained, rand = e["untrained, greedy (the plan's seed)"], e["uniformly random (epsilon = 1)"]
    require(untrained < 0.5, f"The untrained greedy networks should have little entropy (measured median 0.20); got {untrained:.2f}.")
    require(rand > 1.7, f"Uniformly random should be close to log 6 = 1.79; got {rand:.2f}.")
    passed(LAB, "B", f"Part B: entropy {untrained:.2f} for the plan's seed against {rand:.2f} for a random policy.")
