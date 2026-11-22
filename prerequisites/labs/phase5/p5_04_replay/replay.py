"""Lab p5-04: page 04's minimal replay buffer, and what it does to a batch.

A transition is a tuple (obs, action, reward, next_obs, done). The buffer does not look
inside it; it only stores, overwrites and hands back.

    Task 1   RingBuffer.push and __len__   fixed capacity; once full, the oldest is overwritten
    Task 2   RingBuffer.sample             a uniform random batch, drawn with the buffer's rng
    Task 3   lag_one_correlation           how alike neighbouring items in a batch are

Run the checks with:  python -m labs check p5-04
"""

import numpy as np

# ============================================================================ Tasks 1 and 2


class RingBuffer:
    """Fixed capacity. Slot `self.next_slot` is where the next push goes."""

    def __init__(self, capacity, seed=0):
        self.capacity = capacity
        self.slots = [None] * capacity
        self.next_slot = 0
        self.count = 0  # how many slots hold a transition, never more than capacity
        self.rng = np.random.default_rng(seed)

    def push(self, transition):
        """Store `transition` in slot next_slot, then move next_slot on by one, wrapping to 0 at the end.

        Once the buffer is full this overwrites the oldest stored transition, because the
        slot after the newest is always the oldest.
        """
        # TODO: write into self.slots[self.next_slot], advance next_slot modulo capacity, count up to capacity
        raise NotImplementedError("TODO p5-04: write into self.slots[self.next_slot], advance next_slot modulo capacity, count up to capacity")

    def __len__(self):
        # TODO: the number of stored transitions
        raise NotImplementedError("TODO p5-04: the number of stored transitions")

    def sample(self, n):
        """n transitions drawn uniformly, with replacement, from the ones stored. A list.

        Use self.rng.integers to pick the slot numbers. Only slots that hold a transition
        may be picked: before the buffer is full, that is slots 0 .. count - 1.
        """
        # TODO: n slot numbers from self.rng.integers(self.count, size=n), then those slots
        raise NotImplementedError("TODO p5-04: n slot numbers from self.rng.integers(self.count, size=n), then those slots")


# ============================================================================ Task 3


def lag_one_correlation(values):
    """Pearson correlation between each item and the next one: values[:-1] against values[1:].

    Close to 1: each item is nearly a copy of the one before it. Close to 0: knowing one item
    tells you nothing about the next. np.corrcoef(a, b)[0, 1] computes it.
    """
    # TODO: np.corrcoef of values[:-1] and values[1:], the off-diagonal entry, as a float
    raise NotImplementedError("TODO p5-04: np.corrcoef of values[:-1] and values[1:], the off-diagonal entry, as a float")


# ============================================================================ Given: a stream of race laps


LAPS = 20


def race_stream(races, seed=0):
    """Transitions from `races` toy races, in the order they were driven. Given.

    obs = (laps left / 20, tyre age / 20). Each race pits once, on a random lap.
    Action 0 is stay out, 1 is pit. Reward is minus a lap time that grows with tyre age.
    """
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(races):
        pit_lap, age = int(rng.integers(6, 15)), 1
        for lap in range(1, LAPS + 1):
            obs = ((LAPS - lap + 1) / LAPS, age / LAPS)
            action = 1 if lap == pit_lap else 0
            reward = -(10.0 + 0.05 * age + (4.0 if action else 0.0))
            age = 1 if action else age + 1
            next_obs = ((LAPS - lap) / LAPS, age / LAPS)
            out.append((obs, action, reward, next_obs, lap == LAPS))
    return out
