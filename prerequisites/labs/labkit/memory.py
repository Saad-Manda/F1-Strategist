"""Reference replay memories, for the labs that use one without building it.

Labs p5-04 and p5-07 have you build these yourself. Later labs import these copies instead,
so that an unfinished earlier lab never blocks a later one.

Both memories have the same interface:
    push(item)                      store one transition
    sample(n) -> (items, indices, weights)
    update_priorities(indices, td_errors)
    len(memory)

Everything here is given, complete code. Labs import it; nothing in this file is a TODO.
"""

from __future__ import annotations

import numpy as np


class UniformMemory:
    """Page 04's ring buffer: fixed capacity, oldest overwritten first, uniform sampling."""

    def __init__(self, capacity: int, seed: int = 0):
        self.capacity = capacity
        self.items: list = [None] * capacity
        self.next_slot, self.count = 0, 0
        self.rng = np.random.default_rng(seed)

    def push(self, item) -> None:
        self.items[self.next_slot] = item
        self.next_slot = (self.next_slot + 1) % self.capacity
        self.count = min(self.count + 1, self.capacity)

    def sample(self, n: int):
        idx = self.rng.integers(self.count, size=n)
        return [self.items[i] for i in idx], idx, np.ones(n)

    def update_priorities(self, indices, td_errors) -> None:
        """A uniform memory has no priorities to update."""

    def __len__(self) -> int:
        return self.count


class PriorityMemory(UniformMemory):
    """Page 07's proportional prioritized replay on a flat sum tree, with new items at the current maximum."""

    def __init__(self, capacity: int, alpha: float = 0.6, beta: float = 0.4, seed: int = 0):
        super().__init__(capacity, seed)
        self.alpha, self.beta = alpha, beta
        self.nodes = np.zeros(2 * capacity - 1)

    def _set(self, i: int, value: float) -> None:
        k = i + self.capacity - 1
        change = value - self.nodes[k]
        self.nodes[k] = value
        while k > 0:
            k = (k - 1) // 2
            self.nodes[k] += change

    def _find(self, mass: float) -> int:
        k = 0
        while k < self.capacity - 1:
            left = 2 * k + 1
            if mass <= self.nodes[left]:
                k = left
            else:
                mass -= self.nodes[left]
                k = left + 1
        return k - (self.capacity - 1)

    def push(self, item) -> None:
        top = float(self.nodes[self.capacity - 1 :].max())
        self._set(self.next_slot, top if top > 0 else 1.0)
        super().push(item)

    def sample(self, n: int):
        total = self.nodes[0]
        edges = np.linspace(0.0, total, n + 1)
        idx = np.array([self._find(self.rng.uniform(edges[j], edges[j + 1])) for j in range(n)])
        idx = np.minimum(idx, self.count - 1)
        probs = self.nodes[idx + self.capacity - 1] / total
        weights = (self.count * probs) ** (-self.beta)
        return [self.items[i] for i in idx], idx, weights / weights.max()

    def update_priorities(self, indices, td_errors) -> None:
        for i, e in zip(indices, td_errors):
            self._set(int(i), (abs(float(e)) + 1e-6) ** self.alpha)
