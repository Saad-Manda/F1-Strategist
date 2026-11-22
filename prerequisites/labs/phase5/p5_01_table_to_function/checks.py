"""Checks for lab p5-01. Given code: read it if you like, but there is nothing to edit here."""

import copy

import numpy as np
import torch

from labs.labkit.checks import passed, require

LAB = "p5-01"


def _reference_step(net, lr, states, targets):
    """What one plain gradient step should do, computed independently of the learner's code."""
    twin = copy.deepcopy(net)
    opt = torch.optim.SGD(twin.parameters(), lr=lr)
    x = torch.as_tensor((np.asarray(states, dtype=np.float32).reshape(-1, 1) - 500.5) / 500.0)
    loss = ((twin(x).squeeze(1) - torch.as_tensor(np.asarray(targets, dtype=np.float32))) ** 2).mean()
    opt.zero_grad()
    loss.backward()
    opt.step()
    return twin, loss.item()


def update(net_update, make_net, values_of):
    net = make_net(3)
    twin, want_loss = _reference_step(net, 0.05, [200, 700], [-0.5, 0.5])
    before = values_of(net)
    got = net_update(net, torch.optim.SGD(net.parameters(), lr=0.05), [200, 700], [-0.5, 0.5])
    require(isinstance(got, float), f"net_update should return the loss as a plain float (loss.item()); got {type(got).__name__}.")
    require(abs(got - want_loss) < 1e-5, f"The returned loss should be the mean squared error before the step, {want_loss:.5f}; got {got:.5f}.")
    after = values_of(net)
    require(not np.allclose(after, before), "The network's predictions did not change: the step was not applied (optimizer.step()).")
    require(np.allclose(after, values_of(twin), atol=1e-5), "The network moved, but not by exactly one gradient step on the mean squared error. Check zero_grad, the mean, and that step is called once.")
    net2 = make_net(3)
    opt = torch.optim.SGD(net2.parameters(), lr=0.05)
    net_update(net2, opt, [500], [1.0])
    net_update(net2, opt, [500], [1.0])
    twin2, _ = _reference_step(make_net(3), 0.05, [500], [1.0])
    twin2, _ = _reference_step(twin2, 0.05, [500], [1.0])
    require(np.allclose(values_of(net2), values_of(twin2), atol=1e-5), "Two calls should equal two separate steps. If they do not, the gradients are piling up between calls: call optimizer.zero_grad() before backward().")
    passed(LAB, "update", "TODO 1: net_update makes exactly one gradient step on the mean squared error.")


def spread(table, moved):
    require(np.count_nonzero(table) == 1 and table[499] > 0, "Run the cell as given: the table update should change only state 500.")
    require(moved[499] > 0, "The network's value at state 500 should have moved up, toward the target 1.0.")
    require(abs(moved[0]) > 0.5 * moved[499], "Expected state 1 to move by most of what state 500 moved.")
    passed(LAB, "A", "Part A: one network update moved every state's value.")


def learning(learn_from_walks, values_of, rms_error):
    table, net = learn_from_walks(50, 0)
    require(np.count_nonzero(table) > 0, "The table should have learned something: run the cell as given.")
    v = values_of(net)
    require(not np.allclose(v, values_of(learn_from_walks(0, 0)[1])), "The network did not change at all. Is net_update being called inside the walk loop?")
    again = values_of(learn_from_walks(50, 0)[1])
    require(np.allclose(v, again), "The same seed should give the same network: all randomness has to come from the seed.")
    error = rms_error(v)
    require(error < 0.3, f"After 50 walks the network's RMS error should be under 0.3; got {error:.3f}. Is every visited state's target the walk's final reward?")
    require(v[0] < v[-1], "The network should have learned that the left end is worse than the right end.")
    passed(LAB, "learning", "TODO 2: the network learns the walk's values from finished walks.")


def comparison(results):
    require(set(results) == {20, 50, 200}, "Run the comparison cell as given.")
    require(results[50][1] < results[50][0] - 0.1, f"With 50 walks the network should clearly beat the table; got {results[50][1]:.3f} against {results[50][0]:.3f}.")
    require(results[200][0] < results[20][0], "The table should improve with more walks.")
    passed(LAB, "B", "Part B: with little data, the network's guesses about unseen states beat the table's zeros.")


def interference(far_move):
    require(far_move > 0.02, f"States 501-1000 should have moved noticeably; they moved {far_move:.4f} on average.")
    passed(LAB, "C", "Part C: updates about one region moved the network's values in another.")
