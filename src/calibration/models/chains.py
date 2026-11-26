"""Markov chains counted from per-lap labels."""

from collections.abc import Iterable

import pandas as pd

from src.common.errors import CalibrationError


def count_steps(
    sequences: Iterable[pd.Series], states: tuple[str, ...]
) -> tuple[pd.Series, pd.DataFrame]:
    """State of lap 1, and steps from lap to lap. Labels outside `states` break the chain."""
    start = pd.Series(0, index=states)
    counts = pd.DataFrame(0, index=states, columns=states)
    for sequence in sequences:
        labels = sequence.tolist()
        if labels and labels[0] in states:
            start[labels[0]] += 1
        for now, then in zip(labels, labels[1:]):
            if now in states and then in states:
                counts.loc[now, then] += 1
    return start, counts


def shares(counts: pd.Series) -> dict[str, float]:
    """Counts as probabilities; a state never seen has none."""
    if counts.sum() == 0:
        raise CalibrationError(f"'{counts.name or 'start'}' was never seen, so its chances are unknown")
    return (counts / counts.sum()).to_dict()
