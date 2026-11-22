"""Checks for lab p5-07. Given code: nothing to edit here."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import per  # noqa: E402

# ---------------------------------------------------------------- task 1: the tree


def page_tree():
    tree = per.SumTree(4)
    for i, v in enumerate([3.0, 1.0, 4.0, 2.0]):
        tree.update(i, v)
    return tree


def test_tree_builds_page_07_diagram():
    tree = page_tree()
    assert np.allclose(tree.nodes, [10, 4, 6, 3, 1, 4, 2]), f"Leaves 3, 1, 4, 2 should give the flat array [10, 4, 6, 3, 1, 4, 2] (page 07). Got {tree.nodes.tolist()}."


def test_tree_update_touches_only_the_path():
    tree = page_tree()
    tree.update(1, 5.0)
    assert np.allclose(tree.nodes, [14, 8, 6, 3, 5, 4, 2]), f"Changing leaf1 from 1 to 5 adds 4 to its parent and the root, nothing else. Got {tree.nodes.tolist()}."
    tree.update(1, 5.0)
    assert np.allclose(tree.nodes, [14, 8, 6, 3, 5, 4, 2]), "Setting a leaf to the value it already has must change nothing: add the change, not the value."


def test_tree_find_page_07_walk():
    tree = page_tree()
    assert tree.find(6.5) == 2, f"Page 07: a mass of 6.5 walks right, then left, to leaf 2. Got {tree.find(6.5)}."
    assert [tree.find(m) for m in (0.5, 3.0, 3.5, 4.0, 4.5, 8.0, 8.5, 10.0)] == [0, 0, 1, 1, 2, 2, 3, 3], (
        "Leaf 0 owns 0-3, leaf 1 owns 3-4, leaf 2 owns 4-8, leaf 3 owns 8-10. A mass exactly on a boundary goes left."
    )


def test_tree_find_is_proportional():
    tree = page_tree()
    rng = np.random.default_rng(0)
    counts = np.bincount([tree.find(rng.uniform(0, tree.total())) for _ in range(20000)], minlength=4) / 20000
    assert np.allclose(counts, [0.3, 0.1, 0.4, 0.2], atol=0.015), f"Each leaf should be found in proportion to its value: 30%, 10%, 40%, 20%. Got {np.round(counts, 3).tolist()}."


def test_tree_with_capacity_not_a_power_of_two():
    tree = per.SumTree(5)
    for i, v in enumerate([1.0, 2.0, 3.0, 4.0, 5.0]):
        tree.update(i, v)
    assert tree.total() == pytest.approx(15.0)
    rng = np.random.default_rng(1)
    counts = np.bincount([tree.find(rng.uniform(0, 15)) for _ in range(30000)], minlength=5) / 30000
    assert np.allclose(counts, np.array([1, 2, 3, 4, 5]) / 15, atol=0.015), "The flat layout must also work when the capacity is not a power of two."


# ---------------------------------------------------------------- task 2: probabilities and weights


def test_page_07_probabilities():
    leaves = np.array([per.leaf_value(e, 0.6, eps=0.0) for e in (0.5, 0.5, 0.5, 8.0)])
    assert np.allclose(leaves, [0.660, 0.660, 0.660, 3.482], atol=1e-3), f"Page 07: 0.5^0.6 = 0.660 and 8^0.6 = 3.482. Got {np.round(leaves, 3).tolist()}."
    probs = leaves / leaves.sum()
    assert probs[3] == pytest.approx(0.638, abs=1e-3) and probs[0] == pytest.approx(0.121, abs=1e-3)
    assert per.leaf_value(0.0, 0.6) > 0, "The small eps keeps every priority above zero, so no transition is never sampled."
    assert per.leaf_value(-8.0, 0.6) == pytest.approx(per.leaf_value(8.0, 0.6)), "Priority uses the size of the error, |δ|: a negative error counts the same as a positive one."


def test_page_07_weights():
    probs = np.array([0.121, 0.638])
    w = per.importance_weights(probs, 4, 0.4)
    assert w.max() == pytest.approx(1.0), "After dividing by the largest weight, the largest is exactly 1."
    assert np.allclose(w, [1.0, 0.514], atol=2e-3), f"Page 07 at beta = 0.4: weights 1.000 and 0.514. Got {np.round(w, 3).tolist()}."
    assert np.allclose(per.importance_weights(probs, 4, 1.0), [1.0, 0.189], atol=2e-3), "Page 07 at beta = 1: weights 1.000 and 0.189."
    assert np.allclose(per.importance_weights(probs, 4, 0.0), [1.0, 1.0]), "At beta = 0 there is no correction: every weight is 1."


# ---------------------------------------------------------------- task 3: push


def filled(memory_class, errors):
    memory = memory_class(capacity=8)
    for i in range(len(errors)):
        memory.push(i)
    memory.update_priorities(np.arange(len(errors)), errors)
    memory.push("new")
    return memory


def test_first_push_into_an_empty_memory():
    memory = per.PrioritizedMemory(capacity=4)
    memory.push("a")
    assert memory.tree.leaf(0) == pytest.approx(1.0), "With every leaf still empty, a new transition is stored at 1.0."
    assert len(memory) == 1 and memory.next_slot == 1


def test_new_transition_at_the_maximum_large_errors():
    memory = filled(per.PrioritizedMemory, [8.0, 0.5, 0.5, 0.5])
    assert memory.tree.leaf(4) == pytest.approx(3.482, abs=1e-3), (
        f"The largest leaf is the pit stop's 3.482, so the new transition should be stored at 3.482 (page 09 stage 5). Got {memory.tree.leaf(4):.3f}."
    )


def test_new_transition_at_the_maximum_small_errors():
    memory = filled(per.PrioritizedMemory, [0.2, 0.1, 0.1, 0.1])
    assert memory.tree.leaf(4) == pytest.approx(0.2**0.6, abs=1e-3), f"With small errors the maximum leaf is 0.381; the new transition belongs there. Got {memory.tree.leaf(4):.3f}."


def test_push_wraps_round_the_ring():
    memory = per.PrioritizedMemory(capacity=3)
    for i in range(5):
        memory.push(i)
    assert memory.items == [3, 4, 2] and len(memory) == 3, "Once full, push overwrites the oldest slot, as the ring buffer in p5-04 did."


def test_sampling_favours_surprising_transitions():
    memory = per.PrioritizedMemory(capacity=1024, seed=0)
    for i in range(1000):
        memory.push("rare" if i % 33 == 0 else "routine")
    memory.update_priorities(np.arange(1000), [8.0 if i % 33 == 0 else 0.5 for i in range(1000)])
    share = np.mean([item == "rare" for _ in range(300) for item in memory.sample(32)[0]])
    assert 0.12 < share < 0.17, f"31 of 1000 transitions are rare (3.1%). Page 07's formula predicts them in 14.4% of batch slots; got {share:.1%}."


# ---------------------------------------------------------------- task 4: your test


class Reference(per.PrioritizedMemory):
    """A correct push, independent of yours, so that your test is judged on its own."""

    def push(self, item):
        top = float(self.tree.leaves().max())
        self.items[self.next_slot] = item
        self.tree.update(self.next_slot, top if top > 0 else 1.0)
        self.next_slot = (self.next_slot + 1) % self.capacity
        self.count = min(self.count + 1, self.capacity)


def test_your_check_passes_a_correct_memory():
    per.check_new_transition_priority(Reference)


def test_your_check_catches_the_planned_bug():
    with pytest.raises(AssertionError):
        per.check_new_transition_priority(per.PlannedMemory)


def test_the_planned_bug_does_not_always_point_one_way():
    high = filled(per.PlannedMemory, [8.0, 0.5, 0.5, 0.5])
    low = filled(per.PlannedMemory, [0.2, 0.1, 0.1, 0.1])
    assert high.tree.leaf(4) == pytest.approx(3.482**0.6, abs=1e-3), "(given) with large errors the planned push stores 2.114, below the maximum"
    assert low.tree.leaf(4) == pytest.approx(1.0), "(given) with small errors it stores 1.0, above the maximum 0.381"
