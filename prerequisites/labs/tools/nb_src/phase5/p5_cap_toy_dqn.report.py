# %% [markdown]
# # Phase 5 capstone · Network learner report
#
# Run this **after** `python -m labs check p5-cap` is green. It uses the learner you wrote in
# `toy_dqn.py` to do what page 09 does on its 12-lap stint: add one technique at a time and
# measure each against the exact optimum. Then it plants two faults and asks which numbers
# show them. There is nothing to implement: two predictions, then read the results.
#
# It trains eight learners of 600 races each, one per cell. Each takes one to three minutes
# depending on the machine (about three inside Jupyter on the machine this was written on), so
# expect the whole report to take **15 to 30 minutes**. Leave it running.

# %%
import pathlib
import sys
import time

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import numpy as np

import toy_dqn as td
from labs.labkit import memory as memories
from labs.labkit import predict
from labs.labkit import toyrace as tr
from labs.labkit.toyrace import A, ACTION_NAMES, DRY, STAY_OUT

LAB = "p5-cap"
QUIET = tr.RaceModel(sc_hazard=0.0)  # no safety car, as in the tests
OPTIMUM = tr.solve(QUIET)[0][(1, A, 1, 0, False, DRY)]
SCALE = -(OPTIMUM - 20 * td.BASE_LAP)  # what the best Q-value at the start should be, centred
START = td.encode(1, A, 1, 0, False)
print(f"exact optimum {OPTIMUM:.2f} s; the best centred Q-value at the start should be {SCALE:.2f}")


def plan(learner):
    """The greedy race, as the stops it makes."""
    out = td.run_race(learner, QUIET, np.random.default_rng(0), train=False)
    return ", ".join(f"lap {lap} {ACTION_NAMES[a]}" for lap, a in enumerate(out["actions"], 1) if a != STAY_OUT)


def measure(name, learner, offset=td.BASE_LAP, seed=0):
    start = time.time()
    td.train(learner, QUIET, 600, seed=seed, offset=offset)
    row = {"gap": td.gap_to_optimum(learner, QUIET), "q": float(learner.values(START).max()), "plan": plan(learner)}
    print(f"{name:<34} gap {row['gap']:5.2f} s   best Q at start {row['q']:8.1f}   stops: {row['plan']}   ({time.time() - start:.0f} s)")
    return row

# %% [markdown]
# ## 1. One technique at a time
#
# The same 600 races, seed 0, four learners:
#
# 1. **the stream:** one network, trained on each transition as it happens (page 03's naive idea, with no memory)
# 2. **+ target network and replay** (pages 03 and 04), one output head, the target network choosing
# 3. **+ two heads and the decoupled target** (pages 05 and 06): the default `NetLearner`
# 4. **+ prioritized replay** (page 07)
#
# **TODO — predict before you run.** The stream learner gets the same 600 races and the same
# number of updates as the others. How far from the optimum will its greedy race be?

# %%
CHOICES = {
    "close": "within 1 s: the toy is small, as page 09's stage 1 found",
    "near": "1 to 10 s",
    "far": "more than 10 s",
}
my_prediction = "far"  # >>> ANSWER

predict.commit(LAB, "stream", my_prediction, CHOICES)

# %%
rows = {}
rows["stream"] = measure("1. the stream", td.NetLearner(td.QNet, 0, memory=td.LatestOnly(), use_target=False, double=False, warmup=1))
predict.reveal(LAB, "stream", f"the stream learner finished {rows['stream']['gap']:.1f} s from the optimum", correct="far")

# %%
rows["replay"] = measure("2. + target network and replay", td.NetLearner(td.QNet, 0, double=False))

# %%
rows["full"] = measure("3. + two heads, decoupled target", td.NetLearner(seed=0))

# %%
rows["ranked"] = measure("4. + prioritized replay", td.NetLearner(seed=0, memory=memories.PriorityMemory(20_000, seed=0)))

# %% [markdown]
# On page 09's 12-lap stint the stream learner still found a good race. Here, with 20 laps,
# three actions and a mandatory second compound, it does not come close, and its value at
# the start is far from the true scale. Once it has a target network and a memory, the same
# network and the same number of updates find the optimum or a race a fraction of a second
# from it.
#
# Do not read much into the order of rungs 2 to 4 from one seed. The next cell shows why.
#
# ## 2. One more seed
#
# The full design (rung 3) again, with seed 1.

