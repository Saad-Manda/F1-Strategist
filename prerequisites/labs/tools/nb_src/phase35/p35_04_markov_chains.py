# %% [markdown]
# # Lab p35-04 · Markov chains
#
# **Goes with:** Phase 3.5, page 04 — Markov chains · **Time:** about 20 minutes
#
# You will fit a transition matrix from observed sequences by counting, sample new sequences
# from a matrix, and then find out how much data the fit needs before it can be trusted.
#
# **Environment:** the Land of Oz weather chain, a classic from Kemeny and Snell's textbook.
# The Land of Oz never has two nice days in a row. After a nice day it rains or snows with
# equal chance. After rain or snow, there is an even chance of the same again tomorrow, and
# otherwise an equal chance of each of the other two.
#
# ```
#            to RAIN   to NICE   to SNOW
# from RAIN    0.50      0.25      0.25
# from NICE    0.50      0.00      0.50
# from SNOW    0.25      0.25      0.50
# ```
#
# Stuck? Run `python -m labs hint p35-04` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import numpy as np

import checks
from labs.labkit import predict

LAB = "p35-04"
RAIN, NICE, SNOW = 0, 1, 2
NAMES = ["RAIN", "NICE", "SNOW"]
TRUE_P = np.array(
    [
        [0.50, 0.25, 0.25],
        [0.50, 0.00, 0.50],
        [0.25, 0.25, 0.50],
    ]
)
print("each row sums to", TRUE_P.sum(axis=1))

# %% [markdown]
# ## Part A — fit a matrix by counting
#
# The page's estimator: count how often each transition `i → j` was seen, then divide each
# row of counts by its total.
#
# **TODO 1.** Implement `fit_chain`. `sequences` is a list of sequences, and each sequence is
# a list of state numbers, one per day. Two rules from the page:
#
# - only count pairs of consecutive days **within** one sequence, never the last day of one
#   sequence followed by the first day of the next;
# - a state that was never seen as a starting point has a row of zero counts. Give it a
#   **uniform** row (`1 / n_states` everywhere) so that every row still sums to 1.

# %%
def fit_chain(sequences, n_states):
    """Count-and-normalise estimate of a transition matrix. Returns an (n_states, n_states) array."""
    # >>> SOLUTION: tally consecutive pairs inside each sequence into a counts matrix, divide each row by its total, and use a uniform row where the total is zero
    counts = np.zeros((n_states, n_states))
    for sequence in sequences:
        for today, tomorrow in zip(sequence[:-1], sequence[1:]):
            counts[today, tomorrow] += 1
    fitted = np.full((n_states, n_states), 1.0 / n_states)
    for i in range(n_states):
        if counts[i].sum() > 0:
            fitted[i] = counts[i] / counts[i].sum()
    return fitted
    # <<< SOLUTION


checks.fit(fit_chain)

# %% [markdown]
# The first check used the page's own three races (`D D D P P D` and so on) and expected the
# page's own matrix back. Your function and the hand calculation are the same procedure.
#
# ## Part B — sample a sequence from a matrix
#
# **TODO 2.** Implement `sample_trace`: a list of `length` states. The first is `start`. Each
# later one is drawn at random using the row of `P` that belongs to the state before it:
# `rng.choice(n_states, p=P[current])` does one such draw.

# %%
def sample_trace(P, start, length, rng):
    """A sequence of `length` states starting at `start`, each drawn from the previous state's row of P."""
    # >>> SOLUTION: begin with [start]; repeatedly draw the next state with rng.choice using the current state's row, until the list has `length` entries
    trace = [start]
    while len(trace) < length:
        trace.append(int(rng.choice(len(P), p=P[trace[-1]])))
    return trace
    # <<< SOLUTION


for seed in (0, 1):
    trace = sample_trace(TRUE_P, RAIN, 12, np.random.default_rng(seed))
    print(f"seed {seed}:", " ".join(NAMES[s][0] for s in trace))
checks.sample(sample_trace, fit_chain)

# %% [markdown]
# Two seeds, the same starting day, and the sequences part ways within a few days. Look for
# `N N` in either line: it cannot appear, because that entry of the matrix is zero.
#
# The last check fitted a matrix to one very long sequence you sampled and got the true
# matrix back, near enough. Fitting and sampling are inverse operations when there is plenty
# of data.
#
# ## Part C — how much data is "plenty"?
#
# The real project fits one 3×3 weather matrix per circuit from a handful of historical
# races. So the practical question is what a fit from very little data looks like.
#
# We will fit the Oz chain from **3** sequences of 10 days, and from **300** sequences of 10
# days, and measure the largest error in any of the nine entries. Each case is repeated 200
# times and averaged, so the answer does not depend on one lucky draw.
#
# **TODO — predict before you run.** With 100 times as much data, the worst error is

# %%
CHOICES = {
    "same": "about the same size",
    "10x": "about 10 times smaller",
    "100x": "about 100 times smaller",
}
my_prediction = "10x"  # >>> ANSWER

predict.commit(LAB, "data", my_prediction, CHOICES)

# %%
def worst_error(n_sequences, rng, repeats=200):
    errors, impossible = [], 0
    for _ in range(repeats):
        sequences = [sample_trace(TRUE_P, int(rng.integers(3)), 10, rng) for _ in range(n_sequences)]
        fitted = fit_chain(sequences, 3)
        errors.append(np.abs(fitted - TRUE_P).max())
        impossible += bool(((fitted == 0) & (TRUE_P > 0)).any())
    return float(np.mean(errors)), impossible / repeats


rng = np.random.default_rng(0)
result = {}
for n in (3, 300):
    error, share = worst_error(n, rng)
    result[n] = error
    print(f"{n:>3} sequences: worst entry is off by {error:.3f} on average; "
          f"{share:.0%} of fits call something impossible that can in fact happen")

ratio = result[3] / result[300]
predict.reveal(LAB, "data", f"the worst error shrank by a factor of {ratio:.1f}", correct="10x")
checks.compare(result)

# %% [markdown]
# A hundred times the data bought about ten times the accuracy. Error in a counted
# proportion falls with the **square root** of the number of observations, so each extra
# decimal place of accuracy costs a hundred times more data.
#
# Now look at the 3-sequence line again. A worst error near 0.28 means an entry whose true
# value is 0.25 might be fitted as 0.5, or as 0. In about a quarter of those fits, some
# transition that really happens was never seen and so was given probability zero. A solver
# that is told a transition is impossible will plan as if it cannot happen.
#
# This is why the real `weather_markov.py` reports the counts behind every entry along with
# the matrix, and why the page says a thinly fitted Oracle B should be reported as such. The
# fitting code is three lines. Knowing whether to believe its output is the harder part.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
