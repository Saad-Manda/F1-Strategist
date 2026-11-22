"""Phase 5 capstone: a network learner for the toy race, measured against the exact optimum.

The brief is page 09 of the Phase 5 set ("Build It Yourself"). There you build a toy DQN on a
12-lap stint. Here you build the same stack for the 20-lap race of the earlier capstones,
where the Phase 3.5 solver gives the exact answer and the Phase 4 capstone's table learner
gives something to beat.

    python -m labs check p5-cap 1      check one stage
    python -m labs check p5-cap        check everything (stage 7 trains for about 90 seconds)
    python -m labs hint  p5-cap        if you are stuck

THE RACE
--------
`model` is a labs.labkit.toyrace.RaceModel: 20 laps, compounds A = 0 and B = 1, actions
STAY_OUT = 0, PIT_A = 1, PIT_B = 2, weather always DRY. Phase 4's table learner used the state
tuple (lap, compound, age, sc, used_both) as a key. The network instead gets that state as
five numbers between 0 and 1 (stage 1), and nothing is binned.

A TRANSITION, as stored in memory, is the tuple
    (obs, action, reward, next_obs, done, next_mask)
with obs and next_obs float32 arrays of 5, and next_mask a bool array of 3: the legal actions
in the NEXT state. Page 06 explains why the mask travels with the transition.

The memories come from labs.labkit.memory, ready-made: UniformMemory (page 04) and
PriorityMemory (page 07). You built both yourself in labs p5-04 and p5-07.

Names here are deliberately not the real project's names.
"""

import copy

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from labs.labkit import memory as memories
from labs.labkit import toyrace as tr
from labs.labkit.toyrace import A, DRY, STAY_OUT  # noqa: F401

torch.set_num_threads(1)  # tiny networks run faster on one thread
N_OBS, N_ACTIONS = 5, 3
BASE_LAP = tr.BASE_LAP  # subtracting it from every lap time is "reward centring"

# ============================================================================ Stage 1


def encode(lap, compound, age, sc, used_both, horizon=tr.HORIZON):
    """The state as five numbers, a float32 array:

        [laps left including this one / horizon,  age / horizon,  compound,  used_both,  sc]

    `lap` runs from 1 to horizon. The state after the last lap (lap = horizon + 1) has 0 laps left.
    compound, used_both and sc are 0 or 1.
    """
    # >>> SOLUTION: np.array of the five numbers, dtype=np.float32
    return np.array([(horizon - lap + 1) / horizon, age / horizon, float(compound), float(used_both), float(sc)], dtype=np.float32)
    # <<< SOLUTION


def legal_mask(model, lap, compound, used_both):
    """A bool array of N_ACTIONS: True where the action is legal (model.legal_actions, weather DRY).

    After the race (lap > model.horizon) there is nothing to decide: only STAY_OUT is True.
    """
    # >>> SOLUTION: past the horizon only STAY_OUT; otherwise True at each action in model.legal_actions(lap, compound, DRY, used_both)
    mask = np.zeros(N_ACTIONS, dtype=bool)
    if lap > model.horizon:
        mask[STAY_OUT] = True
    else:
        mask[model.legal_actions(lap, compound, DRY, used_both)] = True
    return mask
    # <<< SOLUTION


# ============================================================================ Stage 2


class QNet(nn.Module):
    """One output head: Linear(N_OBS, width) -> ReLU -> Linear(width, width) -> ReLU -> Linear(width, N_ACTIONS)."""

    def __init__(self, width=64):
        super().__init__()
        # >>> SOLUTION: self.layers = the five-layer nn.Sequential above
        self.layers = nn.Sequential(nn.Linear(N_OBS, width), nn.ReLU(), nn.Linear(width, width), nn.ReLU(), nn.Linear(width, N_ACTIONS))
        # <<< SOLUTION

    def forward(self, obs):
        # >>> SOLUTION: run the layers
        return self.layers(obs)
        # <<< SOLUTION


class TwoHeadNet(nn.Module):
    """Page 05: a shared body (two Linear + ReLU layers), a value head of 1 and an advantage head of N_ACTIONS,
    combined as value + advantage - advantage.mean(dim=-1, keepdim=True)."""

    def __init__(self, width=64):
        super().__init__()
        # >>> SOLUTION: self.body, self.value_head, self.advantage_head
        self.body = nn.Sequential(nn.Linear(N_OBS, width), nn.ReLU(), nn.Linear(width, width), nn.ReLU())
        self.value_head = nn.Linear(width, 1)
        self.advantage_head = nn.Linear(width, N_ACTIONS)
        # <<< SOLUTION

    def forward(self, obs):
        # >>> SOLUTION: one pass through the body, both heads, the mean-subtracted combination
        h = self.body(obs)
        advantage = self.advantage_head(h)
        return self.value_head(h) + advantage - advantage.mean(dim=-1, keepdim=True)
        # <<< SOLUTION


