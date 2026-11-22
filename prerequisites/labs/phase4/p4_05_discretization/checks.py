"""Checks for lab p4-05. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import passed, require

LAB = "p4-05"


def grouping(group_of):
    require(group_of(1, 10) == 0 and group_of(100, 10) == 0, "With 10 groups, states 1 to 100 are bin 0.")
    require(group_of(101, 10) == 1, "With 10 groups, state 101 starts bin 1.")
    require(group_of(1000, 10) == 9, f"State 1000 belongs to the last bin, 9. Got {group_of(1000, 10)}.")
    require(group_of(500, 2) == 0 and group_of(501, 2) == 1, "With 2 groups the split is between states 500 and 501.")
    require([group_of(s, 1000) for s in (1, 2, 999, 1000)] == [0, 1, 998, 999], "With 1000 groups every state has its own bin.")
    for n in (2, 3, 7, 20, 50, 200):
        bins = [group_of(s, n) for s in range(1, 1001)]
        require(min(bins) == 0 and max(bins) == n - 1, f"With {n} groups the bins should run from 0 to {n - 1}; got {min(bins)} to {max(bins)}.")
        require(bins == sorted(bins), "Bins should never decrease as the state increases.")
    passed(LAB, "grouping", "TODO 1: every state lands in one of n equal-width bins.")


def learning(learn_values, rms_error):
    values = np.asarray(learn_values(20, 200, np.random.default_rng(0)))
    require(values.shape == (20,), f"learn_values should return one number per bin (20); got shape {values.shape}.")
    again = np.asarray(learn_values(20, 200, np.random.default_rng(0)))
    require(np.array_equal(values, again), "The same seed should give the same result: all randomness has to come from `rng`.")
    require(values[0] < -0.4 and values[-1] > 0.4, f"The leftmost bin should have learned a clearly negative value and the rightmost a clearly positive one. Got {values[0]:.2f} and {values[-1]:.2f}.")
    error = rms_error(values, 20)
    require(error < 0.12, f"With 20 bins and 200 walks the RMS error should be under 0.12; got {error:.3f}. Check the target at the end of a walk: it is the reward alone.")
    still = np.asarray(learn_values(20, 200, np.random.default_rng(0), alpha=0.0))
    require(np.all(still == 0.0), "With alpha = 0 nothing should be learned: alpha has to scale every update.")
    passed(LAB, "learning", "TODO 2: your learner recovers the walk's values to within 0.12 from 200 walks.")


def tradeoff(errors):
    require(set(errors) == {2, 20, 1000}, "Run the comparison cell as given.")
    require(errors[20] < errors[2] - 0.2, f"20 bins should beat 2 bins by a wide margin; got {errors[20]:.3f} against {errors[2]:.3f}.")
    require(errors[20] < errors[1000] - 0.2, f"20 bins should beat 1000 bins by a wide margin with only 200 walks; got {errors[20]:.3f} against {errors[1000]:.3f}.")
    passed(LAB, "C", "Part C: too few bins cannot represent the answer, and too many cannot be filled in time.")


def budget(table):
    require(table[200][20] < table[200][50], "With 200 walks, 20 bins should beat 50.")
    require(table[1000][50] < table[1000][20], "With 1000 walks, 50 bins should beat 20.")
    require(table[1000][200] < table[200][200], "200 bins should improve a great deal when given five times the experience.")
    passed(LAB, "D", "Part D: more experience moves the best resolution finer.")
