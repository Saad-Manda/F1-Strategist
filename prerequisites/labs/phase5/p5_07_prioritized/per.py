"""Lab p5-07: page 07's prioritized replay, from the sum tree up, and the bug recorded against the plan.

    Task 1   SumTree.update, SumTree.find          page 07's tree in one flat array
    Task 2   leaf_value, importance_weights        priority -> leaf, probability -> weight
    Task 3   PrioritizedMemory.push                a new transition at the current maximum
    Task 4   check_new_transition_priority         YOUR test: it must catch PlannedMemory's bug

THE FLAT TREE (page 07). For `capacity` leaves the array has 2 * capacity - 1 nodes:
    node 0 is the root; node k has children 2k + 1 and 2k + 2;
    the last `capacity` nodes are the leaves, so leaf i is node i + capacity - 1.
Every node above the leaves holds the sum of its two children.

Run the checks with:  python -m labs check p5-07
"""

import numpy as np

# ============================================================================ Task 1


class SumTree:
    def __init__(self, capacity):
        self.capacity = capacity
        self.nodes = np.zeros(2 * capacity - 1)

    def leaf(self, i):
        """The value of leaf i. Given."""
        return float(self.nodes[i + self.capacity - 1])

    def leaves(self):
        """All leaf values, in order. Given."""
        return self.nodes[self.capacity - 1 :].copy()

    def total(self):
        """The sum of all leaves: the root. Given."""
        return float(self.nodes[0])

    def update(self, i, value):
        """Set leaf i to `value`, and add the change to every node on the path up to the root.

        Page 07: change leaf1 from 1 to 5, the change is +4, add it to its parent and the root.
        The parent of node k is (k - 1) // 2. Touch nothing off that path.
        """
        # TODO: k = i + capacity - 1; change = value - nodes[k]; set it; climb with k = (k - 1) // 2 adding the change
        raise NotImplementedError("TODO p5-07: k = i + capacity - 1; change = value - nodes[k]; set it; climb with k = (k - 1) // 2 adding the change")

    def find(self, mass):
        """The leaf index that owns `mass`, a number between 0 and total().

        Page 07's walk: start at the root. At each node, go left if mass is no larger than the
        left child's value; otherwise subtract the left child's value and go right. Stop at a
        leaf and return its leaf index (0 .. capacity - 1), not its node index.
        """
        # TODO: walk down from node 0 while k is not a leaf, then convert the node index to a leaf index
        raise NotImplementedError("TODO p5-07: walk down from node 0 while k is not a leaf, then convert the node index to a leaf index")


# ============================================================================ Task 2


def leaf_value(td_error, alpha, eps=1e-6):
    """What a leaf stores for a transition with this TD error: p ** alpha, with p = |td_error| + eps."""
    # TODO: (abs(td_error) + eps) ** alpha
    raise NotImplementedError("TODO p5-07: (abs(td_error) + eps) ** alpha")


def importance_weights(probs, n_stored, beta):
    """Page 07's correction: w = (N * P(i)) ** -beta, then divided by the largest w in the batch.

    `probs` is an array of the sampled transitions' probabilities. Returns an array of the same
    shape whose largest entry is exactly 1.
    """
    # TODO: (n_stored * probs) ** -beta, divided by its maximum
    raise NotImplementedError("TODO p5-07: (n_stored * probs) ** -beta, divided by its maximum")


# ============================================================================ Task 3


class PrioritizedMemory:
    def __init__(self, capacity, alpha=0.6, beta=0.4, seed=0):
        self.capacity, self.alpha, self.beta = capacity, alpha, beta
        self.tree = SumTree(capacity)
        self.items = [None] * capacity
        self.next_slot, self.count = 0, 0
        self.rng = np.random.default_rng(seed)

    def push(self, item):
        """Store `item` at the CURRENT MAXIMUM PRIORITY, so it is sampled soon and gets a real one.

        The leaves already hold p ** alpha. The new leaf is the largest existing leaf, as it is,
        or 1.0 if every leaf is still empty. Then advance the ring, as in lab p5-04.
        """
        # TODO: largest leaf as it is (1.0 if zero), store the item, tree.update, advance next_slot and count
        raise NotImplementedError("TODO p5-07: largest leaf as it is (1.0 if zero), store the item, tree.update, advance next_slot and count")

    def sample(self, n):
        """Given. One draw from each of n equal segments of the total. Returns (items, indices, weights)."""
        edges = np.linspace(0.0, self.tree.total(), n + 1)
        idx = np.array([self.tree.find(self.rng.uniform(edges[j], edges[j + 1])) for j in range(n)])
        idx = np.minimum(idx, self.count - 1)
        probs = np.array([self.tree.leaf(i) for i in idx]) / self.tree.total()
        return [self.items[i] for i in idx], idx, importance_weights(probs, self.count, self.beta)

    def update_priorities(self, indices, td_errors):
        """Given. The write-back: each sampled transition's leaf becomes leaf_value(its new TD error)."""
        for i, e in zip(indices, td_errors):
            self.tree.update(int(i), leaf_value(e, self.alpha))

    def __len__(self):
        return self.count


class PlannedMemory(PrioritizedMemory):
    """Given. push() exactly as the real plan writes it: the largest leaf, floored at 1.0, raised to alpha again."""

    def push(self, item):
        priority = max(float(self.tree.leaves().max()), 1.0)
        self.items[self.next_slot] = item
        self.tree.update(self.next_slot, priority**self.alpha)
        self.next_slot = (self.next_slot + 1) % self.capacity
        self.count = min(self.count + 1, self.capacity)


# ============================================================================ Task 4


def check_new_transition_priority(memory_class):
    """YOUR TEST. Raise AssertionError if memory_class stores a new transition anywhere except
    at the current maximum leaf. Return quietly if it gets it right.

    Build a memory with memory_class(capacity=8), push a few items, give them priorities with
    update_priorities, push one more, and assert that the new leaf equals the largest of the
    earlier leaves. Choose the priorities so that the planned version's mistake shows. Page 07
    and page 09 stage 5 say which numbers do that; there is more than one way to catch it.
    """
    # TODO: priorities large enough that a max leaf above 1 gets raised to alpha again
    raise NotImplementedError("TODO p5-07: priorities large enough that a max leaf above 1 gets raised to alpha again")
