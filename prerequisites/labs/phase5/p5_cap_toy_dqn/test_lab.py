"""Checks for the Phase 5 capstone, one group per stage. Given code: nothing to edit here."""

import copy
import pathlib
import sys

import numpy as np
import pytest
import torch

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "labs" / "labkit").exists())))

import toy_dqn as td  # noqa: E402
from labs.labkit import memory as memories  # noqa: E402
from labs.labkit import toyrace as tr  # noqa: E402
from labs.labkit.toyrace import A, B, PIT_A, PIT_B, STAY_OUT  # noqa: E402

QUIET = tr.RaceModel(sc_hazard=0.0)  # no safety car: every race is the same race


class Fixed(torch.nn.Module):
    """A stand-in network that outputs the same rows whatever it is given."""

    def __init__(self, rows):
        super().__init__()
        self.rows = torch.tensor(rows, dtype=torch.float32)
        self.dummy = torch.nn.Parameter(torch.zeros(1))

    def forward(self, obs):
        return self.rows[: len(obs)] + 0 * self.dummy


# ---------------------------------------------------------------- stage 1: the observation


def test_stage1_encode():
    obs = td.encode(1, A, 1, 0, False)
    assert isinstance(obs, np.ndarray) and obs.dtype == np.float32 and obs.shape == (5,), "encode returns a float32 array of 5 numbers."
    assert np.allclose(obs, [1.0, 0.05, 0.0, 0.0, 0.0]), f"Lap 1 of 20 on a new compound A: [20/20, 1/20, 0, 0, 0]. Got {obs.tolist()}."
    assert np.allclose(td.encode(15, B, 6, 1, True), [6 / 20, 6 / 20, 1.0, 1.0, 1.0]), "Lap 15 has 6 laps left including itself."
    assert td.encode(21, A, 3, 0, True)[0] == 0.0, "After the last lap there are 0 laps left."


def test_stage1_legal_mask():
    m = td.legal_mask(QUIET, 5, A, False)
    assert m.dtype == bool and m.shape == (3,), "legal_mask returns a bool array of 3."
    assert m.tolist() == [True, False, True], "On compound A, PIT_A is illegal (no stop for the compound already fitted)."
    assert td.legal_mask(QUIET, 19, A, False).tolist() == [False, False, True], "With one lap left after this one and only one compound used, STAY_OUT is illegal."
    assert td.legal_mask(QUIET, 21, B, True).tolist() == [True, False, False], "After the race only STAY_OUT is legal."


# ---------------------------------------------------------------- stage 2: the networks


def test_stage2_qnet_shape():
    torch.manual_seed(0)
    q = td.QNet()(torch.rand(7, 5))
    assert q.shape == (7, 3), f"A batch of 7 observations gives Q of shape (7, 3); got {tuple(q.shape)}."


def test_stage2_two_heads():
    torch.manual_seed(0)
    net = td.TwoHeadNet(width=16)
    assert net.value_head.out_features == 1 and net.advantage_head.out_features == 3, "One value, one advantage per action."
    obs = torch.rand(6, 5)
    h = net.body(obs)
    value, adv = net.value_head(h), net.advantage_head(h)
    assert torch.allclose(net(obs), value + adv - adv.mean(dim=-1, keepdim=True), atol=1e-6), "forward is value + advantage - the row's mean advantage (page 05)."


# ---------------------------------------------------------------- stage 3: choosing


def test_stage3_greedy_respects_the_mask():
    net = Fixed([[5.0, 9.0, 1.0]])
    rng = np.random.default_rng(0)
    obs = np.zeros(5, dtype=np.float32)
    picks = {td.choose(net, obs, np.array([True, False, True]), 0.0, rng) for _ in range(50)}
    assert picks == {0}, f"With epsilon 0 the choice is the best LEGAL action, 0. Action 1 is higher and illegal. Got {picks}."


