# %% [markdown]
# # Lab p9-02 · What a baseline buys
#
# **Goes with:** Phase 9, page 02 — Actor-critic and the advantage function · **Time:** about 20 minutes
#
# Page 02 makes two claims about subtracting a baseline b(s) from the return: the gradient's
# *average* does not change, and its *noise* can drop sharply. Here you measure both on p9-01's
# corridor, prove the first one exactly, then learn the baseline while training. Part D is the
# case that matters for this project, whose rewards are minus lap times: what happens when every
# reward sits far from zero.
#
# **Environments:** the short corridor from p9-01 (`labs/labkit/corridor.py`), and a two-armed
# bandit defined in Part D.
#
# Stuck? Run `python -m labs hint p9-02` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import corridor, predict

LAB = "p9-02"


def softmax(z):
    e = np.exp(z - np.max(z))
    return e / e.sum()


def log_softmax_grad(z, a):
    g = -softmax(z)
    g[a] += 1.0
    return g


# %% [markdown]
# ## Part A — same average, less noise
#
# **TODO 1.** `episode_gradient(theta, ep, b)`: p9-01's estimate with G_t − b in place of G_t.
# The cell then draws 4,000 episodes at two fixed values of θ and compares b = 0 with b = the
# exact value of the start cell.

# %%
def episode_gradient(theta, ep, b=0.0):
    """Σ_t (G_t − b) · ∂ log π(a_t) / ∂θ for one corridor episode played at theta."""
    p = corridor.p_right(theta)
    G = np.cumsum([r for _, _, r in ep][::-1])[::-1]
    # >>> SOLUTION: the p9-01 sum with (g - b) in place of g
    return float(sum(((1 - p) if a == corridor.RIGHT else -p) * (g - b) for (_, a, _), g in zip(ep, G)))
    # <<< SOLUTION


rng = np.random.default_rng(0)
stats = {}
for theta in (0.0, 0.4):
    v = corridor.true_value(corridor.p_right(theta))
    plain = [episode_gradient(theta, corridor.episode(theta, rng), 0.0) for _ in range(4000)]
    base = [episode_gradient(theta, corridor.episode(theta, rng), v) for _ in range(4000)]
    stats[theta] = dict(mean_plain=np.mean(plain), mean_base=np.mean(base), std_plain=np.std(plain), std_base=np.std(base),
                        se_plain=np.std(plain) / 63.25, se_base=np.std(base) / 63.25)
    print(f"θ = {theta}: b = 0      mean {np.mean(plain):6.2f}  std {np.std(plain):5.1f}")
    print(f"        b = V(start) mean {np.mean(base):6.2f}  std {np.std(base):5.1f}   (V = {v:.2f})")
checks.same_mean_less_noise(stats)

# %% [markdown]
# Every return here is negative: −8 for a quick finish, −30 for a slow one. Without a baseline
# every episode pushes the probability of *every* action it took down, by an amount that depends
# on how long the episode ran. The baseline turns that into "down if slower than usual, up if
# quicker", which is a smaller and more informative number.

# %% [markdown]
# ## Part B — the zero, exactly
#
# Page 02's proof says E_a[∇log π(a) · b] = b · Σ_a π(a) ∇log π(a) = b · ∇ Σ_a π(a) = 0.
#
# **TODO 2.** `baseline_term(z, b, ...)`: compute b · Σ_a π(a) ∇log π(a) exactly, by summing over
# the actions (no sampling). The check tries 200 random logit vectors and baselines.

# %%
def baseline_term(z, b, softmax, log_softmax_grad):
    """The expected contribution of a baseline b to the gradient, summed exactly over actions."""
    p = softmax(z)
    # >>> SOLUTION: sum over a of p[a] * log_softmax_grad(z, a) * b
    return sum(p[a] * log_softmax_grad(z, a) * b for a in range(len(z)))
    # <<< SOLUTION


checks.exactly_zero(baseline_term, softmax, log_softmax_grad)

# %% [markdown]
# ## Part C — learn the baseline as you go
#
# Nobody hands you V(start). Learn it: a single number w, moved a fraction β of the way towards
# every return seen. (One number is enough because the policy cannot tell the cells apart.)
#
# **TODO 3.** Finish `reinforce_with_baseline`. Both runs below use the same step size α = 2⁻⁹.

# %%
def reinforce_plain(alpha, episodes, seed, theta=-1.5):
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(episodes):
        ep = corridor.episode(theta, rng)
        theta += alpha * episode_gradient(theta, ep, 0.0)
        values.append(corridor.true_value(corridor.p_right(theta)))
    return np.array(values)


