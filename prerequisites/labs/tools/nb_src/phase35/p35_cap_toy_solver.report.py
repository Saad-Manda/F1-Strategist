# %% [markdown]
# # Phase 3.5 capstone · Solver report
#
# Run this **after** `python -m labs check p35-cap` is green. It uses the solver you wrote in
# `toy_solver.py` to look at four things the tests cannot show you. There is nothing to
# implement here: two predictions, then read the results.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

import toy_solver as ts
from labs.labkit import predict
from labs.labkit import toyrace as tr
from labs.labkit.toyrace import A, B, DRY, PIT_B, STAY_OUT, WET, RaceModel

LAB = "p35-cap"
H = tr.HORIZON

# %% [markdown]
# ## 1. The optimal policy, as a picture
#
# Your stage 3 solver produced a table with an action for every state. Here is one slice of
# it: on compound A, the other compound not yet used, for every lap and every tyre age that
# is possible on that lap. Left under a green flag, right under the safety car.

# %%
V, policy = ts.solve_with_rules(RaceModel())

fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
for ax, sc, title in zip(axes, (0, 1), ("green flag", "safety car out")):
    grid = np.full((H, H), np.nan)
    for lap in range(1, H + 1):
        for age in range(1, lap + 1):
            grid[age - 1, lap - 1] = 0 if policy[(lap, A, age, sc, False)] == STAY_OUT else 1
    ax.imshow(grid, origin="lower", cmap=ListedColormap(["#c9d1d9", "#d6336c"]), vmin=0, vmax=1, extent=(0.5, H + 0.5, 0.5, H + 0.5))
    ax.set_title(f"on A, B not used yet: {title}")
    ax.set_xlabel("lap")
axes[0].set_ylabel("tyre age")
plt.suptitle("grey = stay out, red = pit for B")
plt.show()

first_green = min(lap for lap in range(1, H + 1) if policy[(lap, A, lap, 0, False)] != STAY_OUT)
first_sc = min(lap for lap in range(1, H + 1) if policy[(lap, A, lap, 1, False)] != STAY_OUT)
print(f"Never having stopped, the policy first pits on lap {first_green} under green, and already on lap {first_sc} if the safety car is out.")

# %% [markdown]
# The boundary between grey and red is the pit window. It sits at a lower tyre age in the
# right-hand picture: a stop under the safety car costs 40% of the usual loss, so a tyre that
# would be worth keeping under green is worth changing. Nobody wrote that rule. It fell out of
# `min` over two totals.
#
# Only the diagonal (age = lap) is ever visited before the first stop. The solver filled in
# the rest anyway, which is why it knows what to do after any stop at any time.
#
# ## 2. How wide is the window?
#
# With no safety car, the exact optimum is a one-stop race, so it can be compared with every
# one-stop plan directly.

# %%
quiet = RaceModel(sc_hazard=0.0)
V_quiet, _ = ts.solve_with_rules(quiet)
solved = V_quiet[(1, A, 1, 0, False)]


def one_stop_time(model, pit_lap):
    compound, age, total = A, 1, 0.0
    for lap in range(1, model.horizon + 1):
        action = PIT_B if lap == pit_lap else STAY_OUT
        total += model.cost(lap, compound, age, action)
        compound, age = model.next_tyre(compound, age, action)
    return total


pit_laps = list(range(1, H + 1))
times = [one_stop_time(quiet, lap) for lap in pit_laps]
window = [lap for lap, t in zip(pit_laps, times) if t <= solved + 1.0]

plt.figure(figsize=(7, 3.5))
plt.plot(pit_laps, times, marker="o", label="one stop on this lap")
plt.axhline(solved, linestyle="--", color="gray", label="your solver's optimum")
plt.xlabel("lap of the pit stop")
plt.ylabel("total race time (s)")
plt.legend()
plt.show()
print(f"solver optimum: {solved:.2f} s   best one-stop plan: {min(times):.2f} s")
print(f"stops within 1 s of the optimum: laps {window[0]} to {window[-1]}")

# %% [markdown]
# The dashed line touches the bottom of the valley: the solver found, in one backward pass,
# the same lap you found in the Phase 1 report by trying all of them. The window is a few laps
# wide. Keep that width in mind. In Phase 4, a learner that cannot tell those laps apart
# cannot find the bottom.
#
# ## 3. Break it on purpose: a pit stop that gains time
#
# `RaceModel(pit_loss=-4.0)` is the same race with one sign flipped: a pit stop now takes four
# seconds **off** the lap. Your solver will solve that model exactly too.
#
# **Predict first.** How many pit stops will the "optimal" race in the broken model make?

# %%
CHOICES = {
    "one-or-two": "one or two, as before",
    "several": "several more than before, but far from every lap",
    "every-lap": "a stop on every lap, or nearly",
}
my_prediction = "every-lap"  # >>> ANSWER

predict.commit(LAB, "broken-model", my_prediction, CHOICES)