# ============================================================================ Stage 3


def choose(net, obs, mask, epsilon, rng):
    """Masked ε-greedy with a network. Returns an int.

    Draw rng.random(). Below epsilon: a legal action chosen with rng.choice. Otherwise run the
    network on obs (inside torch.no_grad()), set illegal actions to -inf, and take the argmax.
    """
    # >>> SOLUTION: explore among np.flatnonzero(mask) when rng.random() < epsilon; otherwise the masked argmax of net(obs)
    if rng.random() < epsilon:
        return int(rng.choice(np.flatnonzero(mask)))
    with torch.no_grad():
        q = net(torch.as_tensor(obs).unsqueeze(0))[0].numpy().copy()
    q[~mask] = -np.inf
    return int(np.argmax(q))
    # <<< SOLUTION


# ============================================================================ Stage 4


def td_targets(rewards, dones, next_obs, next_masks, online, target, double=True, cutoff=True):
    """Page 06's targets for a batch, as a tensor of shape (B,). No gradient flows through them.

        rewards (B,) float, dones (B,) float 0/1, next_obs (B, N_OBS), next_masks (B, N_ACTIONS) bool

    double=True:  the online network chooses a* among legal actions, the target network scores it.
    double=False: the target network chooses and scores (a masked max).
    target = rewards + score * (1 - dones), with γ = 1.  cutoff=False drops the (1 - dones)
    factor: that is the planted bug of the report, never the default.
    """
    with torch.no_grad():
        # >>> SOLUTION: score = target's value at the online argmax (double) or the target's masked max; then the cut-off
        if double:
            chosen = online(next_obs).masked_fill(~next_masks, -torch.inf).argmax(dim=1)
            score = target(next_obs).gather(1, chosen.unsqueeze(1)).squeeze(1)
        else:
            score = target(next_obs).masked_fill(~next_masks, -torch.inf).max(dim=1).values
        return rewards + (score * (1.0 - dones) if cutoff else score)
        # <<< SOLUTION


# ============================================================================ Stage 5


def follow(target, online, tau):
    """Given. Page 03's soft update, every target weight a fraction tau toward the online weight."""
    with torch.no_grad():
        torch._foreach_lerp_(list(target.parameters()), list(online.parameters()), tau)


class LatestOnly:
    """Given. A 'memory' that holds only the newest transition: training on the stream, as it happens.
    Use it with warmup=1."""

    def __init__(self):
        self.item = None

    def push(self, item):
        self.item = item

    def sample(self, n):
        return [self.item], np.zeros(1, dtype=int), np.ones(1)

    def update_priorities(self, indices, td_errors):
        pass

    def __len__(self):
        return 0 if self.item is None else 1


def stack(items):
    """Given. A list of transitions -> tensors (obs, actions, rewards, next_obs, dones, next_masks)."""
    obs, actions, rewards, next_obs, dones, next_masks = zip(*items)
    return (
        torch.as_tensor(np.array(obs)),
        torch.as_tensor(np.array(actions), dtype=torch.int64),
        torch.as_tensor(np.array(rewards), dtype=torch.float32),
        torch.as_tensor(np.array(next_obs)),
        torch.as_tensor(np.array(dones), dtype=torch.float32),
        torch.as_tensor(np.array(next_masks)),
    )


class NetLearner:
    """The whole stack, with switches. The defaults are the full design: two heads, a target
    network, uniform replay, the decoupled target. Every switch is given; update() is yours."""

    def __init__(self, net_cls=TwoHeadNet, seed=0, memory=None, use_target=True, double=True, cutoff=True,
                 lr=1e-3, tau=0.01, batch=32, warmup=500, clip=10.0):
        torch.manual_seed(seed)
        self.rng = np.random.default_rng(seed)
        self.online = net_cls()
        self.target = copy.deepcopy(self.online) if use_target else self.online  # off: one network does both jobs
        self.optimizer = torch.optim.Adam(self.online.parameters(), lr=lr)
        self.memory = memory if memory is not None else memories.UniformMemory(20_000, seed)
        self.double, self.cutoff = double, cutoff
        self.tau, self.batch, self.warmup, self.clip = tau, batch, warmup, clip
        self.updates = 0

    def act(self, obs, mask, epsilon=0.0):
        return choose(self.online, obs, mask, epsilon, self.rng)

    def remember(self, transition):
        self.memory.push(transition)

    def update(self):
        """One training step. Returns the loss as a float, or None while the memory is warming up.

        In order:
        1. items, indices, weights = self.memory.sample(self.batch); then stack(items)
        2. guess: the online network's value of the action actually taken, row by row (gather)
        3. goal: td_targets(...) with self.double and self.cutoff
        4. loss: the Huber loss per row (F.smooth_l1_loss with reduction="none"), times each
           row's weight, then the mean
        5. zero_grad, backward, clip the online network's gradient norm to self.clip, step
        6. if self.target is not self.online: follow(self.target, self.online, self.tau)
        7. self.memory.update_priorities(indices, the TD errors goal - guess as a NumPy array)
        8. self.updates += 1, and return the loss
        """
        if len(self.memory) < max(1, self.warmup):
            return None
        # >>> SOLUTION: steps 1 to 8
        items, indices, weights = self.memory.sample(self.batch)
        obs, actions, rewards, next_obs, dones, next_masks = stack(items)
        guess = self.online(obs).gather(1, actions.unsqueeze(1)).squeeze(1)
        goal = td_targets(rewards, dones, next_obs, next_masks, self.online, self.target, self.double, self.cutoff)
        weights = torch.as_tensor(np.asarray(weights), dtype=torch.float32)
        loss = (weights * F.smooth_l1_loss(guess, goal, reduction="none")).mean()
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.online.parameters(), self.clip)
        self.optimizer.step()
        if self.target is not self.online:
            follow(self.target, self.online, self.tau)
        self.memory.update_priorities(indices, (goal - guess).detach().numpy())
        self.updates += 1
        return loss.item()
        # <<< SOLUTION

    def values(self, obs):
        """Given. The online network's Q-values for one observation, as a NumPy array."""
        with torch.no_grad():
            return self.online(torch.as_tensor(obs).unsqueeze(0))[0].numpy()