def test_stage3_exploration_stays_legal_and_uniform():
    net = Fixed([[5.0, 9.0, 1.0]])
    rng = np.random.default_rng(0)
    obs = np.zeros(5, dtype=np.float32)
    picks = [td.choose(net, obs, np.array([False, True, True]), 1.0, rng) for _ in range(2000)]
    assert 0 not in picks, "Exploration must stay inside the legal actions."
    assert abs(picks.count(2) / 2000 - 0.5) < 0.05, "At epsilon 1 each legal action is picked about equally often."


# ---------------------------------------------------------------- stage 4: targets


def page_06_batch():
    online = Fixed([[-40, -38, -45], [-30, -22, -35], [-9, -7, -8]])
    target = Fixed([[-41, -42, -44], [-31, -20, -36], [-9, -6, -8]])
    rewards = torch.tensor([-5.0, -6.0, -4.0])
    dones = torch.tensor([0.0, 0.0, 1.0])
    masks = torch.tensor([[True, True, True], [True, False, True], [True, True, True]])
    return rewards, dones, torch.zeros(3, 5), masks, online, target


def test_stage4_double_targets_page_06():
    got = td.td_targets(*page_06_batch(), double=True)
    assert got.shape == (3,), "One target per row."
    assert torch.allclose(got, torch.tensor([-47.0, -37.0, -4.0])), f"Page 06's batch gives [-47, -37, -4]. Got {got.tolist()}."


def test_stage4_vanilla_targets():
    got = td.td_targets(*page_06_batch(), double=False)
    assert torch.allclose(got, torch.tensor([-46.0, -37.0, -4.0])), f"With the target network choosing and scoring (masked max): [-46, -37, -4]. Got {got.tolist()}."


def test_stage4_no_gradient_through_targets():
    online, target = td.QNet(), td.QNet()
    got = td.td_targets(torch.zeros(4), torch.zeros(4), torch.rand(4, 5), torch.ones(4, 3, dtype=torch.bool), online, target)
    assert not got.requires_grad, "Targets are fixed numbers: compute them inside torch.no_grad()."


def test_stage4_cutoff_switch():
    got = td.td_targets(*page_06_batch(), double=True, cutoff=False)
    assert torch.allclose(got[:2], torch.tensor([-47.0, -37.0])), "cutoff=False changes nothing on rows that are not terminal."
    assert torch.isclose(got[2], torch.tensor(-10.0)), (
        f"With cutoff=False the terminal row bootstraps anyway: -4 + Q_target(s', a*) = -4 + (-6) = -10. Got {got[2].item()}."
    )


# ---------------------------------------------------------------- stage 5: one update


def filled_learner(**kw):
    learner = td.NetLearner(seed=0, warmup=10, batch=8, **kw)
    rng = np.random.default_rng(0)
    for _ in range(40):
        obs = rng.random(5).astype(np.float32)
        learner.remember((obs, int(rng.integers(3)), float(-rng.random() * 3), rng.random(5).astype(np.float32), float(rng.random() < 0.1), np.array([True, True, False])))
    return learner


def test_stage5_warmup_gate():
    learner = td.NetLearner(seed=0, warmup=10)
    learner.remember((np.zeros(5, np.float32), 0, -1.0, np.zeros(5, np.float32), 0.0, np.ones(3, bool)))
    assert learner.update() is None, "With fewer transitions than warmup, update does nothing and returns None."


def test_stage5_update_trains_online_and_follows_with_target():
    learner = filled_learner(tau=0.1)
    online_before = [p.detach().clone() for p in learner.online.parameters()]
    target_before = [p.detach().clone() for p in learner.target.parameters()]
    loss = learner.update()
    assert isinstance(loss, float), "update returns the loss as a plain float."
    assert learner.updates == 1, "update counts itself."
    online_after = list(learner.online.parameters())
    assert any(not torch.equal(a, b) for a, b in zip(online_after, online_before)), "The online network should have taken an optimizer step."
    for t, tb, o in zip(learner.target.parameters(), target_before, online_after):
        assert torch.allclose(t, 0.9 * tb + 0.1 * o.detach(), atol=1e-6), "After the step, every target weight moves a fraction tau toward the online weight."
        assert t.grad is None, "The target network never receives a gradient."


