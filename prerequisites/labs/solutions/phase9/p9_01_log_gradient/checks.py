"""Checks for lab p9-01. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit import corridor
from labs.labkit.checks import close, passed, require

LAB = "p9-01"


def gradient(softmax, log_softmax_grad):
    p = softmax(np.array([0.5, 0.0, -1.0]))
    require(close(p.sum(), 1.0, 1e-12), "Probabilities must sum to 1.")
    require(np.allclose(p, [0.5465, 0.3315, 0.1220], atol=1e-4), f"softmax(0.5, 0, −1) should be (0.5465, 0.3315, 0.1220); got {np.round(p, 4)}.")
    require(np.all(np.isfinite(softmax(np.array([1000.0, 0.0])))), "softmax overflowed on a logit of 1000: subtract the largest logit first.")
    rng = np.random.default_rng(1)
    for _ in range(20):
        z = rng.normal(0, 2, size=4)
        a = int(rng.integers(4))
        g = log_softmax_grad(z, a)
        num = np.empty(4)
        for j in range(4):
            e = np.zeros(4)
            e[j] = 1e-6
            num[j] = (np.log(softmax(z + e)[a]) - np.log(softmax(z - e)[a])) / 2e-6
        require(np.allclose(g, num, atol=1e-6), f"Your gradient {np.round(g, 4)} disagrees with finite differences {np.round(num, 4)} for logits {np.round(z, 2)}, action {a}.")
        require(abs(g.sum()) < 1e-9, "The gradient's components should sum to 0: adding the same number to every logit changes no probability.")
    passed(LAB, "grad", "TODO 1 and 2: softmax and its log-gradient agree with finite differences.")


def reinforce_works(values):
    final = values[:, -1]
    require(values.shape == (20, 1000), "Run the cell as given: 20 seeds, 1,000 episodes.")
    require(values[:, 0].mean() < -18, "The learner starts out preferring left (θ = −1.5, start value −24.4).")
    require(final.mean() > -13.5, f"After 1,000 episodes the start value should average above −13.5 (measured −12.1); got {final.mean():.2f}.")
    require(final.mean() < -11.6, "No policy can beat −11.66 here: check the sign of your update.")
    passed(LAB, "reinforce", f"TODO 3: REINFORCE climbs from −24.4 to {final.mean():.2f}; the best possible is −11.66.")


def fixed_policies(always_right, always_left, best):
    require(always_right == -corridor.STEP_CAP and always_left == -corridor.STEP_CAP,
            "Both fixed policies should hit the step cap: always-right bounces between cells 0 and 1, always-left never leaves cell 0.")
    require(close(best[0], 0.586, 1e-3) and close(best[1], -11.657, 1e-3), "The best probability of pressing right is 0.586, worth −11.66.")
    passed(LAB, "C", "Part C: every fixed action loops; only a stochastic policy reaches the goal.")
