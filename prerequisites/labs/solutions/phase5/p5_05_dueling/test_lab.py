"""Checks for lab p5-05. Given code: nothing to edit here."""

import os
import sys

import numpy as np
import pytest
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dueling  # noqa: E402

# ---------------------------------------------------------------- task 1: the split by hand


def test_split_reproduces_page_05():
    v, a = dueling.split_q([-2.0, -5.0, -3.0])
    assert v == pytest.approx(-10 / 3), f"Page 05: V' = -3.33. Got {v}."
    assert np.allclose(a, [4 / 3, -5 / 3, 1 / 3]), f"Page 05: A' = [1.33, -1.67, 0.33]. Got {np.round(a, 2).tolist()}."


def test_split_is_unique_and_adds_up():
    q = np.array([-41.0, -38.0, -45.0, -40.0, -39.0, -44.0])
    v, a = dueling.split_q(q)
    assert abs(np.mean(a)) < 1e-9, "The advantages must average to zero."
    assert np.allclose(v + a, q), "V + A must give back Q."


# ---------------------------------------------------------------- task 2: combining a batch


def test_combine_small_examples():
    got = dueling.combine(torch.tensor([[-10 / 3]]), torch.tensor([[4 / 3, -5 / 3, 1 / 3]]))
    assert got.shape == (1, 3), f"Q should have shape (batch, actions) = (1, 3); got {tuple(got.shape)}."
    assert torch.allclose(got, torch.tensor([[-2.0, -5.0, -3.0]])), f"Page 05's V' and A' should combine back to Q = [-2, -5, -3]; got {got.tolist()}."
    got = dueling.combine(torch.tensor([[1.0]]), torch.tensor([[3.0, 5.0, 1.0]]))
    assert torch.allclose(got, torch.tensor([[1.0, 3.0, -1.0]])), (
        f"V = 1, A = [3, 5, 1]: the mean of A is 3, so Q = 1 + [0, 2, -2] = [1, 3, -1]. Got {got.tolist()}."
    )


def test_combine_mean_is_per_row():
    value = torch.tensor([[0.0], [0.0]])
    advantage = torch.tensor([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]])
    got = dueling.combine(value, advantage)
    want = torch.tensor([[-1.0, 0.0, 1.0], [-10.0, 0.0, 10.0]])
    assert torch.allclose(got, want), (
        f"Each row's advantages must be centred on that row's own mean. Expected {want.tolist()}, got {got.tolist()}. "
        "A mean over the batch dimension runs without error and subtracts the same numbers from every row (page 11)."
    )


def test_shifting_the_advantages_changes_nothing():
    value = torch.tensor([[1.5], [-2.0]])
    advantage = torch.tensor([[0.3, -0.7, 1.1], [2.0, 0.0, -1.0]])
    base = dueling.combine(value, advantage)
    assert torch.allclose(dueling.combine(value, advantage + 10.0), base), "Adding the same number to every advantage of a row must leave Q unchanged: the mean subtraction absorbs it."


def test_the_split_is_pinned():
    value = torch.tensor([[1.5]])
    advantage = torch.tensor([[0.3, -0.7, 1.1]])
    base = dueling.combine(value, advantage)
    plain_sum = value + advantage
    assert torch.allclose((value + 10) + (advantage - 10), plain_sum), "(a plain sum would not notice the trade: that is page 05's degeneracy)"
    traded = dueling.combine(value + 10.0, advantage - 10.0)
    assert torch.allclose(traded, base + 10.0), (
        "Moving 10 from the advantages into the value should raise every Q by exactly 10, because the advantages' shift is absorbed and the value's is not. "
        f"Got {traded.tolist()} from {base.tolist()}."
    )


# ---------------------------------------------------------------- task 3: the network


def test_net_layers_and_shapes():
    torch.manual_seed(0)
    net = dueling.TwoHeadNet(n_obs=4, n_actions=3, width=32)
    assert isinstance(net.body, torch.nn.Sequential), "self.body should be an nn.Sequential."
    assert net.value_head.out_features == 1, "The value head outputs one number."
    assert net.advantage_head.out_features == 3, "The advantage head outputs one number per action."
    assert net.value_head.in_features == 32 and net.advantage_head.in_features == 32, "Both heads read the body's 32 outputs."
    q = net(torch.randn(5, 4))
    assert q.shape == (5, 3), f"A batch of 5 observations should give Q of shape (5, 3); got {tuple(q.shape)}."


def test_net_uses_combine_and_one_shared_body():
    torch.manual_seed(1)
    net = dueling.TwoHeadNet()
    obs = torch.randn(7, 4)
    value, advantage = net.streams(obs)
    assert torch.allclose(net(obs), dueling.combine(value, advantage), atol=1e-6), "forward should return combine(value head, advantage head), both fed by the same body output."
    q_minus_v = net(obs) - value
    assert torch.allclose(q_minus_v.mean(dim=1), torch.zeros(7), atol=1e-6), "In every row, Q - V should average to zero across the actions."


def test_net_parameter_count():
    net = dueling.TwoHeadNet(n_obs=16, n_actions=6, width=128)
    count = sum(p.numel() for p in net.parameters())
    assert count == 16 * 128 + 128 + 128 * 128 + 128 + 128 + 1 + 128 * 6 + 6, (
        f"Counted {count} adjustable numbers. With the real trunk's sizes and one linear layer per head it should be 19,591: inputs × outputs + outputs, layer by layer."
    )


def test_gradients_reach_both_heads():
    torch.manual_seed(2)
    net = dueling.TwoHeadNet()
    net(torch.randn(8, 4))[:, 1].sum().backward()
    assert net.value_head.weight.grad is not None and net.value_head.weight.grad.abs().sum() > 0, "A loss on Q should send gradient into the value head."
    assert net.advantage_head.weight.grad.abs().sum() > 0, "...and into the advantage head."
