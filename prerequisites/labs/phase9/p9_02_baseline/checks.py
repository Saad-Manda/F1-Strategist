"""Checks for lab p9-02. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import close, passed, require

LAB = "p9-02"


def same_mean_less_noise(stats):
    for theta, s in stats.items():
        diff = abs(s["mean_plain"] - s["mean_base"])
        se = np.hypot(s["se_plain"], s["se_base"])
        require(diff < 3 * se, f"At θ = {theta} the two means differ by {diff:.2f}, more than three standard errors ({3 * se:.2f}). "
                "A baseline that depends only on the state must not move the average.")
        require(s["std_base"] < 0.75 * s["std_plain"], f"At θ = {theta} the baseline should cut the spread by a quarter or more "
                f"(measured about 40%); got {s['std_plain']:.1f} → {s['std_base']:.1f}.")
    passed(LAB, "A", "Part A: same average, about 40% less spread.")


def exactly_zero(baseline_term, softmax, log_softmax_grad):
    rng = np.random.default_rng(3)
    worst = 0.0
    for _ in range(200):
        z = rng.normal(0, 3, size=int(rng.integers(2, 6)))
        b = float(rng.normal(0, 100))
        t = np.asarray(baseline_term(z, b, softmax, log_softmax_grad))
        require(t.shape == z.shape, "The baseline term is a vector, one entry per logit.")
        worst = max(worst, float(np.abs(t).max()))
    require(worst < 1e-9, f"Σ_a π(a) ∇log π(a) · b should be exactly zero; the largest entry was {worst:.2e}.")
    passed(LAB, "B", "Part B: the baseline's term sums to zero exactly, for any logits and any b.")


def learned_baseline(plain, base):
    p300, b300 = plain[:, 299], base[:, 299]
    require(b300.mean() >= p300.mean() - 0.1, f"At episode 300 the baseline run should be at least as good on average: {b300.mean():.2f} vs {p300.mean():.2f}.")
    require(b300.std() < 0.5 * p300.std(), f"…and much more consistent across seeds (measured spread 0.11 vs 0.66): got {b300.std():.2f} vs {p300.std():.2f}.")
    require(b300.min() > -12.6, f"Every baseline seed should be close to the best, −11.66, by episode 300; the worst was {b300.min():.2f}.")
    passed(LAB, "C", f"Part C: at the same step size, seed-to-seed spread {p300.std():.2f} without a baseline, {b300.std():.2f} with one.")


def offset_matters(final):
    require(abs(final[(0.0, False)].mean() - final[(0.0, True)].mean()) < 0.03,
            "At offset 0 the two runs should end almost level (measured 0.977 and 0.975).")
    require(final[(-10.0, False)].min() < 0.5, "At offset −10, at least one run without the baseline should lock onto the worse arm.")
    require(final[(-10.0, True)].min() > 0.9, f"With the baseline every run at offset −10 should end on the better arm; the worst was {final[(-10.0, True)].min():.3f}.")
    passed(LAB, "D", "Part D: centred rewards hide the baseline's value; offset rewards show it.")