# ============================================================================ Stage 6


def run_race(learner, model, rng, epsilon=0.0, train=True, offset=BASE_LAP):
    """Drive one race. Returns {"time": total race time in seconds, "actions": [one per lap]}.

    The race starts on compound A, age 1, no safety car, both compounds not yet used. On every
    lap, in this order:
    1. obs = encode(...) and mask = legal_mask(...) for the current state
    2. action = learner.act(obs, mask, epsilon)
    3. lap_time = model.cost(lap, compound, age, action, DRY, sc), BEFORE the tyre changes
    4. the next state: model.next_tyre gives the next compound and age; used_both becomes True
       once the next compound differs from the current one; the next sc is 1 with probability
       model.sc_prob(sc), drawn with rng.random()
    5. if train: remember (obs, action, -(lap_time - offset), next_obs, done, next_mask) with
       done = 1.0 on the last lap and 0.0 otherwise, then call learner.update()

    The returned time is always the true one, the sum of lap_time. offset only changes what
    the learner trains on.
    """
    # >>> SOLUTION: keep compound, age, sc, used_both as locals and follow steps 1-5 for laps 1..model.horizon
    compound, age, sc, used_both = A, 1, 0, False
    total, actions = 0.0, []
    for lap in range(1, model.horizon + 1):
        obs = encode(lap, compound, age, sc, used_both, model.horizon)
        mask = legal_mask(model, lap, compound, used_both)
        action = learner.act(obs, mask, epsilon)
        lap_time = model.cost(lap, compound, age, action, DRY, sc)
        next_compound, next_age = model.next_tyre(compound, age, action)
        next_used = used_both or next_compound != compound
        next_sc = int(rng.random() < model.sc_prob(sc))
        if train:
            done = lap == model.horizon
            next_obs = encode(lap + 1, next_compound, next_age, next_sc, next_used, model.horizon)
            next_mask = legal_mask(model, lap + 1, next_compound, next_used)
            learner.remember((obs, action, -(lap_time - offset), next_obs, 1.0 if done else 0.0, next_mask))
            learner.update()
        total += lap_time
        actions.append(action)
        compound, age, sc, used_both = next_compound, next_age, next_sc, next_used
    return {"time": total, "actions": actions}
    # <<< SOLUTION


# ============================================================================ Given: training and measuring


def epsilon_at(race, races, start=1.0, end=0.05, decay_share=0.6):
    """Linear decay from start to end over the first decay_share of the races, then flat."""
    return max(end, start - (start - end) * race / (decay_share * races))


def train(learner, model, races, seed=0, offset=BASE_LAP):
    rng = np.random.default_rng(seed + 1000)
    for race in range(races):
        run_race(learner, model, rng, epsilon=epsilon_at(race, races), train=True, offset=offset)
    return learner


def greedy_policy(learner, model):
    """The learner's greedy choice, in the (lap, compound, age, sc, used_both, weather) form toyrace uses."""

    def policy(lap, compound, age, sc, used_both, weather):
        return learner.act(encode(lap, compound, age, sc, used_both, model.horizon), legal_mask(model, lap, compound, used_both), 0.0)

    return policy


def gap_to_optimum(learner, model):
    """Exact expected race time of the greedy policy minus the exact optimum, in seconds. No sampling noise."""
    best = tr.solve(model)[0][(1, A, 1, 0, False, DRY)]
    return tr.expected_time(model, greedy_policy(learner, model)) - best
