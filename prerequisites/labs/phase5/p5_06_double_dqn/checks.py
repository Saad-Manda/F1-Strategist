"""Checks for lab p5-06. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import passed, require

LAB = "p5-06"


def bias(best_value_estimates):
    rng = np.random.default_rng(1)
    single, double = best_value_estimates(3, 40_000, rng)
    require(abs(single - 5.75) < 0.03, f"With 3 actions the single estimator should average page 06's 5.75; got {single:.3f}. It is the largest of A's estimates in each trial.")
    require(abs(double - 5.0) < 0.03, f"The double estimator should average 5.00; got {double:.3f}. It is B's estimate at the action A rated highest, not B's own maximum.")
    single6, _ = best_value_estimates(6, 40_000, rng)
    require(abs(single6 - (6 - 2 * 0.5**6)) < 0.03, f"With 6 actions the single estimator should average about 5.97; got {single6:.3f}.")
    passed(LAB, "bias", "TODO 1: the single estimator runs high, the double estimator does not.")


def batch(double_targets, page):
    got = np.asarray(double_targets(**page), dtype=float)
    require(got.shape == (3,), f"One target per row: shape (3,). Got {got.shape}.")
    require(np.isclose(got[0], -47.0), f"Row 1: the online network chooses action 1, the target network scores it -42, so -5 - 42 = -47. Got {got[0]}. If you got -46, the target network did the choosing.")
    require(np.isclose(got[1], -37.0), f"Row 2: action 1 is illegal, so the online network's choice is action 0, scored -31: target -37. Got {got[1]}. If you got -26, the mask was not applied before the argmax.")
    require(np.isclose(got[2], -4.0), f"Row 3 is terminal: the target is the reward alone, -4. Got {got[2]}.")
    half = double_targets(np.array([1.0]), np.array([0.0]), np.array([[0.0, 2.0]]), np.array([[10.0, 4.0]]), np.array([[True, True]]), gamma=0.5)
    require(np.isclose(half[0], 3.0), "gamma multiplies the scored value: 1 + 0.5 × 4 = 3.")
    passed(LAB, "batch", "TODO 2: your targets match page 06's batch, mask and cut-off included.")


def double_update(double_q_update, fresh_table):
    rng = np.random.default_rng(0)
    learned_from = []
    for _ in range(400):
        tables = [fresh_table(), fresh_table()]
        tables[0]["B"][:] = [9.0, 1.0] + [0.0] * 8
        tables[1]["B"][:] = [2.0, 7.0] + [0.0] * 8
        double_q_update(tables, "A", 0, 0.0, "B", False, rng, alpha=1.0)
        a0, a1 = tables[0]["A"][0], tables[1]["A"][0]
        require((a0 == 0.0) != (a1 == 0.0), "Exactly one of the two tables should change on each update.")
        learned_from.append(0 if a1 == 0.0 else 1)
        if a1 == 0.0:
            require(np.isclose(a0, 2.0), f"When table 0 learns, it chooses action 0 (its own best, 9) and table 1 scores it: 2. Got {a0}.")
        else:
            require(np.isclose(a1, 1.0), f"When table 1 learns, it chooses action 1 (its own best, 7) and table 0 scores it: 1. Got {a1}.")
    share = np.mean(learned_from)
    require(0.4 < share < 0.6, f"A fair coin should pick each table about half the time; table 1 learned {share:.0%} of the time.")
    tables = [fresh_table(), fresh_table()]
    tables[0]["B"][:] = 50.0
    tables[1]["B"][:] = 50.0
    double_q_update(tables, "B", 3, -1.5, None, True, np.random.default_rng(0), alpha=1.0)
    require(np.isclose(tables[0]["B"][3] + tables[1]["B"][3], -1.5 + 50.0), "At the end of an episode the target is the reward alone.")
    passed(LAB, "double", "TODO 3: one table chooses, the other scores, and a coin decides which learns.")


def mdp(single, double):
    early = slice(10, 31)
    require(single[early].mean() > 0.6, f"Q-learning should go left most of the time in episodes 10-30; it went left {single[early].mean():.0%}.")
    require(double[early].mean() < single[early].mean() - 0.3, "Double Q-learning should go left far less often than Q-learning in episodes 10-30.")
    require(double[-50:].mean() < 0.12, f"By the end, Double Q-learning should be close to the best possible 5%; it goes left {double[-50:].mean():.0%}.")
    passed(LAB, "C", "Part C: the max's optimism drove Q-learning into the worse action; two estimators were fooled far less.")
