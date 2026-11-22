"""Checks for lab p4-04. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import close, passed, require

LAB = "p4-04"


def update(sarsa_update):
    Q = np.zeros((4, 12, 4))
    s, s2 = (2, 3), (2, 4)
    Q[s][1] = -10.0
    Q[s2] = [-4.0, -6.0, -50.0, -8.0]

    sarsa_update(Q, s, 1, -1.0, s2, 2, False, 0.5)
    require(
        close(Q[s][1], -30.5),
        f"The next action is 2, whose value is -50. Target = -1 + (-50) = -51, so the cell moves from -10 to -10 + 0.5 * (-41) = -30.5. Got {Q[s][1]:.2f}. "
        "(-7.5 would mean the best next action was used, which is Q-learning.)",
    )

    Q[s][1] = -10.0
    sarsa_update(Q, s, 1, -1.0, s2, 0, False, 0.5)
    require(close(Q[s][1], -7.5), f"With next action 0 (value -4): target -5, cell moves to -7.5. Got {Q[s][1]:.2f}.")

    Q[s][1] = -10.0
    sarsa_update(Q, s, 1, -1.0, s2, 2, True, 0.5)
    require(close(Q[s][1], -5.5), f"When done is True nothing follows: target = -1, cell moves to -5.5. Got {Q[s][1]:.2f}.")

    untouched = Q.copy()
    untouched[s][1] = 0.0
    reference = np.zeros((4, 12, 4))
    reference[s2] = [-4.0, -6.0, -50.0, -8.0]
    require(np.array_equal(untouched, reference), "Only the cell Q[s][a] should change.")
    passed(LAB, "update", "TODO 1: your target uses the action actually taken next, and stops at the end of an episode.")


def compare(results):
    q, s = results["Q-learning"], results["SARSA"]
    require(q["edge_share"] > 0.6, f"Q-learning should be making most of its moves on the edge row; got {q['edge_share']:.0%}.")
    require(s["edge_share"] < 0.4, f"SARSA should be keeping away from the edge row; got {s['edge_share']:.0%}. Check that sarsa_update uses a2.")
    require(
        s["late_reward"] > q["late_reward"] + 12,
        f"While training at ε = 0.1, SARSA should collect clearly more reward per episode than Q-learning. Got {s['late_reward']:.1f} against {q['late_reward']:.1f}.",
    )
    passed(LAB, "B", "Part B: Q-learning walks the edge and pays for it while it explores; SARSA keeps its distance.")


def low_epsilon(gap_high, gap_low):
    require(gap_high > 12, f"At ε = 0.1 the gap should be large; got {gap_high:.1f}.")
    require(abs(gap_low) < 6, f"At ε = 0.01 the two should nearly agree; got a gap of {gap_low:.1f}.")
    passed(LAB, "C", "Part C: with almost no exploration, the two algorithms almost agree.")
