"""Reference policy-gradient learners for the quiet toy race. Given code.

A policy here is a table: for every state (lap, compound, tyre age, used both) a row of three
logits, turned into probabilities by a softmax over the legal actions only. Four learners share
it, each a few lines away from the last, which is the Phase 9 pages in order:

    "reinforce"   page 01: after each race, push every lap's logits by G_t times the log-gradient
    "ac"          page 02: the same, with G_t - V(s) and a learned table V
    "ppo"         pages 03-04: GAE advantages, batches of races, several epochs, the clip,
                  advantages standardised per batch (page 05)
    "noclip"      "ppo" without the clip

`train(..., bug=...)` plants one of page 05's quiet bugs, or one loud one (lab p9-05):

    "sign"        the advantage's sign is flipped                     (loud)
    "stale_old"   the old probability is re-read from the current policy every epoch (quiet)
    "gae_next"    the TD residual bootstraps from V(s_t) instead of V(s_t+1)        (quiet)
    "no_norm"     advantages are used without standardising them                   (quiet)

Every learner is scored exactly: `gap(theta)` evaluates its greedy policy with
`toyrace.expected_time` and subtracts the optimum, so the number has no sampling noise.

Labs import this; nothing in this file is a TODO. The p9-cap capstone has you write the same
pieces yourself.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import toyrace as tr
from .racegym import QUIET, legal_mask, optimum

N_ACTIONS = 3
OFFSET = tr.BASE_LAP  # reward = -(lap time - OFFSET): centred near zero
DEFAULT_ALPHA = {"reinforce": 0.01, "ac": 0.05, "ppo": 0.2, "noclip": 0.2}
BUGS = (None, "sign", "stale_old", "gae_next", "no_norm")


# ------------------------------------------------------------------------------- the policy


def probs(logits: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Softmax over the legal actions; illegal actions get probability 0."""
    z = np.where(mask, logits, -np.inf)
    z = z - z[mask].max()
    p = np.exp(z)
    return p / p.sum()


def log_grad(logits: np.ndarray, mask: np.ndarray, action: int) -> np.ndarray:
    """d log pi(action) / d logits: one-hot(action) - pi, and 0 on illegal actions."""
    g = -probs(logits, mask)
    g[action] += 1.0
    return np.where(mask, g, 0.0)


def entropy(p: np.ndarray) -> float:
    q = p[p > 0]
    return float(-(q * np.log(q)).sum())