class FirstEight(memories.UniformMemory):
    """Always hands back the first 8 transitions, with fixed weights, so the loss can be recomputed."""

    WEIGHTS = np.array([1.0, 0.5, 0.25, 1.0, 0.0, 1.0, 0.75, 1.0])

    def sample(self, n):
        return self.items[:8], np.arange(8), self.WEIGHTS


def test_stage5_loss_is_weighted_huber():
    learner = filled_learner(memory=FirstEight(100, seed=0))
    online, target = copy.deepcopy(learner.online), copy.deepcopy(learner.target)
    obs, actions, rewards, next_obs, dones, masks = td.stack(learner.memory.items[:8])
    guess = online(obs).gather(1, actions.unsqueeze(1)).squeeze(1)
    with torch.no_grad():
        chosen = online(next_obs).masked_fill(~masks, -torch.inf).argmax(dim=1)
        goal = rewards + target(next_obs).gather(1, chosen.unsqueeze(1)).squeeze(1) * (1 - dones)
    per_row = torch.nn.functional.smooth_l1_loss(guess, goal, reduction="none").detach()
    want = float((torch.as_tensor(FirstEight.WEIGHTS, dtype=torch.float32) * per_row).mean())
    got = learner.update()
    assert got == pytest.approx(want, rel=1e-5), (
        f"Expected the weighted Huber loss {want:.5f}, got {got:.5f}. The order is: Huber per row (reduction='none'), times the row's weight, then the mean."
    )


def test_stage5_weights_scale_each_row():
    class OneRow(memories.UniformMemory):
        def sample(self, n):
            items, idx, _ = super().sample(2)
            return items, idx, np.array([0.0, 0.0])

    learner = filled_learner(memory=OneRow(100, seed=0))
    before = [p.detach().clone() for p in learner.online.parameters()]
    loss = learner.update()
    assert loss == pytest.approx(0.0), "With every weight 0 the weighted loss is 0: multiply each row's Huber loss by its weight, then take the mean."
    assert all(torch.allclose(a, b) for a, b in zip(learner.online.parameters(), before)), "A zero loss must not move the network."


def test_stage5_priorities_written_back():
    seen = {}

    class Spy(memories.UniformMemory):
        def update_priorities(self, indices, td_errors):
            seen["n"], seen["errors"] = len(indices), np.asarray(td_errors)

    learner = filled_learner(memory=Spy(100, seed=0))
    learner.update()
    assert seen.get("n") == 8, "update should hand one TD error per sampled row back to memory.update_priorities."
    assert seen["errors"].shape == (8,) and np.all(np.isfinite(seen["errors"])), "The TD errors go back as a NumPy array of 8 finite numbers."


def test_stage5_clipping(monkeypatch):
    learner = filled_learner(clip=3.0)
    before = [p.detach().clone() for p in learner.online.parameters()]
    calls = []
    real = torch.nn.utils.clip_grad_norm_

    def spy(params, max_norm, *args, **kwargs):
        params = list(params)
        calls.append({
            "max_norm": max_norm,
            "has_grads": all(p.grad is not None for p in params),
            "not_stepped": all(torch.equal(p.detach(), b) for p, b in zip(params, before)),
            "online": len(params) == len(before),
        })
        return real(params, max_norm, *args, **kwargs)

    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", spy)
    learner.update()
    assert len(calls) == 1, "Call nn.utils.clip_grad_norm_ once per update."
    c = calls[0]
    assert c["max_norm"] == 3.0, "Clip to self.clip."
    assert c["online"], "Clip the online network's parameters."
    assert c["has_grads"] and c["not_stepped"], "The clip goes between backward() and step(): after the gradients exist, before they are used."


# ---------------------------------------------------------------- stage 6: the race


class Recorder:
    """A learner that always stays out unless forced, and records what it is given."""

    def __init__(self):
        self.seen, self.updates = [], 0

    def act(self, obs, mask, epsilon=0.0):
        return STAY_OUT if mask[STAY_OUT] else int(np.flatnonzero(mask)[-1])

    def remember(self, transition):
        self.seen.append(transition)

    def update(self):
        self.updates += 1


