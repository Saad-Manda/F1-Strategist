"""Checks for lab p5-03. Given code: read it if you like, but there is nothing to edit here."""

import copy
import math

import torch

from labs.labkit.checks import passed, require

LAB = "p5-03"


def _params(net):
    return [p.detach().clone() for p in net.parameters()]


def updates(soft_update, hard_update, make_net):
    online, target = make_net(0), make_net(1)
    old_t, old_o = _params(target), _params(online)
    soft_update(target, online, 0.25)
    for t, ot, oo in zip(target.parameters(), old_t, old_o):
        require(torch.allclose(t, 0.25 * oo + 0.75 * ot, atol=1e-6), "After soft_update with tau = 0.25, every target weight should be 0.25 × online + 0.75 × its old value.")
    for o, oo in zip(online.parameters(), old_o):
        require(torch.equal(o, oo), "soft_update must not change the online network.")
    require(all(not p.requires_grad or p.grad is None for p in target.parameters()), "soft_update should not create gradients on the target network.")
    soft_update(target, online, 0.0)
    for t, ot, oo in zip(target.parameters(), old_t, old_o):
        require(torch.allclose(t, 0.25 * oo + 0.75 * ot, atol=1e-6), "With tau = 0 nothing should move.")

    online, target = make_net(0), make_net(1)
    hard_update(target, online)
    require(target is not online, "hard_update must keep two separate networks.")
    for t, o in zip(target.parameters(), online.parameters()):
        require(torch.equal(t, o), "After hard_update every target weight should equal the online weight.")
    with torch.no_grad():
        next(online.parameters()).add_(1.0)
    require(not torch.equal(next(target.parameters()), next(online.parameters())), "Changing the online network after hard_update changed the target too: they are sharing tensors, not copying numbers. Use load_state_dict.")
    passed(LAB, "updates", "TODO 1 and 2: soft and hard updates move the target and leave the online network alone.")


def halving(updates_to_halve):
    for tau in (0.005, 0.05):
        want = math.ceil(math.log(0.5) / math.log(1 - tau))
        got = updates_to_halve(tau)
        require(got == want, f"At tau = {tau} half the gap should close after {want} updates; measured {got}.")
    passed(LAB, "halving", "Part A: the measured half-life matches page 03's formula.")


def one_step(moves):
    require(abs(moves["same network"]) > 1e-4, "With the same network the target should have moved.")
    require(moves["frozen copy"] == 0.0, "With a frozen copy the target should not have moved at all.")
    passed(LAB, "B", "Part B: one update moved the target only when the trained network computed it.")


def training_step(train_chain):
    worst = train_chain("soft", updates=150)
    require(len(worst) == 16, "Run the cell as given.")
    require(worst[-1] < worst[0], f"With a soft target network the worst error should fall during training; it went from {worst[0]:.2f} to {worst[-1]:.2f}. Check the target: -1 plus the next state's value, and only -1 when done.")
    require(worst[-1] < 19.0, f"After 150 updates the worst error should be well below its starting 20; got {worst[-1]:.2f}.")
    a, b = train_chain("soft", updates=50), train_chain("soft", updates=50)
    require(a == b, "The same seed should give the same run.")
    passed(LAB, "train", "TODO 3: the chain trains with a target network.")


def three_ways(curves):
    require(set(curves) == {"same", "soft", "hard"}, "Run the cell as given.")
    require(max(curves["same"]) > 100, f"Without a target network the error should run far past the chain's scale of 20; its largest was {max(curves['same']):.1f}.")
    require(curves["soft"][-1] < 5 and curves["hard"][-1] < 10, f"Both target networks should end close to the true values; got {curves['soft'][-1]:.2f} (soft) and {curves['hard'][-1]:.2f} (hard).")
    passed(LAB, "C", "Part C: without a target network the values ran away; with either kind they converged.")
