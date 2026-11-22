# %% [markdown]
# # Phase 1 capstone · Race report
#
# Run this **after** `python -m labs check p1-cap` is green. It uses the environment you
# built in `toy_race.py` to look at three things the tests cannot show you.
# There is nothing to implement here: one prediction, then read the results.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import toy_race as tr
from labs.labkit import predict
from toy_race import DRY, HORIZON, PIT_A, PIT_B, STAY_OUT

LAB = "p1-cap"
GREEN = [False] * HORIZON


def race_time(env, pit_lap=None):
    """Total time of a dry, green race on A that switches to B at the end of `pit_lap`."""
    env.reset(seed=0, options={"weather": DRY, "sc_trace": GREEN})
    total, done, lap = 0.0, False, 1
    while not done:
        _, _, done, _, info = env.step(PIT_B if lap == pit_lap else STAY_OUT)
        total += info["lap_time"]
        lap += 1
    return total

# %% [markdown]
# ## 1. When should you pit?
#
# One stop, A then B, dry, no safety car. The only choice is the lap. Every point on this
# curve is one complete race in your environment.

# %%
pit_laps = list(range(1, HORIZON))
times = [race_time(tr.ToyRaceEnv(), lap) for lap in pit_laps]
best = pit_laps[int(np.argmin(times))]

plt.figure(figsize=(7, 3.5))
plt.plot(pit_laps, times, marker="o")
plt.axvline(best, linestyle="--", color="gray")
plt.xlabel("lap of the pit stop")
plt.ylabel("total race time (s)")
plt.title(f"One-stop race: best stop is lap {best} ({min(times):.2f} s)")
plt.show()

window = [lap for lap, t in zip(pit_laps, times) if t <= min(times) + 1.0]
print(f"never pitting: {race_time(tr.ToyRaceEnv()):.2f} s")
print(f"laps within 1 s of the best: {window[0]} to {window[-1]}")

# %% [markdown]
# The curve is a valley: pit too early and compound B has to survive too long; pit too late
# and compound A has fallen off its cliff. You found the bottom by trying all 19 options.
# With two stops, safety cars and weather that stops being possible by brute force, which is
# the problem the Phase 3.5 set solves exactly.
#
# ## 2. Break it on purpose: the pit-lap ordering bug
#
# `WrongOrderEnv` below is your environment with one change: on a pit lap it fits the new
# tyre **before** timing the lap, instead of after.
#
# **Predict first.** With a stop on lap 12, is the pit lap in the wrong-order version cheaper,
# dearer, or the same as in your correct version?

# %%
CHOICES = {
    "cheaper": "the wrong-order pit lap takes less time",
    "dearer": "the wrong-order pit lap takes more time",
    "same": "both versions charge the same for the pit lap",
}
my_prediction = "cheaper"  # >>> ANSWER

predict.commit(LAB, "wrong-order", my_prediction, CHOICES)

# %%
class WrongOrderEnv(tr.ToyRaceEnv):
    """The bug: the tyre change is applied before the lap is timed."""

    def step(self, action):
        if action != STAY_OUT:
            self._compound, self._age = ("A" if action == PIT_A else "B"), 1
            self._used.add(self._compound)
            obs, reward, terminated, truncated, info = super().step(STAY_OUT)
            info["lap_time"] += tr.PIT_LOSS
            return obs, reward - tr.PIT_LOSS, terminated, truncated, info
        return super().step(action)


def pit_lap_cost(env, pit_lap):
    env.reset(seed=0, options={"weather": DRY, "sc_trace": GREEN})
    for lap in range(1, pit_lap + 1):
        _, _, _, _, info = env.step(PIT_B if lap == pit_lap else STAY_OUT)
    return info["lap_time"]


right, wrong = pit_lap_cost(tr.ToyRaceEnv(), 12), pit_lap_cost(WrongOrderEnv(), 12)
print(f"pit lap, correct order: {right:.2f} s   (old compound A at age 12, plus the pit loss)")
print(f"pit lap, wrong order:   {wrong:.2f} s   (new compound B, plus the pit loss)")
print(f"whole race, correct:    {race_time(tr.ToyRaceEnv(), 12):.2f} s")
print(f"whole race, wrong:      {race_time(WrongOrderEnv(), 12):.2f} s")
predict.reveal(LAB, "wrong-order", f"the wrong-order pit lap is {right - wrong:.2f} s cheaper", correct="cheaper")

# %% [markdown]
# The buggy version hands the agent a lap of fresh-tyre pace it never drove: the worst lap of
# the old stint simply vanishes. Nothing crashes and every number looks plausible, which is
# why the real project has a test named `test_pit_lap_runs_on_old_tyre`. An agent trained in
# the buggy world would learn to pit late, because late stops erase the most expensive lap.
#
# ## 3. What the mask buys
#
# A timid random policy that pits on about 3% of laps, run for 500 dry races, once choosing
# among all actions and once choosing only among legal ones.

# %%
def races_missing_a_compound(use_mask, n=500):
    env, rng, missing = tr.ToyRaceEnv(), np.random.default_rng(0), 0
    for seed in range(n):
        obs, _ = env.reset(seed=seed, options={"weather": DRY})
        done = False
        while not done:
            action = STAY_OUT if rng.random() > 0.03 else int(rng.choice([PIT_A, PIT_B]))
            if use_mask and not env.action_masks()[action]:
                action = int(rng.choice(np.flatnonzero(env.action_masks())))
            obs, _, done, _, _ = env.step(action)
        missing += not (obs[7] == 1.0 and obs[8] == 1.0)
    return missing / n


print(f"ignoring the mask:   {races_missing_a_compound(False):.0%} of races never used both compounds")
print(f"respecting the mask: {races_missing_a_compound(True):.0%} of races never used both compounds")

# %% [markdown]
# With the mask, breaking the two-compound rule is not something the agent has to learn to
# avoid; it cannot happen. That is the same reason the real environment's −500 penalty is
# described as a backstop that should never fire.
#
# **Capstone complete.** You now have, in your own code, the shape of the real
# `dynamics.py` and `f1_strategy_env.py`. Page 06 names which real piece matches each stage.
