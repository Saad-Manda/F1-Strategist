"""Lab p9-03 · GAE, backwards.

Page 03's estimator over a rollout buffer: a run of steps from one environment that may hold the
end of one episode, a whole episode, and the start of the next. Three functions, in order.

Conventions (one entry per step t):
    rewards[t]       the reward of step t
    values[t]        the critic's V(s_t)
    ends[t]          True if the episode ended right after step t (terminated OR truncated)
    terminated[t]    True if it ended because the episode really finished (a terminal state)
    final_values[t]  where ends[t] and not terminated[t]: the critic's value of the observation
                     the episode was cut off at (a time limit, not a real ending)
    last_value       the critic's value of the observation after the buffer's last step, used
                     when the buffer stops in the middle of an episode

Run `python -m labs check p9-03`.
"""

from __future__ import annotations

import numpy as np


def next_values(values, ends, terminated, final_values, last_value):
    """V(s_{t+1}) for every step, as the TD target needs it.

    * the episode goes on and the next step is in the buffer: values[t + 1]
    * the episode goes on but the buffer stops here: last_value
    * the episode TERMINATED after step t: 0 (nothing comes after a real ending)
    * the episode was TRUNCATED after step t: final_values[t] (the race would have gone on)
    """
    n = len(values)
    out = np.empty(n)
    for t in range(n):
        # TODO: the four cases of the docstring, in the order ends / terminated, then inside the buffer or not
        raise NotImplementedError("TODO p9-03: the four cases of the docstring, in the order ends / terminated, then inside the buffer or not")
    return out


def td_residuals(rewards, values, next_vals, gamma):
    """delta_t = r_t + gamma * V(s_{t+1}) - V(s_t), as an array."""
    # TODO: one line with numpy arrays
    raise NotImplementedError("TODO p9-03: one line with numpy arrays")


def gae(rewards, values, next_vals, ends, gamma, lam):
    """GAE advantages and returns (advantage + value), by one backward pass.

    A_t = delta_t + gamma * lam * A_{t+1}, except that nothing is carried across the end of an
    episode: where ends[t], A_t = delta_t.
    """
    deltas = td_residuals(rewards, values, next_vals, gamma)
    adv = np.zeros(len(deltas))
    carry = 0.0
    for t in reversed(range(len(deltas))):
        # TODO: reset the carry at an episode end, then A_t = delta_t + gamma * lam * carry
        raise NotImplementedError("TODO p9-03: reset the carry at an episode end, then A_t = delta_t + gamma * lam * carry")
    return adv, adv + np.asarray(values, float)