# %%
rows["full, seed 1"] = measure("3. full design, seed 1", td.NetLearner(seed=1), seed=1)

# %% [markdown]
# When this report was written, seed 0 found the optimum exactly and seed 1 finished about
# 4 s off. Look at the stops. The optimum is a single stop for B on lap 8. The near-miss makes
# the same stop and then adds a second, late stop for A, a lap or two from the end, which
# costs more than fresh tyres win back.
#
# That is page 06's warning played out. A late pit stop is a rarely tried action: few
# transitions in memory, an uncertain estimate, and a max (or an argmax) that finds whichever
# uncertain estimate landed high. The decoupled target reduces this bias and does not remove
# it, because the online and target networks share most of their errors. In runs made for this
# lab, with 1,000 races, four seeds of five reached the optimum or 0.18 s from it, and one stayed
# 3.5 s off with exactly this extra stop.
#
# So the tests ask for less than you might expect: within 6 s, against 38.5 s for an untrained
# network. Reporting several seeds and the spread between them, as Phase 4 page 08 does, is the
# only honest way to compare learners whose results come out like this.
#
# ## 3. A planted fault: the terminal cut-off
#
# Train the full design with `cutoff=False`: the last lap's target bootstraps from an
# invented "value after the race" (page 06, "a quiet bug").
#
# **TODO — predict.** Which number gives the fault away?

# %%
CHOICES_FAULT = {
    "gap": "the gap to the optimum: the race will be visibly worse",
    "q": "the best Q-value at the start, against the scale it must have",
    "neither": "neither: the cut-off only affects one lap in twenty",
}
my_prediction_fault = "q"  # >>> ANSWER

predict.commit(LAB, "fault", my_prediction_fault, CHOICES_FAULT)

# %%
rows["no cut-off"] = measure("full design, no terminal cut-off", td.NetLearner(seed=0, cutoff=False))
print(f"\nexpected best Q at the start: {SCALE:.1f}.  With the cut-off: {rows['full']['q']:.1f}.  Without: {rows['no cut-off']['q']:.1f}")
predict.reveal(LAB, "fault", f"the start value moved from {rows['full']['q']:.1f} to {rows['no cut-off']['q']:.1f}, where {SCALE:.1f} is right", correct="q")

# %% [markdown]
# The race is a few seconds worse, which on its own looks like the near-miss of section 2. The
# value is the giveaway: more than twice the true scale. Every lap's target now includes a
# made-up number for "after the race", and since that number is never corrected toward
# anything, it drifts, and the drift is passed backward through all twenty laps. Page 11's
# second proposed test, "a terminal transition's target equals its reward", catches this
# before any training is run.
#
# ## 4. The reward-scale trap, on the toy
#
# The full design once more, trained on the uncentred reward `−lap_time` (offset 0). The true
# best value at the start is then about −224.5 instead of −24.5.

# %%
rows["uncentred"] = measure("full design, uncentred reward", td.NetLearner(seed=0), offset=0.0)
print(f"\nexpected best Q at the start, uncentred: {-OPTIMUM:.1f}.  Got: {rows['uncentred']['q']:.1f}")

# %% [markdown]
# With uncentred rewards the values did not just converge more slowly. They overshot, to more
# than twice the true scale, which is the last row of page 08's table, "runaway estimates".
# The decisions may or may not survive, depending on the seed; the values do not. Twenty laps
# of −10 is a much smaller scale than the real project's 52 laps of −95, and the trap is
# already visible.
#
# ## 5. Where this leaves the comparison

# %%
print(f"{'learner':<36}{'gap to optimum (s)':>20}")
print(f"{'DP optimum (Phase 3.5 capstone)':<36}{0.0:>20.2f}")
print(f"{'table, 5,000 races (Phase 4 report)':<36}{'2.2 on average':>20}")
for name in ("replay", "full", "full, seed 1", "ranked"):
    print(f"{'network, 600 races: ' + name:<36}{rows[name]['gap']:>20.2f}")

# %% [markdown]
# The Phase 4 capstone's table learner, with centred rewards, was 2.2 s from the optimum on
# average over three seeds after 5,000 races. The network learners here had 600 races. On
# this small state space a table is not hopeless, as page 10 says the real plan expects. The
# network's advantage is how little experience it needs once it is stable, and that grows
# with every dimension a table would have to bin.
#
# **Done.** This report is not tracked; the capstone counts as passed when `python -m labs
# check p5-cap` is green.
