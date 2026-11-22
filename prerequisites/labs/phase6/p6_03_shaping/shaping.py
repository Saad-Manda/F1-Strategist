"""Lab p6-03: page 03's shaping term, and the one condition that keeps it safe.

    Task 1   shaping_term     γ·Φ(s') − Φ(s), with Φ taken as 0 once the episode has ended
    Task 2   shaped           wrap any reward function with a potential
    Task 3   TRAP_EXIT        which exit the UNZEROED version heads for (one letter)

The grids, the exact solver and the reward functions they start from are given, in
`labs/labkit/gridshape.py`. A reward function has the signature

    reward_fn(s, a, s2, done) -> float        s, s2 are (row, col) cells; done: s2 ends the episode

The tests solve each grid exactly (value iteration, gamma = 0.95) with and without your shaping
and compare the optimal actions in every single cell, so there is no training noise anywhere.

Run the checks with:  python -m labs check p6-03
"""

# ============================================================================ Task 1


def shaping_term(phi_s: float, phi_next: float, gamma: float, next_is_terminal: bool) -> float:
    """The potential-based shaping term F = γ·Φ(s') − Φ(s).

    When s' ends the episode its potential counts as 0, whatever phi_next says. Page 03's
    telescoping sum leaves γ^T·Φ(s_T) − Φ(s_0) over; if different endings kept different
    potentials, that leftover would depend on where the episode ended, i.e. on the policy.
    """
    # TODO: use 0 for the next potential when next_is_terminal, then gamma * next - phi_s
    raise NotImplementedError("TODO p6-03: use 0 for the next potential when next_is_terminal, then gamma * next - phi_s")


# ============================================================================ Task 2


def shaped(reward_fn, phi, gamma: float):
    """A new reward function: reward_fn's reward plus the shaping term for the step s -> s2.

    `phi(cell) -> float` is the potential. Use shaping_term, so the zero at the end is applied.
    """
    # TODO: return a function (s, a, s2, done) that adds shaping_term(phi(s), phi(s2), gamma, done) to reward_fn(s, a, s2, done)
    raise NotImplementedError("TODO p6-03: return a function (s, a, s2, done) that adds shaping_term(phi(s), phi(s2), gamma, done) to reward_fn(s, a, s2, done)")


# ============================================================================ Task 3

# TWO_EXITS (labkit.gridshape) has a near exit N worth 8 and a far exit F worth 10. Unshaped,
# the best route from S goes to F. Now shape it with Φ(N) = 5, Φ(every other cell) = 0, but
# WITHOUT the zero at the end (the episode's last potential is kept). Which exit does the
# optimal policy head for? Work it out from page 03's leftover term before you check.
# Answer "N" or "F".

TRAP_EXIT = None  # TODO: your answer


def unzeroed(reward_fn, phi, gamma: float):
    """Given: the trap. The same shaping with the last potential NOT set to 0."""

    def reward(s, a, s2, done):
        return reward_fn(s, a, s2, done) + gamma * phi(s2) - phi(s)

    return reward
