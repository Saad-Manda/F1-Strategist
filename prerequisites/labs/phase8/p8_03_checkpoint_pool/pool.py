"""Lab p8-03 · The checkpoint pool.

Page 03's sampling rule, built so that it works for every pool size, including the size the
real plan's pool has for its first 1,000 episodes: one.

THE RULE (the plan's CheckpointPool.sample). With n entries, cut = max(1, int(0.8 * n)).
The "recent" slice is entries[cut:], the "older" slice entries[:cut]. With probability
recency_bias, sample uniformly from the recent slice; otherwise uniformly from the older one.

Run the checks:  python -m labs check p8-03
"""

from __future__ import annotations

import numpy as np


class RecencyPool:
    def __init__(self, recency_bias: float = 0.7, max_size: int = 50, loader=None):
        self.recency_bias = recency_bias
        self.max_size = max_size
        self.entries: list = []
        self.loader = loader  # called as loader(name) to turn a stored name into an opponent
        self._cache: dict = {}

    def __len__(self) -> int:
        return len(self.entries)

    def add(self, name) -> None:
        """Append `name`. If the pool is now over max_size, drop the OLDEST entry (and its cached copy)."""
        # TODO: append; while too long, pop index 0 and forget it in the cache
        raise NotImplementedError("TODO p8-03: append; while too long, pop index 0 and forget it in the cache")

    def slices(self) -> tuple[list, list]:
        """(recent, older) under the plan's rule. With ONE entry, the plan's rule leaves the recent
        slice empty; then every sample must come from the one entry, so return ([], [entry])."""
        if not self.entries:
            raise ValueError("the pool is empty: add at least one entry first")
        # TODO: cut = max(1, int(0.8 * n)); recent = entries[cut:], older = entries[:cut]
        raise NotImplementedError("TODO p8-03: cut = max(1, int(0.8 * n)); recent = entries[cut:], older = entries[:cut]")

    def probabilities(self) -> np.ndarray:
        """The probability of sampling each entry, in the order of self.entries. Sums to 1.

        If the recent slice is empty, the older slice gets all of the probability: this is the
        one-line guard the plan is missing.
        """
        recent, older = self.slices()
        p = np.zeros(len(self.entries))
        # TODO: recency_bias / len(recent) on each recent entry, the rest on the older ones; guard the empty slice
        raise NotImplementedError("TODO p8-03: recency_bias / len(recent) on each recent entry, the rest on the older ones; guard the empty slice")

    def sample(self, rng: np.random.Generator):
        """One entry, drawn with probabilities(). Never raises for a non-empty pool."""
        # TODO: the plan's two-step rule, with the guard: if there is no recent slice, draw from older
        raise NotImplementedError("TODO p8-03: the plan's two-step rule, with the guard: if there is no recent slice, draw from older")

    def get(self, name):
        """The opponent for `name`, built by self.loader the FIRST time only (audit K: the plan
        reloads a .pt file for every opponent, every episode)."""
        # TODO: a dict cache keyed by name
        raise NotImplementedError("TODO p8-03: a dict cache keyed by name")
