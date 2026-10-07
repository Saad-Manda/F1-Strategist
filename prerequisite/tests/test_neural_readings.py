"""Execute R5 examples with independent analytic and unchanged-pack witnesses."""
import copy
import json
import math
import random

import numpy as np
import pytest
import torch

from test_foundations_readings import code, pack
from test_reading_shell import ROOT


@pytest.fixture(scope='module')
def neural():
    ns = {}
    course = json.loads((ROOT/'content/course-registry.json').read_text(encoding='utf-8'))
    for reading in course['readings']:
        if reading['module'] == 'neural-value-learning':
            for block in code(reading['source'].removeprefix('content/')):
                exec(compile(block, reading['source'], 'exec'), ns)
    return ns


def test_forward_shapes_selected_loss_and_pack(neural):
    reference = pack('p5-network')
    x = torch.tensor([[2., 1.], [0., 1.]], dtype=torch.float64)
    weight = torch.tensor([[1., -1.], [.5, .5], [-1., 2.]], dtype=torch.float64)
    bias = torch.tensor([0., 1., -1.], dtype=torch.float64)
    actual = neural['predict'](x, weight, bias)
    assert torch.equal(actual, reference.predict(x, weight, bias))
    assert actual.tolist() == [[1., 2.5, -1.], [-1., 1.5, 1.]]
    q = torch.tensor([[3., 5., 99.], [2., -1., 7.]], dtype=torch.float64)
    selected = q.gather(1, torch.tensor([[1], [0]])).squeeze(1)
    labels = torch.tensor([4., 3.], dtype=torch.float64)
    assert selected.shape == labels.shape == (2,)
    assert float(neural['mse'](selected, labels)) == float(reference.mse(selected, labels)) == 1
    for prediction, target in [(selected[:, None], labels), (torch.tensor([]), torch.tensor([])),
                               (torch.tensor([float('nan')]), torch.tensor([1.]))]:
        with pytest.raises(ValueError):
            neural['mse'](prediction, target)


def test_chain_rule_matches_finite_differences_and_one_sgd_step(neural):
    w1 = np.array([[1., -1.], [.5, .5]])
    w2 = np.array([2., -1.])
    def loss(first, second):
        return float(second @ np.maximum(first @ np.array([2., 1.]), 0))**2
    for index, expected in [((0, 0), 4), ((0, 1), 2), ((1, 0), -2), ((1, 1), -1)]:
        plus, minus = w1.copy(), w1.copy()
        plus[index] += 1e-6; minus[index] -= 1e-6
        assert (loss(plus, w2)-loss(minus, w2))/2e-6 == pytest.approx(expected, abs=1e-8)
    model = torch.nn.Linear(1, 2, dtype=torch.float64)
    with torch.no_grad():
        model.weight.zero_(); model.bias.zero_()
    x = torch.tensor([[.25]], dtype=torch.float64)
    labels = torch.tensor([[.25, .75]], dtype=torch.float64)
    before = x.clone(), labels.clone()
    optimizer = torch.optim.SGD(model.parameters(), lr=.1)
    result = neural['train_step'](model, optimizer, x, labels)
    assert result == .3125
    assert model.weight.detach().flatten().tolist() == pytest.approx([.00625, .01875])
    assert model.bias.detach().tolist() == pytest.approx([.025, .075])
    assert model(x).detach().flatten().tolist() == pytest.approx([.0265625, .0796875])
    assert torch.equal(x, before[0]) and torch.equal(labels, before[1])
    # Adam derivation is optional and checked separately from required SGD.
    theta, m, v = neural['adam_scalar'](2, 2, 0, 0, 1)
    assert (theta, m, v) == pytest.approx((1.999000000005, .2, .004))


