"""Checks for lab p5-04. Given code: nothing to edit here."""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import replay  # noqa: E402

# ---------------------------------------------------------------- task 1: storing


def test_push_and_length():
    buf = replay.RingBuffer(5)
    assert len(buf) == 0, "A new buffer holds nothing."
    for i in range(3):
        buf.push(("t", i))
    assert len(buf) == 3, f"After 3 pushes into a buffer of 5, len should be 3; got {len(buf)}."
    assert buf.slots[:3] == [("t", 0), ("t", 1), ("t", 2)], "Pushes fill the slots in order from slot 0."


def test_length_stops_at_capacity():
    buf = replay.RingBuffer(5)
    for i in range(12):
        buf.push(i)
    assert len(buf) == 5, f"len can never exceed the capacity; got {len(buf)} after 12 pushes into 5 slots."


def test_full_buffer_overwrites_the_oldest():
    buf = replay.RingBuffer(4)
    for i in range(6):
        buf.push(i)
    assert sorted(buf.slots) == [2, 3, 4, 5], f"After pushing 0..5 into 4 slots, the buffer should hold the newest four, 2..5. It holds {buf.slots}."
    assert buf.slots == [4, 5, 2, 3], f"The overwrite goes round the ring: slots should be [4, 5, 2, 3], got {buf.slots}."
    assert buf.next_slot == 2, "The next push should overwrite slot 2, which now holds the oldest item."


# ---------------------------------------------------------------- task 2: sampling


def test_sample_size_and_contents():
    buf = replay.RingBuffer(10)
    for i in range(10):
        buf.push(i)
    batch = buf.sample(64)
    assert isinstance(batch, list) and len(batch) == 64, "sample(n) returns a list of n transitions. With replacement, n may be larger than the buffer."
    assert set(batch) <= set(range(10)), "Every sampled item must be one that was stored."


def test_sample_ignores_empty_slots():
    buf = replay.RingBuffer(100)
    for i in range(3):
        buf.push(i)
    batch = buf.sample(200)
    assert None not in batch, "The buffer is not full yet: only slots that hold a transition may be sampled."
    assert set(batch) == {0, 1, 2}


def test_sample_is_uniform():
    buf = replay.RingBuffer(4, seed=1)
    for i in range(4):
        buf.push(i)
    counts = np.bincount(buf.sample(8000), minlength=4) / 8000
    assert np.all(np.abs(counts - 0.25) < 0.02), f"Each of 4 stored items should be drawn about 25% of the time; got {np.round(counts, 3).tolist()}."


def test_sample_uses_the_buffer_rng():
    a, b = replay.RingBuffer(50, seed=3), replay.RingBuffer(50, seed=3)
    for i in range(50):
        a.push(i)
        b.push(i)
    assert a.sample(20) == b.sample(20), "Two buffers with the same seed and contents should draw the same batch: use self.rng, not NumPy's global random state."


# ---------------------------------------------------------------- task 3: correlation


def test_correlation_of_known_sequences():
    assert abs(replay.lag_one_correlation(np.arange(30)) - 1.0) < 1e-9, "A steadily rising sequence: each item predicts the next perfectly, correlation 1."
    alternating = np.array([1.0, -1.0] * 15)
    assert abs(replay.lag_one_correlation(alternating) + 1.0) < 1e-9, "An alternating sequence has correlation -1."
    noise = np.random.default_rng(0).normal(size=5000)
    assert abs(replay.lag_one_correlation(noise)) < 0.05, "Independent noise should have a correlation near 0."


# ---------------------------------------------------------------- the point of the lab


def _race_left(batch):
    return [t[0][0] for t in batch]  # the fraction of the race still to run



def test_in_order_batches_are_highly_correlated():
    stream = replay.race_stream(300)
    in_order = [replay.lag_one_correlation(_race_left(stream[i : i + 32])) for i in range(0, 3000, 32)]
    assert np.mean(in_order) > 0.6, (
        f"32 consecutive laps: average lag-one correlation of 'race left' {np.mean(in_order):.2f}. Expected it high: consecutive laps are nearly the same."
    )


def test_sampled_batches_are_not():
    stream = replay.race_stream(300)
    buf = replay.RingBuffer(5000, seed=0)
    for t in stream:
        buf.push(t)
    sampled = [replay.lag_one_correlation(_race_left(buf.sample(32))) for _ in range(100)]
    assert abs(np.mean(sampled)) < 0.1, (
        f"32 laps sampled from the buffer: average correlation {np.mean(sampled):.2f}. Expected it near 0, because neighbours in a sampled batch come from unrelated moments."
    )