def entropy_grad(logits: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """d H / d logits for H = -sum p log p over the legal actions: -p_j (log p_j + H)."""
    p = probs(logits, mask)
    with np.errstate(divide="ignore"):
        logp = np.where(p > 0, np.log(np.where(p > 0, p, 1.0)), 0.0)
    h = -(p * logp).sum()
    return np.where(mask, -p * (logp + h), 0.0)


# --------------------------------------------------------------------------------- one race


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


def run_race(theta: dict, rng: np.random.Generator, model: tr.RaceModel = QUIET, offset: float = OFFSET) -> Race:
    """One race sampled from the table policy. Rewards are -(lap time - offset)."""
    race = Race()
    lap, compound, age, used = 1, tr.A, 1, False
    while lap <= model.horizon:
        key = (lap, compound, age, used)
        mask = legal_mask(model, lap, compound, used)
        p = probs(row(theta, key), mask)
        action = int(rng.choice(N_ACTIONS, p=p))
        lap_time = model.cost(lap, compound, age, action, tr.DRY, 0)
        race.keys.append(key)
        race.masks.append(mask)
        race.actions.append(action)
        race.rewards.append(-(lap_time - offset))
        race.p_taken.append(float(p[action]))
        race.time += lap_time
        new_compound, age = model.next_tyre(compound, age, action)
        used = used or new_compound != compound
        compound = new_compound
        lap += 1
    return race


def returns_to_go(rewards) -> np.ndarray:
    return np.cumsum(np.asarray(rewards, dtype=float)[::-1])[::-1]


def gae(rewards, values, lam: float, gamma: float = 1.0) -> np.ndarray:
    """GAE advantages for one complete episode (the step after the last is terminal, value 0)."""
    values = list(values) + [0.0]
    adv, run = np.zeros(len(rewards)), 0.0
    for t in reversed(range(len(rewards))):
        delta = rewards[t] + gamma * values[t + 1] - values[t]
        run = delta + gamma * lam * run
        adv[t] = run
    return adv


def gae_bootstrapping_from_the_wrong_state(rewards, values, lam: float, gamma: float = 1.0) -> np.ndarray:
    """The planted "gae_next" bug: delta_t = r_t + gamma V(s_t) - V(s_t)."""
    values = list(values)
    adv, run = np.zeros(len(rewards)), 0.0
    for t in reversed(range(len(rewards))):
        delta = rewards[t] + gamma * values[t] - values[t]
        run = delta + gamma * lam * run
        adv[t] = run
    return adv


def advantage_fn(bug=None):
    """The advantage estimator a learner with `bug` uses."""
    return gae_bootstrapping_from_the_wrong_state if bug == "gae_next" else gae


# ----------------------------------------------------------------------------- the learners


@dataclass
class Result:
    theta: dict
    V: dict
    times: list = field(default_factory=list)  # each training race's time
    entropy: list = field(default_factory=list)  # mean policy entropy over each race's laps
    max_ratio: list = field(default_factory=list)  # PPO only: largest ratio seen in each update
    trace: dict | None = None  # inspect=True: the last update's internals
    curve: list = field(default_factory=list)  # checkpoint_every=n: (environment steps so far, exact gap)


def _ppo_update(buf, theta, V, *, alpha, v_lr, eps, epochs, clip, bug, ent_coef, rng, trace):
    advs = np.array([b["adv"] for b in buf])
    used = advs if bug == "no_norm" else (advs - advs.mean()) / (advs.std() + 1e-8)
    if bug == "sign":
        used = -used
    ratios_by_epoch, largest = [], 0.0
    for _ in range(epochs):
        ratios = np.empty(len(buf))
        for i in rng.permutation(len(buf)):
            b = buf[i]
            logits = row(theta, b["key"])
            p = probs(logits, b["mask"])
            p_old = p[b["action"]] if bug == "stale_old" else b["p_old"]
            ratio = p[b["action"]] / p_old
            ratios[i] = ratio
            a_i = used[i]
            active = (not clip) or (a_i > 0 and ratio < 1 + eps) or (a_i < 0 and ratio > 1 - eps)
            if active:
                logits += alpha * ratio * a_i * log_grad(logits, b["mask"], b["action"])
            if ent_coef:
                logits += alpha * ent_coef * entropy_grad(logits, b["mask"])
            V[b["key"]] = V.get(b["key"], 0.0) + v_lr * (b["ret"] - V.get(b["key"], 0.0))
        ratios_by_epoch.append(ratios)
        largest = max(largest, float(ratios.max()))
    if trace is not None:
        trace.update(ratios=ratios_by_epoch, used_advantages=used, raw_advantages=advs)
    return largest


def train(
    kind: str = "ppo",
    races: int = 2000,
    seed: int = 0,
    bug: str | None = None,
    alpha: float | None = None,
    ent_coef: float = 0.0,
    v_lr: float = 0.1,
    eps: float = 0.2,
    epochs: int = 4,
    batch: int = 10,
    lam: float = 0.95,
    model: tr.RaceModel = QUIET,
    offset: float = OFFSET,
    inspect: bool = False,
    checkpoint_every: int | None = None,
) -> Result:
    """Train one table learner for `races` races and return what it learned and how it went."""
    assert kind in DEFAULT_ALPHA, kind
    assert bug in BUGS, bug
    alpha = DEFAULT_ALPHA[kind] if alpha is None else alpha
    rng = np.random.default_rng(seed)
    res = Result(theta={}, V={})
    theta, V = res.theta, res.V
    estimate = advantage_fn(bug)
    buf = []
    for n in range(1, races + 1):
        if checkpoint_every and n > 1 and (n - 1) % checkpoint_every == 0:
            res.curve.append(((n - 1) * model.horizon, gap(theta, model)))
        race = run_race(theta, rng, model, offset)
        res.times.append(race.time)
        res.entropy.append(float(np.mean([entropy(probs(row(theta, k), m)) for k, m in zip(race.keys, race.masks)])))
        G = returns_to_go(race.rewards)
        if kind in ("reinforce", "ac"):
            for key, mask, action, g in zip(race.keys, race.masks, race.actions, G):
                logits = row(theta, key)
                weight = g if kind == "reinforce" else g - V.get(key, 0.0)
                logits += alpha * weight * log_grad(logits, mask, action)
                if ent_coef:
                    logits += alpha * ent_coef * entropy_grad(logits, mask)
                if kind == "ac":
                    V[key] = V.get(key, 0.0) + v_lr * (g - V.get(key, 0.0))
            continue
        values = [V.get(k, 0.0) for k in race.keys]
        adv = estimate(race.rewards, values, lam)
        if inspect and not buf:
            res.trace = {"rewards": list(race.rewards), "values": values, "advantage_fn": estimate}
        for key, mask, action, p_old, a, v in zip(race.keys, race.masks, race.actions, race.p_taken, adv, values):
            buf.append({"key": key, "mask": mask, "action": action, "p_old": p_old, "adv": a, "ret": a + v})
        if len(buf) >= batch * model.horizon:
            res.max_ratio.append(
                _ppo_update(buf, theta, V, alpha=alpha, v_lr=v_lr, eps=eps, epochs=epochs, clip=kind == "ppo", bug=bug,
                            ent_coef=ent_coef, rng=rng, trace=res.trace if inspect else None)
            )
            buf = []
    if checkpoint_every:
        res.curve.append((races * model.horizon, gap(theta, model)))
    return res


def inspect_update(bug: str | None = None, seed: int = 0, races: int = 200) -> dict:
    """Train a PPO learner briefly and return the internals of its last update (lab p9-05).

    Keys: "rewards" and "values" of the first race of that batch; "advantage_fn", the estimator
    the learner used; "ratios", one array per epoch; "raw_advantages"; "used_advantages", what was
    actually fed to the clipped update.
    """
    return train("ppo", races=races, seed=seed, bug=bug, inspect=True).trace


# ------------------------------------------------------------------------------- the ruler


def greedy_policy(theta: dict, model: tr.RaceModel = QUIET):
    def policy(lap, compound, age, sc, used_both, weather):
        mask = legal_mask(model, lap, compound, used_both)
        return int(np.argmax(probs(theta.get((lap, compound, age, used_both), np.zeros(N_ACTIONS)), mask)))

    return policy


def gap(theta: dict, model: tr.RaceModel = QUIET) -> float:
    """Exact expected race time of the greedy policy, minus the optimum, in seconds."""
    return tr.expected_time(model, greedy_policy(theta, model)) - optimum(model)


def uniform_gap(model: tr.RaceModel = QUIET) -> float:
    """The same for the uniformly random legal policy, evaluated exactly by averaging over actions."""
    H = model.horizon
    V = {}
    for state in sorted(tr.state_space(model), reverse=True):
        lap, c, age, sc, used, w = state
        if sc or w:
            continue
        legal = model.legal_actions(lap, c, tr.DRY, used)
        total = 0.0
        for action in legal:
            nc, nage = model.next_tyre(c, age, action)
            nused = used or nc != c
            nxt = 0.0 if lap == H else V[(lap + 1, nc, nage, nused)]
            total += model.cost(lap, c, age, action, tr.DRY, 0) + nxt
        V[(lap, c, age, used)] = total / len(legal)
    return V[(1, tr.A, 1, False)] - optimum(model)
