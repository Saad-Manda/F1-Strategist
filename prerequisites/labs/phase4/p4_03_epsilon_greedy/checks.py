"""Checks for lab p4-03. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import LabTodo, close, passed, require

LAB = "p4-03"


def selection(choose):
    q = np.array([1.0, 9.0, 3.0, 2.0])
    legal = np.array([True, False, True, True])
    rng = np.random.default_rng(0)

    picks = [choose(q, legal, 0.0, rng) for _ in range(200)]
    require(all(p == 2 for p in picks), f"With epsilon = 0 the choice should always be the best LEGAL action (index 2, value 3.0). Got {sorted(set(picks))}. Action 1 has the highest q but is illegal.")

    picks = [choose(q, legal, 1.0, rng) for _ in range(3000)]
    require(1 not in picks, "With epsilon = 1 every choice is an exploration, and exploration must stay inside the legal actions. The illegal action 1 was returned.")
    shares = [picks.count(a) / len(picks) for a in (0, 2, 3)]
    require(all(abs(s - 1 / 3) < 0.04 for s in shares), f"Exploration should pick each legal action equally often (about a third each). Got shares {np.round(shares, 3)}.")

    picks = [choose(q, legal, 0.3, rng) for _ in range(6000)]
    share_best = picks.count(2) / len(picks)
    require(abs(share_best - 0.8) < 0.03, f"With epsilon = 0.3 and three legal actions, the best one should be chosen 0.7 + 0.3/3 = 80% of the time. Got {share_best:.1%}.")

    a = [choose(q, legal, 0.5, np.random.default_rng(7)) for _ in range(1)]
    b = [choose(q, legal, 0.5, np.random.default_rng(7)) for _ in range(1)]
    require(a == b, "All randomness should come from the `rng` that was passed in.")
    require(isinstance(choose(q, legal, 0.0, rng), int), "Return a plain Python int.")
    passed(LAB, "selection", "TODO 1: exploration and exploitation both stay inside the legal actions.")


def schedule(linear_epsilon):
    require(close(linear_epsilon(0, 1.0, 0.05, 500_000), 1.0), "At step 0 epsilon is its starting value.")
    require(close(linear_epsilon(1, 1.0, 0.05, 500_000), 1.0 - 1.9e-6, 1e-12), "Each step lowers epsilon by (start - end) / decay_steps, which is 1.9e-6 for the plan's numbers.")
    require(close(linear_epsilon(250_000, 1.0, 0.05, 500_000), 0.525), "Halfway through the decay, epsilon is halfway between start and end: 0.525.")
    require(close(linear_epsilon(500_000, 1.0, 0.05, 500_000), 0.05), "At decay_steps epsilon has reached its floor.")
    require(close(linear_epsilon(900_000, 1.0, 0.05, 500_000), 0.05), "After decay_steps epsilon stays at the floor. It must not keep falling.")
    passed(LAB, "schedule", "TODO 2: the schedule falls in a straight line and stops at the floor.")


def floor(races, linear_epsilon):
    if races is None:
        raise LabTodo(f"TODO {LAB}: set races_until_floor")
    require(9600 <= races <= 9620, f"{races} is not it. The floor is reached after decay_steps steps, and each race is 52 steps.")
    require(linear_epsilon(52 * 9616, 1.0, 0.05, 500_000) == 0.05, "Your schedule should be at the floor by then.")
    passed(LAB, "floor", "TODO 3: 500,000 / 52 ≈ 9,615 races, of a run of 10,000.")


def sweep(results):
    require(set(results) == {1, 300, 3000}, "Run the sweep cell as given.")
    require(results[300] > results[1] + 0.2, f"Exploring first should beat greedy-from-the-start by a wide margin; got {results[300]:.2f} against {results[1]:.2f}.")
    require(results[300] > results[3000] + 0.2, f"Settling down should beat exploring to the end by a wide margin; got {results[300]:.2f} against {results[3000]:.2f}.")
    passed(LAB, "C", "Part C: too little exploration and too much both lose to a schedule that explores, then settles.")


def discovery(masked, unmasked):
    require(abs(masked - 0.983) < 0.02, f"Masked exploration should find the useful action in about 98.3% of trials; got {masked:.3f}.")
    require(abs(unmasked - 0.838) < 0.03, f"Unmasked exploration should find it in about 83.8% of trials; got {unmasked:.3f}.")
    passed(LAB, "D", "Part D: your function reproduces the page's 0.983 and 0.838.")