def test_replay_copy_detachment_and_target_schedules(neural):
    reference = pack('p5-stability')
    buffer = []; expected = []
    for i in range(6):
        neural['push'](buffer, i, 4); reference.push(expected, i, 4)
    assert buffer == expected == [2, 3, 4, 5]
    assert neural['sample'](buffer, 20, random.Random(7)) == reference.sample(expected, 20, random.Random(7))
    online = torch.nn.Linear(1, 2, dtype=torch.float64)
    with torch.no_grad():
        online.weight.zero_(); online.bias.copy_(torch.tensor([1., 2.]))
    target = neural['make_target'](online)
    assert all(a.data_ptr() != b.data_ptr() for a, b in zip(online.parameters(), target.parameters()))
    with torch.no_grad():
        online.bias.copy_(torch.tensor([3., 4.]))
    neural['sync_target'](target, online, 1, 2)
    assert target.bias.tolist() == [1, 2]
    neural['soft_update'](target, online, .5)
    assert target.bias.tolist() == [2, 3]
    neural['sync_target'](target, online, 2, 2)
    assert target.bias.tolist() == [3, 4]
    assert all(not p.requires_grad and p.grad is None for p in target.parameters())
    states = torch.zeros((2, 1), dtype=torch.float64)
    rewards = torch.ones(2, dtype=torch.float64)
    done = torch.tensor([False, True])
    y = neural['targets'](online, states, rewards, done, .5)
    assert torch.equal(y, reference.targets(online, states, rewards, done, .5))
    assert y.tolist() == [3, 1] and not y.requires_grad
    assert .995**138 > .5 > .995**139
    assert math.ceil(math.log(.5)/math.log(.995))*4 == 556


def batch_models():
    online = torch.nn.Linear(1, 3, dtype=torch.float64)
    target = torch.nn.Linear(1, 3, dtype=torch.float64)  # Deliberately trainable source.
    with torch.no_grad():
        online.weight.zero_(); target.weight.zero_()
        online.bias.copy_(torch.tensor([5., 4., 100.]))
        target.bias.copy_(torch.tensor([1., 7., 99.]))
    batch = dict(states=torch.zeros((2, 1), dtype=torch.float64), actions=torch.tensor([0, 1]),
                 rewards=torch.ones(2, dtype=torch.float64), next_states=torch.zeros((2, 1), dtype=torch.float64),
                 terminated=torch.tensor([False, True]), legal_next=torch.tensor([[True, True, False], [False]*3]),
                 gamma=.5)
    return online, target, batch


def test_complete_updates_detach_mask_and_preserve_input_shapes(neural):
    for double, labels, loss in [(False, [4.5, 1.], 4.625), (True, [1.5, 1.], 10.625)]:
        online, target, batch = batch_models()
        before = {k: v.clone() for k, v in batch.items() if isinstance(v, torch.Tensor)}
        target_before = copy.deepcopy(target.state_dict())
        result = neural['dqn_step'](online, target, torch.optim.SGD(online.parameters(), lr=.1),
                                     **batch, double=double, max_norm=100)
        assert result['targets'].tolist() == labels
        assert result['loss'] == loss
        assert not result['targets'].requires_grad and not result['td_error'].requires_grad
        assert all(p.grad is None for p in target.parameters())
        assert all(torch.equal(target.state_dict()[k], v) for k, v in target_before.items())
        assert all(torch.equal(batch[k], v) for k, v in before.items())
        assert online.bias.grad[2] == 0  # Illegal output has no direct selected loss in this plain head.
    online, target, batch = batch_models()
    weights = torch.tensor([.5, 1.], dtype=torch.float64, requires_grad=True)
    result = neural['dqn_step'](online, target, torch.optim.SGD(online.parameters(), lr=.1),
                                 **batch, double=True, weights=weights, huber=True)
    assert result['loss'] == pytest.approx((.5*3+2.5)/2)
    assert weights.grad is None


