"""Checks for lab p6-02. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import close, passed, require

LAB = "p6-02"


def update_and_tiebreak(td_update, greedy):
    Q = np.zeros((4, 2))
    Q[2] = [1.0, 3.0]
    td_update(Q, 1, 1, -1.0, 2, False, 0.5, 1.0)
    require(close(Q[1, 1], 1.0), f"Target −1 + max(1, 3) = 2; half way from 0 is 1.0. Got {Q[1, 1]:.3f}.")
    td_update(Q, 1, 1, -1.0, 2, False, 0.5, 0.9)
    require(close(Q[1, 1], 0.5 * 1.0 + 0.5 * (-1 + 0.9 * 3)), "With γ = 0.9 the next state's best value is discounted.")
    Q2 = np.zeros((4, 2))
    Q2[3] = [50.0, 50.0]
    td_update(Q2, 2, 1, 1.0, 3, True, 0.5, 1.0)
    require(close(Q2[2, 1], 0.5), "When the step ends the episode the target is just r: nothing after the end counts.")
    require(Q2[2, 0] == 0 and Q2[3, 0] == 50.0, "Only Q[s, a] may change.")

    rng = np.random.default_rng(0)
    picks = [greedy(np.zeros(2), rng) for _ in range(2000)]
    share = np.mean(picks)
    require(0.45 < share < 0.55, f"With both values equal each action should be picked about half the time; action 1 was picked {share:.0%} of the time.")
    require(all(greedy(np.array([0.0, -1.0, 2.0]), rng) == 2 for _ in range(50)), "Without a tie, greedy must return the largest value's index.")
    passed(LAB, "update", "TODO 1 and 2: the update and the random tie-break behave.")


def growth(sizes, medians):
    ratio = [s / d for s, d in zip(medians["sparse"], medians["dense"])]
    require(sizes == [5, 10, 20, 40], "Run the cell as given.")
    require(ratio[-1] > 3.0, f"At n = 40 the sparse learner should need more than three times the steps (measured about 5); got {ratio[-1]:.1f}.")
    require(ratio[-1] > ratio[0] + 1.0, f"The ratio should grow with n: {ratio[0]:.1f} at n = 5, {ratio[-1]:.1f} at n = 40.")
    passed(LAB, "B", "Part B: the end-only reward costs more, and more as the corridor grows.")


def closed_form(loop_value, break_even):
    require(close(loop_value(1.0, 0.5, 1), 2.0), "1 + 0.5 + 0.25 + … = 2.")
    require(close(loop_value(2.0, 0.95, 4), 2.0 / (1 - 0.95**4)), "b / (1 − γ^period).")
    b = break_even(0.95)
    require(close(b, 1.854938, 1e-5), f"10 × (1 − 0.95⁴) = 1.855; got {b:.4f}.")
    require(close(loop_value(b, 0.95), 10.0), "At the break-even bonus the loop is worth exactly the goal.")
    passed(LAB, "loop", "TODO 3 and 4: the loop is worth b / (1 − γ⁴), and overtakes the goal at b ≈ 1.85.")


def farming(results):
    rate = {b: np.mean([r["finish_rate"] for r in runs]) for b, runs in results.items()}
    taken = {b: np.mean([r["bonuses"] for r in runs]) for b, runs in results.items()}
    require(rate[0.0] > 0.9, f"With no bonus the agent should learn to finish; finish rate {rate[0.0]:.2f}.")
    require(rate[1.0] > 0.9, f"Below the threshold the agent still finishes; finish rate at b = 1 was {rate[1.0]:.2f}.")
    require(rate[2.0] < 0.1 and taken[2.0] > 8, f"Above it, the agent should farm: finish rate {rate[2.0]:.2f}, {taken[2.0]:.1f} bonuses an episode.")
    passed(LAB, "C", "Part C: past the threshold the bonus is what the agent does instead of finishing.")
