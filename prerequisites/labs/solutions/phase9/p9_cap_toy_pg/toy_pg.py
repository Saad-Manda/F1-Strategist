"""Lab p9-cap · Policy gradient on the toy race.

Page 09 is the brief. You build, in seven checked stages, a policy-gradient learner for the quiet
toy race (no safety car, dry): a table policy, REINFORCE, GAE and a critic, the destructive update,
the clip that stops it, a small PPO, and the clip's real job at ten epochs per batch.

THE POLICY. A table: for every state (lap, compound, tyre age, used both) a row of three logits,
one per action (STAY_OUT, PIT_A, PIT_B). Probabilities are a softmax over the LEGAL actions only;
an illegal action has probability 0. `theta` is a dict from state to its row; rows start at 0.

THE REWARD of a lap is -(lap time - 10): centred, as Finding C and lab p9-02 part D require.

THE RULER. `gap(theta)` evaluates the greedy policy exactly with toyrace.expected_time and
subtracts the optimum (224.49 s). 0.00 means optimal. A uniformly random policy is 43.45 s away.

What is given: the race loop, the training loops, and the ruler. What you write: the functions
with a TODO. The given loops call them in exactly the order the reference in labs/labkit/minipg.py
does, so a correct solution reproduces the reference's numbers.

Check one stage at a time:  python -m labs check p9-cap 1   (then 2, 3, ...)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from labs.labkit import toyrace as tr
from labs.labkit.racegym import QUIET, legal_mask, optimum

N_ACTIONS = 3
OFFSET = tr.BASE_LAP


# ============================================================================ Stage 1: the policy


def masked_probs(logits: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Softmax over the legal actions (mask True). Illegal actions get exactly 0.

    Subtract the largest LEGAL logit before exponentiating.
    """
    # >>> SOLUTION: set illegal logits to -inf, subtract the largest legal one, exponentiate, normalise
    z = np.where(mask, logits, -np.inf)
    z = z - z[mask].max()
    p = np.exp(z)
    return p / p.sum()
    # <<< SOLUTION


def log_grad(logits: np.ndarray, mask: np.ndarray, action: int) -> np.ndarray:
    """d log pi(action) / d logits: one-hot(action) minus the probabilities, and 0 on illegal actions."""
    # >>> SOLUTION: -masked_probs, plus 1 at action, then zero where the mask is False
    g = -masked_probs(logits, mask)
    g[action] += 1.0
    return np.where(mask, g, 0.0)
    # <<< SOLUTION


# ============================================================================ Given: one race


@dataclass
class Race:
    keys: list = field(default_factory=list)
    masks: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    rewards: list = field(default_factory=list)
    p_taken: list = field(default_factory=list)
    time: float = 0.0


def row(theta: dict, key) -> np.ndarray:
    if key not in theta:
        theta[key] = np.zeros(N_ACTIONS)
    return theta[key]


def run_race(theta: dict, rng: np.random.Generator, model: tr.RaceModel = QUIET) -> Race:
    """Sample one race from the table policy. Given."""
    race = Race()
    lap, compound, age, used = 1, tr.A, 1, False
    while lap <= model.horizon:
        key = (lap, compound, age, used)
        mask = legal_mask(model, lap, compound, used)
        p = masked_probs(row(theta, key), mask)
        action = int(rng.choice(N_ACTIONS, p=p))
        lap_time = model.cost(lap, compound, age, action, tr.DRY, 0)
        race.keys.append(key)
        race.masks.append(mask)
        race.actions.append(action)
        race.rewards.append(-(lap_time - OFFSET))
        race.p_taken.append(float(p[action]))
        race.time += lap_time
        new_compound, age = model.next_tyre(compound, age, action)
        used = used or new_compound != compound
        compound = new_compound
        lap += 1
    return race


def returns_to_go(rewards) -> np.ndarray:
    return np.cumsum(np.asarray(rewards, dtype=float)[::-1])[::-1]


# ============================================================================ Stage 2: REINFORCE


def reinforce_update(theta: dict, race: Race, alpha: float, sign: float = 1.0) -> None:
    """Page 01's update, lap by lap, in place: theta[key] += sign * alpha * G_t * log_grad.

    G_t is the return from lap t to the end of the race (returns_to_go). `sign` exists only so the
    tests can plant a sign error; leave it as a factor.
    """
    G = returns_to_go(race.rewards)
    for key, mask, action, g in zip(race.keys, race.masks, race.actions, G):
        # >>> SOLUTION: theta[key] = theta[key] + sign * alpha * g * log_grad(theta[key], mask, action)
        theta[key] = theta[key] + sign * alpha * g * log_grad(theta[key], mask, action)
        # <<< SOLUTION


def train_reinforce(races: int, seed: int = 0, alpha: float = 0.01, sign: float = 1.0) -> dict:
    """Given: `races` races of REINFORCE. Returns theta."""
    rng = np.random.default_rng(seed)
    theta: dict = {}
    for _ in range(races):
        reinforce_update(theta, run_race(theta, rng), alpha, sign)
    return theta


# ============================================================================ Stage 3: GAE and the critic


