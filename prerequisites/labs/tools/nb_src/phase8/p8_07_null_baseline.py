# %% [markdown]
# # Lab p8-07 · Is it really a reaction?
#
# **Goes with:** Phase 8, page 07 — Is it really bimodal? · **Time:** about 20 minutes
#
# Page 07 compares the real pit-lap deltas with a shuffled version, to ask whether two cars'
# stops are linked. You build that test, run it on three synthetic data sets, find the one it gets
# wrong, and fix it. Last, a case it cannot see at all.
#
# **Data:** `labs/labkit/pitdata.py`, 2,000 races of 52 laps each. One stop per car per race, plus
# the lap a safety car came out (or −1).
#
# Stuck? Run `python -m labs hint p8-07` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import games, pitdata, pitgame, predict

LAB = "p8-07"
N_SHUFFLES = 500

# %% [markdown]
# ## Part A — the statistic and the shuffle
#
# The statistic is the share of races in which the two cars stopped on the **same lap**,
# P(delta = 0). An undercut or an overcut moves mass away from 0; two cars that simply like the
# same window put some there by chance. The shuffle asks how much is "by chance".
#
# **TODO 1.** `delta_stat(agent, rival)`: the fraction of races with agent lap == rival lap.
#
# **TODO 2.** `shuffle_null(agent, rival, n, rng)`: n times, permute `rival` (break the pairing
# between races) and recompute the statistic. Return (the array of n null statistics, the p-value).
# The p-value is two-sided: (1 + the number of null values at least as far from the null's mean as
# the real value is) / (n + 1).

# %%
def delta_stat(agent, rival):
    # >>> SOLUTION: mean of agent == rival
    return float(np.mean(np.asarray(agent) == np.asarray(rival)))
    # <<< SOLUTION


def p_value(real, null):
    null = np.asarray(null)
    # >>> SOLUTION: two-sided, with the +1 in numerator and denominator
    far = np.abs(null - null.mean()) >= abs(real - null.mean())
    return float((far.sum() + 1) / (len(null) + 1))
    # <<< SOLUTION


def shuffle_null(agent, rival, n, rng):
    real = delta_stat(agent, rival)
    # >>> SOLUTION: n permutations of rival, each scored with delta_stat
    null = np.array([delta_stat(agent, rng.permutation(rival)) for _ in range(n)])
    # <<< SOLUTION
    return null, p_value(real, null)


checks.part_a(delta_stat, p_value, shuffle_null)

# %% [markdown]
# ## Part B — three data sets
#
# * **independent:** each car stops in its own window, laps 16–24. Nothing links them.
# * **shared safety car:** the same, but half the races have a safety car, and a car whose window is
#   near it stops under it. Both cars react to the safety car. Neither reacts to the other.
# * **reactive:** as the shared one, but with no safety car the agent stops one or two laps before
#   or after the rival: an undercut or an overcut. A real reaction.
#
# **Predict.** On the *shared safety car* data, does the shuffle test say the cars' stops are linked?

# %%
CHOICES = {
    "no": "no: neither car reacts to the other, so the test should not reject",
    "yes": "yes: the test rejects, even though neither car reacts to the other",
}
my_prediction = "yes"  # >>> ANSWER
predict.commit(LAB, "sc", my_prediction, CHOICES)

# %%
data = {name: getattr(pitdata, name)(2000, 0) for name in ("independent", "shared_safety_car", "reactive")}
plain = {}
for name, (a, b, sc) in data.items():
    null, p = shuffle_null(a, b, N_SHUFFLES, np.random.default_rng(0))
    plain[name] = p
    print(f"{name:18s}  P(delta = 0): real {delta_stat(a, b):.3f}, shuffled {null.mean():.3f}   p = {p:.3f}")
predict.reveal(LAB, "sc", f"p = {plain['shared_safety_car']:.3f} on the shared-safety-car data", correct="yes")
checks.part_b(plain)

# %% [markdown]
# The shuffle pairs each agent stop with a rival stop *from another race*. That breaks the
# reaction, if there is one, but it also breaks everything else the two cars shared in a race: the
# same safety car, the same weather, the same scenario seed. In the real plan every car in a race
# shares its scenario, so this is the normal case. The shuffle cannot tell "they reacted to each
# other" from "they reacted to the same thing".

# %% [markdown]
# ## Part C — shuffle only among races that shared the same conditions
#
# **TODO 3.** `stratified_null(agent, rival, strata, n, rng)`: as `shuffle_null`, but each
# permutation only moves rival stops between races with the same `strata` value (here, the same
# safety-car lap, −1 for none). Within a group, the shared cause is the same for every race, so
# shuffling there breaks only the link between the two cars.

# %%
def stratified_null(agent, rival, strata, n, rng):
    real = delta_stat(agent, rival)
    rival, strata = np.asarray(rival), np.asarray(strata)
    groups = [np.flatnonzero(strata == v) for v in np.unique(strata)]
    null = np.empty(n)
    # >>> SOLUTION: for each shuffle, permute rival within each group, then score
    for k in range(n):
        shuffled = rival.copy()
        for idx in groups:
            shuffled[idx] = rival[rng.permutation(idx)]
        null[k] = delta_stat(agent, shuffled)
    # <<< SOLUTION
    return null, p_value(real, null)


strat = {}
for name, (a, b, sc) in data.items():
    null, p = stratified_null(a, b, sc, N_SHUFFLES, np.random.default_rng(0))
    strat[name] = p
    print(f"{name:18s}  stratified: shuffled {null.mean():.3f}   p = {p:.3f}   (plain shuffle p = {plain[name]:.3f})")
checks.part_c(strat)

# %% [markdown]
# ## Part D — a shape the test cannot see
#
# Given cells. Take the pit-timing duel of the capstone (`labkit.pitgame`): with blocking on, the
# equilibrium has the follower mixing undercuts and an overcut, and the leader covering. Draw 2,000
# races in which each car picks its stop lap *independently* from its equilibrium mixture, before
# the race starts. The delta histogram is strategic through and through: it is the shape of the
# equilibrium. Is it a "reaction"?

# %%
U = pitgame.matrix(interaction=True)
i8 = pitgame.lap_index(8)
f_mix, l_mix, _ = games.fictitious_play(U, 10_000, start=(i8, i8))
rng = np.random.default_rng(3)
fa = np.array(pitgame.LAPS)[rng.choice(len(pitgame.LAPS), 2000, p=f_mix)]
la = np.array(pitgame.LAPS)[rng.choice(len(pitgame.LAPS), 2000, p=l_mix)]
null, p_mixed = shuffle_null(fa, la, N_SHUFFLES, np.random.default_rng(0))
d = fa - la
plt.hist(d, bins=np.arange(-8.5, 9.5), edgecolor="k"); plt.axvline(0, color="r")
plt.xlabel("follower stop lap − leader stop lap"); plt.title("equilibrium play, no reaction within the race"); plt.show()
print(f"P(delta = 0) {delta_stat(fa, la):.3f}, shuffled {null.mean():.3f}, p = {p_mixed:.3f}")
checks.part_d(p_mixed)

# %% [markdown]
# The test does not reject, and it is right not to: it asks whether one car's stop depended on the
# other's *in the same race*, and these were chosen before the start. The undercut-and-cover shape
# is in the *marginals*, which the shuffle keeps. So the two questions are different:
#
# * "Did the cars react to each other during the race?" — the stratified shuffle.
# * "Is the shape of the histogram strategic?" — compare against a world where it cannot be, which
#   for this project means the same training with blocking switched off (pages 06 and 08).
