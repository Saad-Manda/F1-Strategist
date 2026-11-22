"""Lab p5-05: page 05's value/advantage split, as code.

    Task 1   split_q        the unique (V, A) with mean-zero A that adds up to a given Q (NumPy)
    Task 2   combine        V + (A - mean of A), for a whole batch at once (PyTorch)
    Task 3   TwoHeadNet     a shared body, a one-number value head, a per-action advantage head

Shapes, for a batch of B observations and n actions:
    value      (B, 1)    one number per observation
    advantage  (B, n)    one number per observation and action
    Q          (B, n)

Run the checks with:  python -m labs check p5-05
"""

import numpy as np
import torch
import torch.nn as nn

# ============================================================================ Task 1


def split_q(q):
    """Page 05's mean-subtracted decomposition of one state's Q-values. Returns (V, A).

    V is a float and A a NumPy array with A.mean() == 0 and V + A == q.
    """
    # TODO: V is the mean of q; A is q minus that mean
    raise NotImplementedError("TODO p5-05: V is the mean of q; A is q minus that mean")


# ============================================================================ Task 2


def combine(value, advantage):
    """Q = value + (advantage - its mean over the actions), row by row.

    The mean is taken across the actions of each row (the last dimension), keeping that
    dimension so it subtracts from every action: .mean(dim=-1, keepdim=True).
    """
    # TODO: value + advantage - advantage.mean(dim=-1, keepdim=True)
    raise NotImplementedError("TODO p5-05: value + advantage - advantage.mean(dim=-1, keepdim=True)")


# ============================================================================ Task 3


class TwoHeadNet(nn.Module):
    """body: Linear(n_obs, width) -> ReLU -> Linear(width, width) -> ReLU, shared by both heads.
    value_head: Linear(width, 1).  advantage_head: Linear(width, n_actions).
    """

    def __init__(self, n_obs=4, n_actions=3, width=32):
        super().__init__()
        # TODO: build self.body (an nn.Sequential), self.value_head and self.advantage_head
        raise NotImplementedError("TODO p5-05: build self.body (an nn.Sequential), self.value_head and self.advantage_head")

    def forward(self, obs):
        """obs (B, n_obs) -> Q (B, n_actions), using combine()."""
        # TODO: run the body once, both heads on its output, then combine
        raise NotImplementedError("TODO p5-05: run the body once, both heads on its output, then combine")

    def streams(self, obs):
        """The two heads' raw outputs, (value, advantage), for inspection. Given."""
        h = self.body(obs)
        return self.value_head(h), self.advantage_head(h)
