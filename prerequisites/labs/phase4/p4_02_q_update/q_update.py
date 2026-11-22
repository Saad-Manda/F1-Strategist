"""Lab p4-02: the Q-learning update, as two small functions.

The table `Q` is a NumPy array with one row per state and one column per action, so
Q[state, action] is one cell. `legal_next` is a list of the actions that are legal in the
next state.

    target = reward                                          if the transition ended the episode
    target = reward + gamma * max over LEGAL a' of Q[next_state, a']       otherwise
    delta  = target - Q[state, action]
    Q[state, action] <- Q[state, action] + alpha * delta

Run the checks with:  python -m labs check p4-02
"""

import numpy as np

# page 02's toy: two decision states, one terminal state, two actions
S1, S2, S3 = 0, 1, 2
A0, A1 = 0, 1
N_STATES, N_ACTIONS = 3, 2

# (state, action) -> (reward, next state, done)
TOY = {
    (S1, A0): (-1.0, S2, False),
    (S1, A1): (-3.0, S3, True),
    (S2, A0): (-1.0, S3, True),
    (S2, A1): (-2.0, S3, True),
}

# the four transitions page 02 runs by hand: (state, action, reward, next state, done)
PAGE_TRANSITIONS = [
    (S1, A0, -1.0, S2, False),
    (S2, A0, -1.0, S3, True),
    (S1, A1, -3.0, S3, True),
    (S1, A0, -1.0, S2, False),
]


# ============================================================================ Task 1


def td_target(Q, reward, next_state, done, legal_next, gamma=1.0):
    """The Q-learning target for one transition. Returns a float.

    If `done`, nothing follows: the target is the reward alone, whatever the table says about
    next_state. Otherwise add gamma times the largest Q[next_state, a'] among the actions in
    `legal_next`. Actions that are not in `legal_next` must not be considered at all.
    """
    # TODO: return reward when done; otherwise reward + gamma * the max of Q[next_state, a] over a in legal_next
    raise NotImplementedError("TODO p4-02: return reward when done; otherwise reward + gamma * the max of Q[next_state, a] over a in legal_next")


# ============================================================================ Task 2


def q_update(Q, state, action, reward, next_state, done, legal_next, alpha, gamma=1.0):
    """Apply one Q-learning update to the table, in place. Returns the TD error (delta).

    Exactly one cell changes: Q[state, action].
    """
    # TODO: delta = td_target(...) - Q[state, action]; move that one cell by alpha * delta; return delta
    raise NotImplementedError("TODO p4-02: delta = td_target(...) - Q[state, action]; move that one cell by alpha * delta; return delta")


# ============================================================================ Given: used by the checks


def train_on_toy(n_transitions: int, alpha: float, rng: np.random.Generator) -> np.ndarray:
    """Feed your q_update a long stream of randomly chosen transitions of the toy. Given."""
    Q = np.zeros((N_STATES, N_ACTIONS))
    pairs = list(TOY)
    for _ in range(n_transitions):
        state, action = pairs[int(rng.integers(len(pairs)))]
        reward, next_state, done = TOY[(state, action)]
        q_update(Q, state, action, reward, next_state, done, [A0, A1], alpha)
    return Q
