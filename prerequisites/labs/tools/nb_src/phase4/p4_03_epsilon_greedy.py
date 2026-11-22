# %% [markdown]
# # Lab p4-03 · Decay and masking
#
# **Goes with:** Phase 4, page 03 — Exploration: ε-greedy · **Time:** about 20 minutes
#
# You will implement masked ε-greedy and the linear decay schedule, find out how fast ε can
# fall before an agent locks onto the wrong choice, and reproduce the page's
# masked-versus-unmasked table by experiment.
#
# **Environment:** the 10-armed bandit testbed from Sutton & Barto, chapter 2. There is no
# state and no sequence: ten levers, each paying a noisy reward around its own hidden average.
# The only problem is the one this page is about, which is how much to explore.
#
# Stuck? Run `python -m labs hint p4-03` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import numpy as np

import checks
from labs.labkit import predict

LAB = "p4-03"

# %% [markdown]
# ## Part A — masked ε-greedy
#
# **TODO 1.** Implement `masked_epsilon_greedy`. `q` is an array with one estimated value per
# action, and `legal` is a boolean array of the same length.
#
# - Draw one number with `rng.random()`. If it is below `epsilon`, **explore**: return one
#   of the legal actions, each equally likely (`rng.choice` on the legal indices).
# - Otherwise **exploit**: return the legal action with the highest `q`. An illegal action
#   must never be returned, however high its `q` is.

# %%
def masked_epsilon_greedy(q, legal, epsilon, rng):
    """One ε-greedy choice among the legal actions. Returns an int."""
    # >>> SOLUTION: with probability epsilon pick uniformly among the legal indices; otherwise take the argmax of q with illegal entries set to -inf
    legal_indices = np.flatnonzero(legal)
    if rng.random() < epsilon:
        return int(rng.choice(legal_indices))
    masked = np.where(legal, q, -np.inf)
    return int(np.argmax(masked))
    # <<< SOLUTION


checks.selection(masked_epsilon_greedy)

# %% [markdown]
# ## Part B — the decay schedule
#
# **TODO 2.** Implement `linear_epsilon`: the page's formula.
#
# ```
# ε_t = max( end,  start − step · (start − end) / decay_steps )
# ```

# %%
def linear_epsilon(step, start, end, decay_steps):
    """ε after `step` steps of a linear decay from `start` to `end` over `decay_steps` steps."""
    # >>> SOLUTION: start minus step times the per-step decrement, never below end
    return max(end, start - step * (start - end) / decay_steps)
    # <<< SOLUTION


checks.schedule(linear_epsilon)

# %% [markdown]
# Now use it on the real plan's numbers: `start = 1.0`, `end = 0.05`,
# `decay_steps = 500,000`, and a training run of 10,000 races.
#
# **TODO 3.** A race at this project's reference circuit is **52 laps**, so 52 steps. After
# how many complete races does ε reach its floor? Work it out and set the answer.

# %%
races_until_floor = 9615  # >>> ANSWER

checks.floor(races_until_floor, linear_epsilon)

# %% [markdown]
# Read that number against the 10,000 races of the planned run. Exploration does not reach
# its floor until the run is nearly over. The plan's config comment says the decay covers
# "~5K eps", which would be true of a 100-lap race. Whether that much exploration is too much
# is the question Part C answers.
#
# ## Part C — how fast should ε fall?
#
# The bandit below is given. It plays 1,000 pulls with ε falling from 1.0 to 0 over
# `decay_steps` pulls, using your two functions, and reports how often it pulled the truly
# best lever during its **last 200 pulls**. We average over 150 different bandits.
#
# Three schedules:
#
# - `decay_steps = 1`: greedy from the first pull;
# - `decay_steps = 300`: explore for the first third, then settle;
# - `decay_steps = 3000`: still exploring about two pulls in three when the run ends.
#
# **TODO — predict before you run.** Which one pulls the best lever most often at the end?

# %%
CHOICES = {
    "1": "greedy from the start: no pulls wasted on exploring",
    "300": "explore for a third of the run, then exploit",
    "3000": "keep exploring throughout: the best-informed estimates",
}
my_prediction = "300"  # >>> ANSWER

predict.commit(LAB, "decay", my_prediction, CHOICES)

# %%
def run_bandit(decay_steps, seed, pulls=1000, arms=10):
    rng = np.random.default_rng(seed)
    true_values = rng.normal(0.0, 1.0, arms)
    estimates, counts = np.zeros(arms), np.zeros(arms)
    legal = np.ones(arms, dtype=bool)
    best, hits = int(np.argmax(true_values)), 0
    for t in range(pulls):
        epsilon = linear_epsilon(t, 1.0, 0.0, decay_steps)
        arm = masked_epsilon_greedy(estimates, legal, epsilon, rng)
        reward = rng.normal(true_values[arm], 1.0)
        counts[arm] += 1
        estimates[arm] += (reward - estimates[arm]) / counts[arm]
        if t >= pulls - 200:
            hits += arm == best
    return hits / 200


results = {}
for decay_steps in (1, 300, 3000):
    results[decay_steps] = float(np.mean([run_bandit(decay_steps, seed) for seed in range(150)]))
    print(f"decay_steps = {decay_steps:>4}: best lever pulled on {results[decay_steps]:.0%} of the last 200 pulls")

winner = max(results, key=results.get)
predict.reveal(LAB, "decay", f"decay_steps = {winner} did best", correct="300")
checks.sweep(results)

# %% [markdown]
# Both extremes lose, for opposite reasons.
#
# - **Greedy from the start** commits to whichever lever looked best after one or two noisy
#   pulls and never finds out it was wrong. This is the page's "decaying ε too fast" pitfall
#   in its purest form.
# - **Still exploring at the end** knows the best lever perfectly well, and is pulling a
#   random one most of the time anyway. Knowing and doing are different things, and reward
#   comes only from doing.
#
# The real plan's schedule, with ε still at its starting slope for 96% of the run, sits
# toward the second failure. That is worth raising before Phase 4 is built: a
# `decay_steps` near half the run's total steps, about 260,000, is what the page describes.
#
# ## Part D — masking inside exploration
#
# The page's table: 6 actions, 3 of them legal, and exactly one of those 3 is the useful one.
# Over 10 exploratory visits, how likely is it that the useful action gets tried at least
# once? The page computes 0.983 with masking and 0.838 without. Check it with your function,
# at `epsilon = 1.0` so every choice is an exploration.

# %%
def discovery_rate(legal, useful=2, visits=10, trials=4000, seed=0):
    rng = np.random.default_rng(seed)
    q = np.zeros(len(legal))
    found = 0
    for _ in range(trials):
        found += any(masked_epsilon_greedy(q, legal, 1.0, rng) == useful for _ in range(visits))
    return found / trials


masked = discovery_rate(np.array([True, False, True, False, True, False]))
unmasked = discovery_rate(np.ones(6, dtype=bool))  # "no mask" is the same as "everything legal"
print(f"masked:   useful action tried at least once in {masked:.3f} of trials   (page: 0.983)")
print(f"unmasked: useful action tried at least once in {unmasked:.3f} of trials   (page: 0.838)")
checks.discovery(masked, unmasked)

# %% [markdown]
# The unmasked agent spends half of its exploration on actions that could never have been
# taken. With 10 visits it mostly gets away with it. At a rarely visited state, with 2 or 3
# visits in a whole training run, it often does not.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
