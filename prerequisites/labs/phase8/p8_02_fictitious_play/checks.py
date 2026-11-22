"""Checks for lab p8-02. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit import games
from labs.labkit.checks import close, passed, require

LAB = "p8-02"


def part_a(best_response, exploitability):
    U = games.RPS
    require(best_response(U, np.array([1.0, 0, 0]), "row") == 1, "Against pure Rock, the row player's best response is Paper (index 1).")
    require(best_response(U, np.array([1.0, 0, 0]), "col") == 1, "Against a row player on pure Rock, the column player's best response is Paper too (index 1): it holds row to −1.")
    require(best_response(games.MATCHING_PENNIES, np.array([0.0, 1.0]), "row") == 1, "In matching pennies, against pure tails the row player should show tails.")
    half = np.array([0.5, 0.5])
    require(close(exploitability(games.MATCHING_PENNIES, half, half), 0.0), "50/50 against 50/50 is matching pennies' equilibrium: exploitability 0.")
    h = games.pure(2, 0)
    require(close(exploitability(games.MATCHING_PENNIES, h, h), 2.0),
            "At (H, H) row already gets +1 and cannot gain; column gets −1 and would get +1 by switching to T. Total: 0 + 2 = 2.")
    third = np.ones(3) / 3
    require(close(exploitability(games.RPS, third, third), 0.0), "1/3 each is RPS's equilibrium.")
    require(close(exploitability(games.DOMINATED, games.pure(2, 1), games.pure(2, 1)), 0.0), "(P, P) is the old R/P game's equilibrium.")
    passed(LAB, "A", "Part A: best responses and exploitability are right on all three games.")


def part_b(periods):
    require(periods["old R/P"] == 1, f"The old R/P game should settle (period 1); your loop repeats every {periods['old R/P']}.")
    require(periods["pennies"] == 2, f"Matching pennies should cycle with period 2; got {periods['pennies']}.")
    require(periods["RPS"] == 3, f"RPS should cycle with period 3; got {periods['RPS']}.")
    passed(LAB, "B", "Part B: the dominated game settles; pennies and RPS chase in cycles of 2 and 3.")


def part_c(results):
    r, c, tr = results["pennies"]
    require(np.allclose(r, 0.5, atol=0.01) and np.allclose(c, 0.5, atol=0.01), f"Matching pennies' averages should be within 0.01 of 50/50; got {np.round(r, 3)}, {np.round(c, 3)}.")
    require(tr[-1] < 0.01, f"…and their exploitability under 0.01 after 2,000 rounds (measured 0.001); got {tr[-1]:.4f}.")
    r, c, tr = results["RPS"]
    require(np.allclose(r, 1 / 3, atol=0.02) and np.allclose(c, 1 / 3, atol=0.02), f"RPS's averages should be within 0.02 of 1/3 each; got {np.round(r, 3)}, {np.round(c, 3)}.")
    require(tr[-1] < 0.05, f"…and their exploitability under 0.05 after 2,000 rounds (measured 0.02); got {tr[-1]:.4f}.")
    require(tr[-1] < tr[9] / 5, "Exploitability should fall a long way between round 10 and round 2,000.")
    passed(LAB, "C", "Part C: fictitious play's averages close in on the equilibrium.")