def test_terminal_empty_masks_invalid_batches_and_gradient_clipping(neural):
    class NeverCalled(torch.nn.Module):
        def forward(self, x):
            raise AssertionError('terminal successor must not be evaluated')
    online, target, batch = batch_models()
    batch = {k: v[:1] if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
    batch['terminated'][:] = True; batch['legal_next'][:] = False
    before = torch.cat([p.detach().flatten() for p in online.parameters()])
    result = neural['dqn_step'](online, NeverCalled(), torch.optim.SGD(online.parameters(), lr=.1),
                                 **batch, max_norm=.01)
    assert result['targets'].shape == (1,) and result['targets'].item() == 1
    after = torch.cat([p.detach().flatten() for p in online.parameters()])
    assert torch.linalg.vector_norm(after-before) <= .00100001
    for change in ('mask', 'action', 'reward', 'weight'):
        online, target, batch = batch_models()
        if change == 'mask':
            batch['legal_next'][0] = False; batch['gamma'] = 0
        elif change == 'action': batch['actions'][0] = 3
        elif change == 'reward': batch['rewards'][0] = float('nan')
        else: batch['weights'] = torch.ones((2, 1), dtype=torch.float64)
        before = copy.deepcopy(online.state_dict())
        with pytest.raises(ValueError):
            neural['dqn_step'](online, target, torch.optim.SGD(online.parameters(), lr=.1), **batch)
        assert all(torch.equal(online.state_dict()[k], v) for k, v in before.items())


def test_double_ties_and_dueling_effective_identifiability(neural):
    reference = pack('p5-double-dueling')
    online = torch.tensor([[5., 4., 100.], [0., 0., 0.]], dtype=torch.float64, requires_grad=True)
    target = torch.tensor([[1., 7., 99.], [9., 9., 9.]], dtype=torch.float64, requires_grad=True)
    rewards = torch.tensor([1., -7.], dtype=torch.float64)
    done = torch.tensor([False, True]); legal = torch.tensor([[True, True, False], [False]*3])
    actual = neural['double_targets'](online, target, rewards, done, legal, .5)
    assert torch.equal(actual, reference.double_targets(online, target, rewards, done, legal, .5))
    assert actual.tolist() == [1.5, -7] and not actual.requires_grad
    tied = torch.tensor([[5., 5.]], dtype=torch.float64)
    assert neural['double_targets'](tied, torch.tensor([[1., 7.]]), torch.tensor([1.]),
                                    torch.tensor([False]), torch.tensor([[True, True]]), .5).item() == 1.5
    raw = torch.tensor([[-2., -5., -3.]], dtype=torch.float64, requires_grad=True)
    value = torch.tensor([[-10/3]], dtype=torch.float64, requires_grad=True)
    q = neural['dueling'](value, raw)
    assert q.tolist()[0] == pytest.approx([-2, -5, -3])
    assert torch.allclose(q, neural['dueling'](value, raw+10))
    assert torch.equal(q, reference.dueling(value, raw))
    q[0, 0].backward()
    assert raw.grad.tolist()[0] == pytest.approx([2/3, -1/3, -1/3])
    model = neural['DuelingMLP']().double()
    assert sum(p.numel() for p in model.parameters()) == 35655
    assert model(torch.zeros((2, 16), dtype=torch.float64)).shape == (2, 6)


def test_per_probabilities_correction_identity_and_pack(neural):
    reference = pack('p5-per')
    for alpha in (0, .5, 1):
        for beta in (0, .4, 1):
            p, weights = neural['distribution']([1, 4, 9], alpha, beta)
            expected = reference.distribution([1, 4, 9], alpha, beta)
            assert p == pytest.approx(expected[0]) and weights == pytest.approx(expected[1])
    p, weights = neural['distribution']([1, 4, 9], .5, 1)
    losses = np.array([1., 4., 9.])
    assert p == pytest.approx([1/6, 1/3, 1/2])
    assert weights == pytest.approx([1, .5, 1/3])
    assert neural['weighted_loss'](losses, weights) == reference.weighted_loss(losses, weights) == 2
    assert np.sum(p*(1/(3*p))*losses) == pytest.approx(14/3)
    assert np.sum(p*weights*losses) == pytest.approx(7/3)
    assert neural['new_priority']([]) == 1 and neural['new_priority']([1, 4, 9]) == 9
    assert neural['update_priority'](-3, 1) == reference.update_priority(-3, 1) == 4
    assert math.sqrt(math.sqrt(9)) != math.sqrt(9)  # Detect the plan's insertion exponent error.
    for raw in ([], [0, 1], [-1, 2], [float('nan')]):
        with pytest.raises(ValueError): neural['distribution'](raw, .5, 1)
    for shape in (np.ones((3, 1)), np.ones(2)):
        with pytest.raises(ValueError): neural['weighted_loss'](losses, shape)


def test_reward_loss_scales_and_centering_common_horizon(neural):
    first = torch.tensor([1., -2.], dtype=torch.float64)
    assert first.square().mean() == 2.5 and (10*first).square().mean() == 250
    assert neural['smooth_l1_witness'](first).mean() == 1
    assert neural['smooth_l1_witness'](10*first).mean() == 14.5
    assert 52*(-95+90) == -260 and 52*-95 == -4940
    assert sum(i >= 1000 and i % 4 == 0 for i in range(1, 4001)) == 751
