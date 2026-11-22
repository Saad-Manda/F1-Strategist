"""Checks for lab p8-01. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import close, passed, require

LAB = "p8-01"


def update_and_choose(update, choose):
    q = np.zeros(2)
    update(q, 1, 1.0, 0.1)
    require(close(q[1], 0.1) and q[0] == 0.0, "From Q = (0, 0), one update of action 1 towards reward 1 at α = 0.1 gives Q = (0, 0.1).")
    update(q, 1, 1.0, 0.5)
    require(close(q[1], 0.55), "Then at α = 0.5: 0.1 + 0.5 × (1 − 0.1) = 0.55.")
    rng = np.random.default_rng(0)
    picks = [choose(np.array([0.0, 1.0]), 0.0, rng) for _ in range(200)]
    require(set(picks) == {1}, "With ε = 0, choose must always return the action with the larger Q.")
    ties = [choose(np.array([0.5, 0.5]), 0.0, rng) for _ in range(400)]
    require(0.35 < np.mean(ties) < 0.65, "On a tie, pick at random, not always the first action.")
    explore = [choose(np.array([0.0, 1.0]), 1.0, rng) for _ in range(400)]
    require(0.35 < np.mean(explore) < 0.65, "With ε = 1, every action is equally likely.")
    passed(LAB, "A", "Part A: the update and the ε-greedy choice behave.")


def keeps_moving(flips):
    require(min(flips) > 50, f"Both greedy actions should keep changing for the whole run (well over 50 switches each); got {flips}.")
    print("✓ Neither learner settles.")


def stale_replay(replayed, fresh, true_q):
    e_old = float(np.abs(replayed - true_q).mean())
    e_new = float(np.abs(fresh - true_q).mean())
    require(e_new < 0.3, f"Fitted on the new rounds only, Q should be close to (−0.6, +0.6); its error is {e_new:.2f}.")
    require(e_old > 4 * e_new, f"Fitted on the whole buffer, the error should be several times larger (measured about 8×): {e_old:.2f} vs {e_new:.2f}.")
    require(int(np.argmax(replayed)) == 0, "The whole-buffer learner should prefer H, the reply to the OLD opponent.")
    passed(LAB, "B", f"Part B: replaying the old game gives error {e_old:.2f}, against {e_new:.2f} on the new rounds only.")
