"""Checks for lab p9-08. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import close, passed, require

LAB = "p9-08"


def readers(gap_at, window_mean):
    curve = [(100, 9.0), (200, 4.0), (300, 6.0), (400, 1.0)]
    require(gap_at(curve, 300) == 6.0 and gap_at(curve, 350) == 6.0, "gap_at: the last checkpoint at or before the budget.")
    require(gap_at(curve, 10_000) == 1.0, "Past the end of a curve, its last checkpoint.")
    require(close(window_mean(curve, 200, 400), (4 + 6 + 1) / 3), "window_mean: both ends included.")
    passed(LAB, "read", "TODO 1 and 2: reading a curve at a budget, and over a window.")


def margins(unfair, matched):
    require(unfair > 10, f"At 40,000 steps against 5,000 the PPO learner should look far ahead (measured about 24 s); got {unfair:.1f} s.")
    require(0 < matched < unfair / 2, f"At matched experience the margin should shrink to well under half (measured about 6 s against 24); got {matched:.1f} against {unfair:.1f}.")
    passed(LAB, "B", f"Part B: {unfair:.1f} s apart at unmatched budgets, {matched:.1f} s at matched ones.")


def single_checkpoints(spread):
    require(max(spread) > 5, f"Within the window, one seed's single checkpoints should differ by more than 5 s (measured up to 28); got at most {max(spread):.1f} s.")
    passed(LAB, "C", "Part C: one final checkpoint of a noisy learner is a sample, not a summary.")
