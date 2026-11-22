"""Checks for lab p8-07. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import close, passed, require

LAB = "p8-07"


def part_a(delta_stat, p_value, shuffle_null):
    require(close(delta_stat([20, 21, 22, 23], [20, 25, 22, 19]), 0.5), "Two of four races have equal stop laps: 0.5.")
    require(close(p_value(0.5, [0.5] * 9), 1.0), "When every null value is as far out as the real one, p = 1.")
    require(close(p_value(1.0, [0.0, 0.1, -0.1, 0.05]), 1 / 5), "When no null value is as far out, p = 1 / (n + 1).")
    a = np.arange(200) % 7
    null, p = shuffle_null(a, a.copy(), 200, np.random.default_rng(0))
    require(len(null) == 200, "shuffle_null returns one statistic per shuffle.")
    require(p < 0.01, "Identical lists (every pair matches) must be far outside their shuffled null.")
    passed(LAB, "A", "Part A: the statistic, the p-value and the shuffle behave.")


def part_b(plain):
    require(plain["independent"] > 0.1, f"Independent stops should not be rejected; p = {plain['independent']:.3f}.")
    require(plain["reactive"] < 0.01, f"The reactive data should be rejected; p = {plain['reactive']:.3f}.")
    require(plain["shared_safety_car"] < 0.01, f"The plain shuffle should (wrongly) reject the shared-safety-car data (measured p = 0.002); got {plain['shared_safety_car']:.3f}.")
    passed(LAB, "B", "Part B: the plain shuffle rejects a shared cause as if it were a reaction.")


def part_c(strat):
    require(strat["shared_safety_car"] > 0.1, f"Shuffling within races that shared the same safety car should not reject (measured p = 0.67); got {strat['shared_safety_car']:.3f}.")
    require(strat["reactive"] < 0.01, f"…and should still catch the real reaction; got p = {strat['reactive']:.3f}.")
    require(strat["independent"] > 0.1, f"…and leave independent stops alone; got p = {strat['independent']:.3f}.")
    passed(LAB, "C", "Part C: the stratified shuffle separates a shared cause from a reaction.")


def part_d(p_mixed):
    require(p_mixed > 0.05, f"Independent draws from the equilibrium mixtures have no within-race link, so the shuffle should not reject; got p = {p_mixed:.3f}.")
    print("✓ Part D: a strategic shape with no in-race reaction is invisible to the shuffle.")
