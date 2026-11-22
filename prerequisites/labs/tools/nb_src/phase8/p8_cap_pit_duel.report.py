# %% [markdown]
# # p8-cap report · Learners on the pit-timing duel
#
# Given cells: nothing to write, about six minutes to run. It uses the closed-loop learners in
# `labs/labkit/pitgame.py`, not your file, so it runs before your stages are green too.
#
# Your stages solved the duel *exactly*: a payoff matrix, best responses, fictitious play. The
# Phase 8 plan instead trains learners by self-play and reads a histogram off them. This report
# does that on the same duel, with tabular learners that choose every lap (they see the lap,
# whether each car has stopped, and who is ahead), and asks how much of what you'd read is real.

# %%
import pathlib
import sys
import time

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

from labs.labkit import games, pitgame

SEEDS = (0, 1, 2, 3)
RACES = 20_000

# %% [markdown]
# ## 1 · The exact answer, for reference
#
# Fictitious play on the cached matrices, 10,000 rounds: the delta histogram at equilibrium.

# %%
i8 = pitgame.lap_index(8)
exact = {}
for inter in (False, True):
    f, l, _ = games.fictitious_play(pitgame.matrix(inter), 10_000, start=(i8, i8))
    exact[inter] = pitgame.delta_distribution(f, l)
    d = exact[inter]
    print(f"blocking {'on ' if inter else 'off'}: P(delta = 0) {d.get(0, 0):.2f}, "
          f"follower first {sum(v for k, v in d.items() if k < 0):.2f}, leader first {sum(v for k, v in d.items() if k > 0):.2f}")

# %% [markdown]
# ## 2 · Sixteen self-play runs (about six minutes)
#
# Two opponent rules (the latest snapshot only, or the recency pool: 70% from the newest 20%,
# with the n = 1 guard, seeded with a random policy), blocking on and off, four seeds each. Each
# run is 20,000 races; then the learner plays 400 races against its last 20 pool entries, half in
# each seat, and we record both cars' stop laps.

# %%
t0 = time.time()
stops = {}
for mode in ("latest", "pool"):
    for inter in (False, True):
        for seed in SEEDS:
            learner, pool = pitgame.selfplay_train(mode, inter, RACES, seed)
            stops[mode, inter, seed] = pitgame.selfplay_deltas(learner, pool, inter)
print(f"{len(stops)} runs in {time.time() - t0:.0f} s")


def shares(s):
    d = s[:, 0] - s[:, 1]
    return np.mean(d == 0), np.mean(d < 0), np.mean(d > 0)


print("                         P(delta=0)  follower first  leader first")
for (mode, inter, seed), s in stops.items():
    p0, neg, pos = shares(s)
    print(f"{mode:6s} blocking {'on ' if inter else 'off'} seed {seed}:   {p0:.2f}        {neg:.2f}           {pos:.2f}")

# %%
bins = np.arange(-16.5, 17.5)
fig, ax = plt.subplots(4, 4, figsize=(14, 9), sharex=True, sharey=True)
for r, (mode, inter) in enumerate([(m, i) for m in ("latest", "pool") for i in (False, True)]):
    for c, seed in enumerate(SEEDS):
        s = stops[mode, inter, seed]
        a = ax[r, c]
        a.hist(s[:, 0] - s[:, 1], bins=bins, density=True, edgecolor="k", lw=0.3)
        ks = list(exact[inter])
        a.plot(ks, [exact[inter][k] for k in ks], "r.", ms=5)
        a.axvline(0, color="grey", lw=0.5)
        a.set_title(f"{mode}, blocking {'on' if inter else 'off'}, seed {seed}", fontsize=9)
for a in ax[-1]:
    a.set_xlabel("follower stop − leader stop")
fig.suptitle("learned pit-delta histograms (bars) against the exact equilibrium (red dots)")
plt.tight_layout(); plt.show()

# %% [markdown]
# Read the grid by columns before rows. If one seed's histogram looked like a finding ("two
# modes!", "the follower undercuts!"), the other three seeds of the same configuration say how much
# of that is the seed. This is why page 10 asks for several seeds before anyone reads a shape.
#
# Blocking off has a pure equilibrium at (8, 8), every delta 0. Whatever the learners show away
# from 0 there is learning noise or exploration, not strategy, and it is the control the
# blocking-on histogram must be compared against (page 06).
#
# At the build (2026-11-22) the exact blocking-on answer was 0.11 / 0.61 / 0.28 (same lap,
# follower first, leader first). The pool learners' "follower first" share ran from 0.09 to 0.78
# across the four seeds; with blocking off, where the exact answer is all at 0, learners still put
# up to 1.00 on "leader first". A single seed's histogram is not a result.

# %% [markdown]
# ## 3 · Closed-loop learners can react, so the null can reject
#
# Your stage 7 drew both stop laps *before* the race, and the shuffle rightly found no in-race
# link. These learners decide every lap and see whether the rival has stopped, so one car's stop can
# depend on the other's. There is no safety car in this duel, so there is no shared cause to
# stratify on and the plain shuffle is the stratified one.

# %%
def shuffle_p(f, l, n=500, seed=0):
    rng = np.random.default_rng(seed)
    real = np.mean(f == l)
    null = np.array([np.mean(f == rng.permutation(l)) for _ in range(n)])
    return float((np.sum(np.abs(null - null.mean()) >= abs(real - null.mean())) + 1) / (n + 1)), real, null.mean()


for (mode, inter, seed), s in stops.items():
    if seed > 1:
        continue
    p, real, nm = shuffle_p(s[:, 0], s[:, 1])
    print(f"{mode:6s} blocking {'on ' if inter else 'off'} seed {seed}: P(delta = 0) {real:.2f} vs shuffled {nm:.2f}, p = {p:.3f}")

# %% [markdown]
# At the build, blocking-on runs rejected for three of the four (p = 0.002), and so did one
# blocking-OFF run (pool, seed 0). The cars race each other with or without blocking, so a
# learner that covers the rival's stop is reacting whether or not the reaction pays.
#
# A small p here says the cars' stops are linked *within* a race: one waits for, or answers, the
# other. It does not say the link is the equilibrium's, nor that it is clever. The two questions
# stay apart, as in lab p8-07: "did they react?" is the shuffle; "is the shape strategic?" is the
# comparison with blocking off.
