# %% [markdown]
# # Lab p1-01 · Be the agent
#
# **Goes with:** Phase 1, page 01 — RL fundamentals · **Time:** about 15 minutes
#
# You will drive the agent–environment loop by hand, write the loop as a function, and then
# watch a "policy" that has only memorised one lucky episode fall apart the moment the
# randomness is fresh.
#
# **Environment:** FrozenLake, the classic 4×4 grid. Start top-left (state 0), reach the goal
# bottom-right (state 15), don't step in a hole.
#
# ```
# S F F F      states are numbered row by row, 0..15
# F H F H      H = hole: episode ends, reward 0
# F F F H      G = goal: episode ends, reward 1
# H F F G
# ```
#
# Run the cells in order. Cells marked **TODO** need you; everything else is given.
# Stuck? Run `python -m labs hint p1-01` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import numpy as np

import checks
from labs.labkit import envs, predict
from labs.labkit.envs import DOWN, LEFT, RIGHT, UP

LAB = "p1-01"

# %% [markdown]
# ## Part A — be the agent
#
# No policy yet: *you* choose the actions. The ice is not slippery in this part, so each
# action does exactly what it says. The cell below takes two steps: RIGHT, then DOWN.
# Read what comes back from each `env.step(...)`.

# %%
env = envs.make_frozen_lake(slippery=False)
obs, info = env.reset(seed=0)
print("reset            -> obs =", obs)

for name, action in [("RIGHT", RIGHT), ("DOWN", DOWN)]:
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"step({name:<5})      -> obs = {obs}, reward = {reward}, terminated = {terminated}, truncated = {truncated}")

# %% [markdown]
# The second step walked into the hole at state 5.
#
# **TODO.** Answer two questions about what you just saw.
#
# 1. Which of the five returned values told you the episode was over?
#    One of `"obs"`, `"reward"`, `"terminated"`, `"truncated"`, `"info"`.
# 2. What reward did falling in the hole give? (A number.)

# %%
ended_signal = "terminated"  # >>> ANSWER
hole_reward = 0.0  # >>> ANSWER

checks.part_a(ended_signal, hole_reward)

# %% [markdown]
# Notice what that second answer means: the environment never *tells* the agent that holes
# are bad. A hole and a harmless step both pay 0. The only signal is that episodes ending in
# a hole never collect the 1. That is the page's point about the agent only ever seeing
# observation → action → reward.
#
# ## Part B — write the loop
#
# **TODO.** Implement the agent–environment loop from the page as a function.
#
# - `policy` is any callable that takes an observation and returns an action.
# - Start the episode with `env.reset(seed=seed)`.
# - Keep stepping until the episode ends **for either reason** (`terminated` or `truncated`).
# - Return the total reward and the number of steps taken.

# %%
def run_episode(env, policy, seed=None):
    """Play one episode. Returns (total_reward, steps)."""
    # >>> SOLUTION: reset with the seed, then loop: act, step, add up reward, stop on terminated or truncated
    obs, info = env.reset(seed=seed)
    total_reward, steps = 0.0, 0
    while True:
        action = policy(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        steps += 1
        if terminated or truncated:
            break
    return total_reward, steps
    # <<< SOLUTION


checks.part_b(run_episode)

# %% [markdown]
# ## Part C — memorising is not learning
#
# Now the ice is **slippery**: each action only goes where you intended a third of the time.
#
# `envs.lucky_sequence(seed)` plays the slippery lake from one particular seed until an
# episode happens to win, and writes down the exact actions of that winning episode.
# `envs.OpenLoopPolicy` then replays that list blindly. It never looks at the observation.
#
# We will measure this replay policy's success rate in two worlds:
#
# - **replayed**: every episode is reset with the *same* seed the sequence was found on;
# - **fresh**: every episode gets a *new* seed, so the slips land differently each time.
#
# **TODO — predict before you run.** Set `my_prediction` to one of the keys below.

# %%
CHOICES = {
    "both-high": "the sequence wins most of the time in both worlds",
    "replayed-only": "it wins almost always when replayed, and rarely when fresh",
    "fresh-only": "it wins rarely when replayed, and often when fresh",
    "both-low": "it rarely wins in either world",
}
my_prediction = "replayed-only"  # >>> ANSWER

predict.commit(LAB, "memorise", my_prediction, CHOICES)

# %%
SEED = 7
memorised = envs.OpenLoopPolicy(envs.lucky_sequence(SEED))
slippery = envs.make_frozen_lake(slippery=True)


def success_rate(seeds):
    wins = 0
    for s in seeds:
        memorised.reset()
        total_reward, _ = run_episode(slippery, memorised, seed=s)
        wins += total_reward == 1.0
    return wins / len(seeds)


replayed = success_rate([SEED] * 300)
fresh = success_rate(range(1000, 1300))
print(f"replayed randomness: {replayed:.0%} of episodes reach the goal")
print(f"fresh randomness:    {fresh:.0%} of episodes reach the goal")

predict.reveal(LAB, "memorise", f"replayed {replayed:.0%}, fresh {fresh:.0%}", correct="replayed-only")
checks.part_c(replayed, fresh)

# %% [markdown]
# A score of 100% that collapses the moment the dice are re-rolled is a lookup table, not a
# strategy. This is exactly why the real environment samples its safety cars fresh every
# episode: if they were replayed from a handful of fixed scenarios, an agent could score well
# by memorising "the safety car comes on lap 12" and would have learned nothing about racing.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
