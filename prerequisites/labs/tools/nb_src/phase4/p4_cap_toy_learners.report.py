# %% [markdown]
# # Phase 4 capstone · Learner report
#
# Run this **after** `python -m labs check p4-cap` is green. It uses the learners you wrote
# in `toy_learners.py` to look at four things the tests only touch on. There is nothing to
# implement here: two predictions, then read the results. It takes about a minute to run.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import toy_learners as tl
from labs.labkit import predict
from labs.labkit import toyrace as tr
from labs.labkit.toyrace import A, DRY

LAB = "p4-cap"
QUIET = tr.RaceModel(sc_hazard=0.0)  # no safety car
OPTIMUM = tr.solve(QUIET)[0][(1, A, 1, 0, False, DRY)]
print(f"exact optimum of the quiet race: {OPTIMUM:.2f} s")

# %% [markdown]
# ## 1. Two learning curves, against the exact answer
#
# Each point is the **exact** expected time of the learner's current greedy policy, minus the
# optimum. Nothing is estimated from sample races, so a gap of 0.00 means the policy is
# optimal, and any wobble in the curve is the policy really changing.

# %%
def gap_curve(learner, model, races=5000, every=250):
    points = []
    for chunk in range(races // every):
        tl.train(learner, model, every, seed=chunk)
        points.append(tl.gap_to_optimum(learner, model))
    return points


curves = {
    "off-policy (Q-learning)": gap_curve(tl.OffPolicyLearner(seed=0), QUIET),
    "on-policy (SARSA)": gap_curve(tl.OnPolicyLearner(seed=0), QUIET),
}
x = np.arange(1, 21) * 250
plt.figure(figsize=(7, 3.5))
for name, points in curves.items():
    plt.plot(x, points, marker="o", label=name)
plt.axvline(3000, linestyle="--", color="gray")
plt.text(3050, max(max(p) for p in curves.values()) * 0.9, "ε reaches its floor")
plt.xlabel("training races")
plt.ylabel("gap to the exact optimum (s)")
plt.legend()
plt.show()
for name, points in curves.items():
    print(f"{name:<24} gap after 1,000 races: {points[3]:6.2f} s   after 5,000: {points[-1]:5.2f} s")

# %% [markdown]
# The curves do not fall smoothly, even after ε reaches its floor. The greedy policy is read
# off the table one state at a time, so a single update that flips the preferred action at
# one early lap changes the whole race that follows. Early on, with a half-filled table, the
# policy can be far worse than it was 250 races before. The real project's curve will look
# like this too. The number that says whether learning worked is the gap at the end, and one
# seed is one sample of it: section 2 uses three.
#
# ## 2. What reward centring does
#
# The learners above were told `-(lap_time - 10)` each lap, about −1. The uncentred reward
# is `-lap_time`, about −11. Every cell of the table starts at 0 either way.
#
# **Predict first.** Train the same off-policy learner both ways, three seeds each, 5,000
# races. The uncentred learner will finish

# %%
CHOICES = {
    "same": "with the same gap: a constant cannot change which policy is best",
    "worse": "with a clearly larger gap",
    "better": "with a smaller gap: larger rewards are a stronger signal",
}
my_prediction = "worse"  # >>> ANSWER

predict.commit(LAB, "centring", my_prediction, CHOICES)

# %%
def final_gap(offset, seed, races=5000):
    learner = tl.OffPolicyLearner(seed=seed)
    tl.train(learner, QUIET, races, seed=seed, offset=offset)
    return tl.gap_to_optimum(learner, QUIET)


centred = [final_gap(tl.BASE_LAP, seed) for seed in range(3)]
uncentred = [final_gap(0.0, seed) for seed in range(3)]
print("gap with centring:   ", np.round(centred, 2), f"  mean {np.mean(centred):.2f} s")
print("gap without centring:", np.round(uncentred, 2), f"  mean {np.mean(uncentred):.2f} s")
predict.reveal(LAB, "centring", f"mean gap {np.mean(centred):.2f} s with centring, {np.mean(uncentred):.2f} s without", correct="worse")

# %% [markdown]
# The first choice states a true fact: centring cannot change which policy is best. What it
# changes is how hard that policy is to find from a table of zeros.
#
# Uncentred, a 20-lap race is worth about −225, so a cell that has never been updated (0)
# looks 225 seconds better than any cell that has. Every unvisited action looks like a
# bargain, in every state, until it has been tried many times. With a fixed budget of races,
# some of those cells are still wrong at the end, and the greedy policy walks into them.
# Centred, the same race is worth about −25, and the untried cells are far less misleading.
#
# The real race is 52 laps at about −95 each: nearly −5,000. That is why page 08 calls the
# reward scale the most likely reason for "trains without error and learns nothing".
#
# ## 3. Evaluating with exploration left on
#
# After training, ε sits at its floor of 0.05. Suppose the trained learner is "evaluated" by
# simply running more races, without switching exploration off.
#
# **Predict first.** Over 20 laps at ε = 0.05, about what share of evaluation races will
# differ from the learner's real, greedy race?

# %%
CHOICES = {
    "few": "about 5%: one race in twenty",
    "third": "roughly a third to a half",
    "all": "nearly all of them",
}
my_prediction = "third"  # >>> ANSWER

predict.commit(LAB, "exploration-on", my_prediction, CHOICES)

# %%
learner = tl.OffPolicyLearner(seed=0)
tl.train(learner, QUIET, 5000, seed=0)
rng = np.random.default_rng(1)
real = tl.run_race(learner, QUIET, rng, train=False, greedy=True)
noisy = [tl.run_race(learner, QUIET, rng, train=False, greedy=False) for _ in range(2000)]
changed = np.mean([race["actions"] != real["actions"] for race in noisy])
lost = np.mean([race["time"] for race in noisy]) - real["time"]
stops = np.mean([sum(a != 0 for a in race["actions"]) for race in noisy])

print(f"greedy race: {real['time']:.2f} s, {sum(a != 0 for a in real['actions'])} stop")
print(f"with ε = 0.05 left on: {changed:.0%} of races differ from it, {stops:.2f} stops on average, {lost:.2f} s slower on average")
print(f"chance that a 20-lap race has no random draw at all: 0.95^20 = {0.95 ** 20:.0%}")
print(f"same sum for the real 52-lap race:                   0.95^52 = {0.95 ** 52:.0%}")
predict.reveal(LAB, "exploration-on", f"{changed:.0%} of the evaluation races were not the learner's real race", correct="third")

# %% [markdown]
# Five per cent per lap sounds negligible and is not: a random draw happens somewhere in
# about two races out of three. Many draws happen to pick the action the table preferred
# anyway, which is why fewer races than that actually change. In the real 52-lap race only
# about 7% of evaluation races would escape a random draw altogether.
#
# The learner's policy did not get worse. The measurement did. Every reported number would
# understate the agent, by an amount that depends on ε and nothing else. The fix is the
# `greedy=True` flag you implemented in stage 1, and using it whenever a number is reported.
#
# ## 4. The same learner, with a safety car
#
# Everything above used a race with no randomness. Now the full toy race, where a safety car
# can appear, with a longer run of 8,000 races.

# %%
full = tr.RaceModel()
learner = tl.OffPolicyLearner(seed=0, decay_steps=96_000)
tl.train(learner, full, 8000, seed=0)
gap = tl.gap_to_optimum(learner, full)
optimum_full = tr.solve(full)[0][(1, A, 1, 0, False, DRY)]
print(f"exact optimum with the safety car: {optimum_full:.2f} s")
print(f"gap after 8,000 races: {gap:.2f} s  ({100 * gap / optimum_full:.1f}% of the race)")

# %% [markdown]
# More races, and a gap that has not closed. Two things got harder at once. There are twice
# as many states to fill, since every situation now exists with and without the safety car.
# And each cell's target is noisy: the same action from the same state leads to different
# next states, so a cell needs many visits before its average means anything.
#
# This is the number the real project reports for Phase 4: the gap to the exact optimum, in
# seconds. "It beat a baseline" says the learner found something. The gap says how much is
# left.
#
# **Capstone complete.** You now have, in your own code, the shape of the real
# `q_learning_agent.py`. Page 08 names which real piece matches each stage.