def gae(rewards, values, lam: float, gamma: float = 1.0) -> np.ndarray:
    """GAE advantages for ONE complete race (page 03). The step after the last lap is terminal: V = 0."""
    # >>> SOLUTION: backward pass: delta_t = r_t + gamma * V_{t+1} - V_t (V after the last lap is 0); A_t = delta_t + gamma * lam * A_{t+1}
    values = list(values) + [0.0]
    adv, run = np.zeros(len(rewards)), 0.0
    for t in reversed(range(len(rewards))):
        delta = rewards[t] + gamma * values[t + 1] - values[t]
        run = delta + gamma * lam * run
        adv[t] = run
    return adv
    # <<< SOLUTION


def critic_update(V: dict, key, target: float, lr: float) -> None:
    """Move V[key] (0 if never seen) a fraction lr of the way towards target, in place."""
    # >>> SOLUTION: V[key] = V.get(key, 0.0) + lr * (target - V.get(key, 0.0))
    V[key] = V.get(key, 0.0) + lr * (target - V.get(key, 0.0))
    # <<< SOLUTION


# ============================================================================ Stage 4: the destructive update


def destructive_step(logits, mask, action, advantage: float, step: float) -> np.ndarray:
    """One plain policy-gradient step, no clip: logits + step * advantage * log_grad. Returns new logits."""
    # >>> SOLUTION: one line
    return logits + step * advantage * log_grad(logits, mask, action)
    # <<< SOLUTION


# ============================================================================ Stage 5: the clip


def clipped_step(logits, mask, action, advantage: float, p_old: float, eps: float, step: float, clip: bool = True) -> np.ndarray:
    """One step on page 04's clipped objective for one sample. Returns new logits.

    ratio = pi(action) / p_old, with pi from the CURRENT logits and p_old frozen when the race was run.
    The gradient of min(ratio * A, clip(ratio, 1-eps, 1+eps) * A) with respect to the logits is
        ratio * A * log_grad      while the unclipped term is the smaller one,
        0                         once the clip binds: A > 0 and ratio >= 1 + eps, or A < 0 and ratio <= 1 - eps.
    Take a step of size `step` along it. With clip=False, never stop (the "noclip" learner).
    """
    # >>> SOLUTION: compute ratio; if clip and the clip binds, return logits unchanged; else logits + step * ratio * advantage * log_grad
    ratio = masked_probs(logits, mask)[action] / p_old
    if clip and ((advantage > 0 and ratio >= 1 + eps) or (advantage < 0 and ratio <= 1 - eps)):
        return logits
    return logits + step * ratio * advantage * log_grad(logits, mask, action)
    # <<< SOLUTION


# ============================================================================ Stage 6: a small PPO


def ppo_update(theta: dict, V: dict, batch: list, rng: np.random.Generator, alpha: float, v_lr: float,
               eps: float, epochs: int, clip: bool = True) -> None:
    """Page 04 and 05's update over one batch. Each entry of `batch` is a dict with
    key, mask, action, p_old, adv (GAE advantage), ret (adv + V at collection time).

    1. Standardise the batch's advantages: (adv - mean) / (std + 1e-8)   (page 05)
    2. For each of `epochs` epochs, visit the samples in the order rng.permutation(len(batch)), and for each:
         theta[key] = clipped_step(theta[key], mask, action, standardised adv, p_old, eps, alpha, clip)
         critic_update(V, key, ret, v_lr)
    Use p_old as stored in the batch: the probability under the policy that RAN the race.
    """
    advs = np.array([b["adv"] for b in batch])
    # >>> SOLUTION: standardise; then the epoch loop of step 2
    used = (advs - advs.mean()) / (advs.std() + 1e-8)
    for _ in range(epochs):
        for i in rng.permutation(len(batch)):
            b = batch[i]
            theta[b["key"]] = clipped_step(row(theta, b["key"]), b["mask"], b["action"], used[i], b["p_old"], eps, alpha, clip)
            critic_update(V, b["key"], b["ret"], v_lr)
    # <<< SOLUTION


def train_ppo(races: int, seed: int = 0, alpha: float = 0.2, v_lr: float = 0.1, eps: float = 0.2, epochs: int = 4,
              batch_races: int = 10, lam: float = 0.95, clip: bool = True) -> dict:
    """Given: collect `batch_races` races, compute GAE with the critic, run ppo_update, repeat. Returns theta."""
    rng = np.random.default_rng(seed)
    theta: dict = {}
    V: dict = {}
    batch: list = []
    for _ in range(races):
        race = run_race(theta, rng)
        values = [V.get(k, 0.0) for k in race.keys]
        adv = gae(race.rewards, values, lam)
        for key, mask, action, p_old, a, v in zip(race.keys, race.masks, race.actions, race.p_taken, adv, values):
            batch.append({"key": key, "mask": mask, "action": action, "p_old": p_old, "adv": a, "ret": a + v})
        if len(batch) >= batch_races * QUIET.horizon:
            ppo_update(theta, V, batch, rng, alpha, v_lr, eps, epochs, clip)
            batch = []
    return theta


# ============================================================================ Given: the ruler


def greedy_policy(theta: dict, model: tr.RaceModel = QUIET):
    def policy(lap, compound, age, sc, used_both, weather):
        mask = legal_mask(model, lap, compound, used_both)
        return int(np.argmax(masked_probs(theta.get((lap, compound, age, used_both), np.zeros(N_ACTIONS)), mask)))

    return policy


def gap(theta: dict, model: tr.RaceModel = QUIET) -> float:
    """Exact expected race time of the greedy policy minus the optimum, in seconds. Given."""
    return tr.expected_time(model, greedy_policy(theta, model)) - optimum(model)
