"""Checks for lab p35-04. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit.checks import passed, require

LAB = "p35-04"

OZ = np.array([[0.50, 0.25, 0.25], [0.50, 0.00, 0.50], [0.25, 0.25, 0.50]])

# page 04's three toy races: D = 0, P = 1, W = 2
PAGE_RACES = [[0, 0, 0, 1, 1, 0], [0, 0, 1, 2, 2, 1], [0, 1, 1, 0, 0, 0]]
PAGE_MATRIX = np.array([[0.625, 0.375, 0.0], [0.4, 0.4, 0.2], [0.0, 0.5, 0.5]])


def fit(fit_chain):
    got = np.asarray(fit_chain(PAGE_RACES, 3), dtype=float)
    require(got.shape == (3, 3), f"fit_chain should return an n_states × n_states array; got shape {got.shape}.")
    require(
        np.allclose(got, PAGE_MATRIX),
        f"Page 04's three races should give page 04's matrix.\nExpected:\n{PAGE_MATRIX}\nGot:\n{np.round(got, 3)}",
    )

    got = np.asarray(fit_chain([[0, 0], [1, 1]], 2), dtype=float)
    require(
        np.allclose(got, [[1.0, 0.0], [0.0, 1.0]]),
        "Two sequences, [0, 0] and [1, 1]: state 0 was only ever followed by 0, and 1 by 1. "
        f"Got {got.tolist()}. A nonzero 0 → 1 entry means the last day of one sequence was paired with the first day of the next.",
    )

    got = np.asarray(fit_chain([[0, 1, 0, 1]], 3), dtype=float)
    require(np.allclose(got.sum(axis=1), 1.0), f"Every row must sum to 1, including the row of a state that was never seen. Row sums: {got.sum(axis=1)}.")
    require(np.allclose(got[2], 1 / 3), f"State 2 never appears as a starting point, so its row should be uniform (1/3 each). Got {got[2]}.")
    require(np.allclose(got[0], [0, 1, 0]) and np.allclose(got[1], [1, 0, 0]), "The rows that were observed should still come from the counts.")

    got = np.asarray(fit_chain([[1]], 2), dtype=float)
    require(np.allclose(got, 0.5), "A single one-day sequence contains no transitions at all, so both rows fall back to uniform.")
    passed(LAB, "fit", "TODO 1: counting stays inside each sequence, rows are normalised, and an unseen state gets a uniform row.")


def sample(sample_trace, fit_chain):
    trace = sample_trace(OZ, 0, 12, np.random.default_rng(0))
    require(len(trace) == 12, f"A trace of length 12 was asked for; got {len(trace)} states.")
    require(trace[0] == 0, "The first state of the trace is the `start` it was given.")
    require(all(int(s) in (0, 1, 2) for s in trace), "Every entry should be a state number.")

    again = sample_trace(OZ, 0, 12, np.random.default_rng(0))
    require(list(trace) == list(again), "The same seed should give the same trace: all the randomness has to come from `rng`.")
    other = sample_trace(OZ, 0, 40, np.random.default_rng(1))
    require(list(other[:12]) != list(trace), "A different seed should give a different trace.")

    long = sample_trace(OZ, 0, 20_000, np.random.default_rng(2))
    pairs = set(zip(long[:-1], long[1:]))
    require((1, 1) not in pairs, "NICE followed by NICE has probability 0 in this chain, but it appears in your trace. Each draw should use the row of the CURRENT state.")
    refit = np.asarray(fit_chain([long], 3), dtype=float)
    worst = np.abs(refit - OZ).max()
    require(worst < 0.03, f"Fitting a matrix to 20,000 days of your sampling should give the true matrix back within 0.03; the worst entry is off by {worst:.3f}.")
    passed(LAB, "sample", "TODO 2: your traces follow the matrix, and fitting a long one recovers it.")


def compare(result):
    require(set(result) == {3, 300}, "Run the comparison cell as given.")
    require(result[3] > 0.15, f"With 3 short sequences the worst entry should be off by well over 0.15 on average; got {result[3]:.3f}.")
    require(result[300] < 0.05, f"With 300 sequences the worst entry should be within 0.05; got {result[300]:.3f}.")
    ratio = result[3] / result[300]
    require(5 < ratio < 25, f"A hundred times the data should shrink the error by about ten times; got a factor of {ratio:.1f}.")
    passed(LAB, "C", "Part C: a hundred times the data buys about ten times the accuracy.")
