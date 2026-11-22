"""Checks for lab p6-07. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import close, passed, require

LAB = "p6-07"


def updates(step_size_update, average_update):
    v, n = np.zeros(2), np.zeros(2)
    step_size_update(v, n, 1, 1.0, alpha=0.5)
    require(close(v[1], 0.5) and v[0] == 0, f"Half way from 0 toward +1 is 0.5, and only the chosen action moves. Got {v.tolist()}.")
    step_size_update(v, n, 1, -1.0, alpha=0.5)
    require(close(v[1], -0.25), "Then half way from 0.5 toward −1 is −0.25.")
    v, n = np.zeros(2), np.zeros(2)
    for r in (1.0, -1.0, 1.0, 1.0):
        average_update(v, n, 0, r)
    require(close(v[0], 0.5) and n[0] == 4, f"After rewards 1, −1, 1, 1 the sample average is 0.5 and the count 4. Got value {v[0]:.3f}, count {n[0]}.")
    require(n[1] == 0 and v[1] == 0, "The other action's value and count must not change.")
    passed(LAB, "update", "TODO 1 and 2: both updates behave.")


def settles(fixed_flips):
    require(len(fixed_flips) == 5, "Run the cell as given.")
    require(sum(fixed_flips) <= 5, f"Against the fixed script the greedy choice should stop changing; it flipped {fixed_flips} times.")
    passed(LAB, "A", "Part A: against a script, the values settle and the choice stops changing.")


def chases(adapting_flips):
    require(min(adapting_flips) >= 15, f"Against the adapting opponent the greedy choice should keep flipping (measured 50 to 100 times); got {adapting_flips}.")
    passed(LAB, "B", "Part B: against an opponent that adapts, the choice never settles.")


def tracking(table):
    fixed_avg, fixed_step = table[("fixed", "sample average")], table[("fixed", "step size 0.05")]
    require(fixed_avg < 0.05, f"Against the script the sample average should be nearly exact; error {fixed_avg:.3f}.")
    require(fixed_avg < fixed_step, "Against the script the sample average should beat the constant step size.")
    require(min(table[("adapting", "sample average")], table[("adapting", "step size 0.05")]) > 0.5, "Against the adapting opponent neither rule should get close.")
    passed(LAB, "C", "Part C: the textbook estimate is exact when the world holds still, and lost when it does not.")