def reinforce_with_baseline(alpha, beta, episodes, seed, theta=-1.5):
    rng = np.random.default_rng(seed)
    w, values = 0.0, []
    for _ in range(episodes):
        ep = corridor.episode(theta, rng)
        p = corridor.p_right(theta)
        G = np.cumsum([r for _, _, r in ep][::-1])[::-1]
        g = 0.0
        for (_, a, _), g_t in zip(ep, G):
            dlog = (1 - p) if a == corridor.RIGHT else -p
            # >>> SOLUTION: add dlog * (g_t - w) to g, then move w towards g_t by beta
            g += dlog * (g_t - w)
            w += beta * (g_t - w)
            # <<< SOLUTION
        theta += alpha * g
        values.append(corridor.true_value(corridor.p_right(theta)))
    return np.array(values)


plain = np.array([reinforce_plain(2**-9, 1000, s) for s in range(20)])
base = np.array([reinforce_with_baseline(2**-9, 2**-6, 1000, s) for s in range(20)])
for runs, name in ((plain, "no baseline"), (base, "learned baseline")):
    m, sd = runs.mean(axis=0), runs.std(axis=0)
    plt.plot(m, label=name)
    plt.fill_between(range(1000), m - sd, m + sd, alpha=0.2)
plt.axhline(-11.657, color="k", ls="--", lw=1)
plt.ylim(-25, -11); plt.xlabel("episode"); plt.ylabel("start value (mean ± spread over 20 seeds)"); plt.legend(); plt.show()
checks.learned_baseline(plain, base)

# %% [markdown]
# On a problem this small both runs find the answer on average. The difference is how much luck
# is involved: the shaded band is the spread across seeds. The rest of this phase, and every
# library, uses a learned baseline: page 02's critic.

# %% [markdown]
# ## Part D — when rewards sit far from zero
#
# A two-armed bandit: arm R pays N(1, 2), arm P pays N(0, 0.5), so R is better on average. One
# step per episode, so G is just the reward. Then **add a constant c to every reward**. That
# changes nothing about which arm is better, and with one-step episodes it cannot change the
# optimal policy either.
#
# Predict: does the learned baseline matter at c = 0? At c = −10?

# %%
CHOICES = {
    "neither": "it hardly matters at either offset",
    "both": "it helps a lot at both",
    "offset": "it hardly matters at 0, and matters a lot at −10",
}
my_prediction = "offset"  # >>> ANSWER
predict.commit(LAB, "offset", my_prediction, CHOICES)

# %% [markdown]
# **TODO 4.** One update of the bandit learner. The baseline is learned in both runs; only the
# update decides whether it is used.

# %%
def bandit_run(offset, use_baseline, seed, episodes=500, alpha=0.05, critic_lr=0.1):
    rng = np.random.default_rng(seed)
    z, baseline = np.zeros(2), 0.0
    for _ in range(episodes):
        p = softmax(z)
        a = 0 if rng.random() < p[0] else 1  # 0 = R, 1 = P
        reward = (rng.normal(1.0, 2.0) if a == 0 else rng.normal(0.0, 0.5)) + offset
        grad = log_softmax_grad(z, a)
        # >>> SOLUTION: advantage = reward minus (baseline if used, else 0); step z; then update the baseline
        advantage = reward - (baseline if use_baseline else 0.0)
        z = z + alpha * advantage * grad
        baseline += critic_lr * (reward - baseline)
        # <<< SOLUTION
    return softmax(z)[0]


final = {}
for offset in (0.0, -10.0, -50.0):
    for use in (False, True):
        final[(offset, use)] = np.array([bandit_run(offset, use, s) for s in range(20)])
        print(f"offset {offset:6.1f}  baseline {'on ' if use else 'off'}:  final P(R) mean {final[(offset, use)].mean():.3f}, worst seed {final[(offset, use)].min():.3f}")
predict.reveal(LAB, "offset", "level at 0; at −10, some runs without the baseline end on the worse arm", correct="offset")
checks.offset_matters(final)

# %% [markdown]
# At c = −10 every reward is negative. Without a baseline, whichever arm is pulled gets pushed
# *down*, by about 10 per pull, and an early run of pulls on one arm can push it to near-zero
# probability before the difference of 1 between the arms shows. With the baseline, after a few
# pulls the update sees reward − 9, which is about ±1.
#
# At c = −50 even the baseline run struggles at first: it starts at 0 and needs a few dozen
# pulls to catch up with the scale, and those first updates are large. Starting the baseline at
# the first reward, or centring the reward in the first place, removes that too.
#
# This is the project's situation exactly. A lap reward is about −90 s, and the Phase 4/5 sets'
# reward centring (`reward_offset="base_pace"`, Finding C) is the fix, applied before any
# learner sees the reward. A critic is a second line of defence, not a replacement.