def test_stage6_race_time_and_actions():
    rec = Recorder()
    out = td.run_race(rec, QUIET, np.random.default_rng(0), train=False)
    want = tr.simulate(QUIET, lambda lap, c, age, sc, used, w: PIT_B if lap == 19 else STAY_OUT, np.random.default_rng(0))
    assert out["actions"] == want["actions"], f"Staying out until forced: a stop on lap 19. Got {out['actions']}."
    assert out["time"] == pytest.approx(want["time"]), f"The race time should be the sum of model.cost over the laps: {want['time']:.2f}. Got {out['time']:.2f}."
    assert rec.seen == [] and rec.updates == 0, "With train=False nothing is remembered and nothing is updated."


def test_stage6_transitions():
    rec = Recorder()
    out = td.run_race(rec, QUIET, np.random.default_rng(0), train=True)
    assert len(rec.seen) == 20 and rec.updates == 20, "One transition and one update per lap."
    obs, action, reward, next_obs, done, next_mask = rec.seen[0]
    assert np.allclose(obs, td.encode(1, A, 1, 0, False)) and np.allclose(next_obs, td.encode(2, A, 2, 0, False)), "Lap 1's transition goes from lap 1 to lap 2 on the same tyre."
    assert reward == pytest.approx(-(QUIET.cost(1, A, 1, STAY_OUT) - td.BASE_LAP)), "The stored reward is minus the lap time, centred by the offset."
    assert [t[4] for t in rec.seen] == [0.0] * 19 + [1.0], "done is 1.0 on the last lap only."
    _, act18, _, nxt18, _, mask18 = rec.seen[18]
    assert act18 == PIT_B and np.allclose(nxt18, td.encode(20, B, 1, 0, True)), "The pit on lap 19 means lap 20 is driven on a new compound B, age 1, with both compounds used."
    assert mask18.tolist() == td.legal_mask(QUIET, 20, B, True).tolist(), "Each transition stores the NEXT state's legal mask."
    assert sum(t[2] for t in rec.seen) == pytest.approx(-(out["time"] - 20 * td.BASE_LAP)), "The rewards add up to minus the centred race time."


def test_stage6_offset_changes_only_the_rewards():
    a, b = Recorder(), Recorder()
    ta = td.run_race(a, QUIET, np.random.default_rng(0), offset=0.0)["time"]
    tb = td.run_race(b, QUIET, np.random.default_rng(0), offset=10.0)["time"]
    assert ta == pytest.approx(tb), "The reported time is the true one, whatever the offset."
    assert a.seen[0][2] == pytest.approx(b.seen[0][2] - 10.0), "offset is subtracted from every lap time before it becomes a reward."


def test_stage6_safety_car_follows_the_model():
    model = tr.RaceModel(sc_hazard=1.0, sc_continue=1.0)
    rec = Recorder()
    td.run_race(rec, model, np.random.default_rng(0))
    assert rec.seen[0][0][4] == 0.0 and all(t[3][4] == 1.0 for t in rec.seen), "With a hazard of 1 the safety car is out from lap 2 on, and the observation says so."


# ---------------------------------------------------------------- stage 7: it learns


@pytest.fixture(scope="module")
def trained():
    learner = td.NetLearner(seed=0)
    td.train(learner, QUIET, 600, seed=0)
    return learner


def test_stage7_closes_the_gap(trained):
    gap = td.gap_to_optimum(trained, QUIET)
    assert gap < 6.0, (
        f"After 600 races the greedy policy should be within 6 s of the exact optimum (an untrained network is 38.5 s off); it is {gap:.2f} s off. "
        "If stages 1-6 are green, check that update() is reached during training and that the reward is minus the lap time."
    )


def test_stage7_values_are_at_the_right_scale(trained):
    q = trained.values(td.encode(1, A, 1, 0, False))
    best = tr.solve(QUIET)[0][(1, A, 1, 0, False, tr.DRY)] - 20 * td.BASE_LAP
    assert abs(q.max() - (-best)) < 6.0, f"At the start the best Q-value should be within 6 of minus the centred optimum, {-best:.1f}. Got {q.max():.1f}."