# %%
broken = RaceModel(sc_hazard=0.0, pit_loss=-4.0)
V_broken, policy_broken = ts.solve_full(broken)
race = tr.simulate(broken, lambda *state: policy_broken[state], np.random.default_rng(0))
stops = sum(action != STAY_OUT for action in race["actions"])
solved_broken, baseline_broken = V_broken[(1, A, 1, 0, False, DRY)], ts.best_one_stop_time(broken)

print(f"stops in the 'optimal' race: {stops} of {H} laps")
print(f"solver: {solved_broken:.1f} s   best one-stop baseline in the same model: {baseline_broken:.1f} s")
print(f"saving over the baseline: {100 * (baseline_broken - solved_broken) / baseline_broken:.0f}%")
print("looks_absurd:", ts.looks_absurd(solved_broken, baseline_broken))
predict.reveal(LAB, "broken-model", f"{stops} stops in {H} laps", correct="every-lap")

# %% [markdown]
# The solver did nothing wrong. It was asked for the best policy of the model it was given,
# and in that model changing tyres every lap really is best. An exact solver cannot tell
# "cheap" from "cheap because of a bug", so it finds the bug's most profitable use every time.
#
# That is what makes it a good test of a simulator. The comparison with a baseline you can
# reason about by hand caught the problem in one line. The real project's
# `test_oracle_no_absurd_exploit` is this check.
#
# ## 4. What is knowing the weather worth?
#
# Two ways to solve a race whose weather changes:
#
# - **Markov weather:** the solver knows only the chain. This is the question the agent faces.
# - **Known weather:** the solver is told the whole race's weather in advance.
#
# For each of 60 sampled weather histories, we solve the race knowing that history, and we
# also work out exactly what the Markov-weather policy would score on that same history.
#
# **Predict first.** Across those histories, the known-weather solver will be

# %%
CHOICES = {
    "always-at-least-as-good": "at least as fast as the Markov-weather policy on every single history",
    "better-on-average": "faster on average, but slower on some histories",
    "no-different": "no different: the weather does not change the decisions",
}
my_prediction = "always-at-least-as-good"  # >>> ANSWER

predict.commit(LAB, "foresight", my_prediction, CHOICES)

# %%
def evaluate(model, policy):
    """Exact expected time of following a fixed `policy` in `model`: the backward pass with no min."""
    V = {}
    for lap in range(model.horizon + 1, 0, -1):
        ages = range(1, model.horizon + 2) if lap > model.horizon else range(1, lap + 1)
        for c in (A, B):
            for age in ages:
                for sc in (0, 1):
                    for used in (False, True):
                        for w in (DRY, WET):
                            key = (lap, c, age, sc, used, w)
                            if lap > model.horizon:
                                V[key] = 0.0
                                continue
                            action = policy[key]
                            next_c, next_age = model.next_tyre(c, age, action)
                            V[key] = model.cost(lap, c, age, action, w, sc) + ts.expect_next(
                                model, V, lap, next_c, next_age, used or next_c != c, sc, w
                            )
    return V


START = (1, A, 1, 0, False, DRY)
V_markov, policy_markov = ts.solve_full(RaceModel(weather="markov"))

rng = np.random.default_rng(0)
gaps = []
for _ in range(60):
    history = [DRY]
    while len(history) < H:
        history.append(int(rng.random() < tr.WEATHER_CHAIN[history[-1]][WET]))
    known = RaceModel(weather_trace=history)
    with_foresight = ts.solve_full(known)[0][START]
    without = evaluate(known, policy_markov)[START]
    gaps.append(without - with_foresight)
gaps = np.array(gaps)

print(f"Markov-weather optimum (what the agent can aim for): {V_markov[START]:.2f} s")
print(f"gap to the known-weather solver, per history: smallest {gaps.min():.2f} s, mean {gaps.mean():.2f} s, largest {gaps.max():.2f} s")
outcome = "never slower" if gaps.min() > -1e-9 else "sometimes slower"
predict.reveal(LAB, "foresight", f"the known-weather solver was {outcome}; foresight is worth {gaps.mean():.2f} s on average",
               correct="always-at-least-as-good")

# %% [markdown]
# The smallest gap is zero and none is negative. A solver that knows the future can always
# copy what the other policy does, so it can never do worse. That is the real project's
# `test_oracle_a_dominates_oracle_b`.
#
# The mean gap, a little under a second in a race of about 250, is the **value of perfect
# foresight** in this toy. It is not something a learning agent failed to find. No agent that
# sees only the current weather could have it. That is why the real project reports an
# agent's gap to the Markov-weather oracle (Oracle B), and reports the known-weather oracle
# (Oracle A) separately, as a bound.
#
# **Capstone complete.** You now have, in your own code, the shape of the real
# `dp_oracle.py`. Page 06 names which real piece matches each stage. The Phase 4 capstone
# will measure a learning agent against the numbers you just computed.
