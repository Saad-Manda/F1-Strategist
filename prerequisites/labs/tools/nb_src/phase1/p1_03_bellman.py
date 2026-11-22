# %% [markdown]
# # Lab p1-03 · Bellman backups
#
# **Goes with:** Phase 1, page 03 — Value functions and the Bellman equations · **Time:** about 20 minutes
#
# You will implement the Bellman backup, use it to compute a value function exactly, read a
# policy off that value function, and then test the page's reward-centring proof to find out
# which of its assumptions is doing the work.
#
# **Environment:** the 4×4 GridWorld from Sutton & Barto, Example 4.1.
#
# ```
#  T  1  2  3      16 cells numbered 0..15, row by row
#  4  5  6  7      T = terminal corners (cells 0 and 15)
#  8  9 10 11      every move costs -1
# 12 13 14  T      walking into a wall leaves you in place (and still costs -1)
# ```
#
# Unlike a learning agent, here you are handed the **model**:
# `model[s][a]` is a list of `(prob, next_state, reward, done)` outcomes for taking action
# `a` in state `s`. Actions are `G_UP, G_DOWN, G_LEFT, G_RIGHT` = 0, 1, 2, 3.
#
# Stuck? Run `python -m labs hint p1-03` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import numpy as np

import checks
from labs.labkit import envs, predict

LAB = "p1-03"
model = envs.gridworld_model()
N_STATES, N_ACTIONS = 16, 4

print("model[5][envs.G_UP]  =", model[5][envs.G_UP], "  <- from cell 5, UP lands in cell 1")
print("model[1][envs.G_LEFT] =", model[1][envs.G_LEFT], " <- from cell 1, LEFT reaches the terminal corner")

# %% [markdown]
# ## Part A — one backup, then a whole value function
#
# The page's Bellman equation for a fixed policy π, written for the state value:
#
# ```
# V(s) = Σ_a π(a|s) · Σ_outcomes prob · [ reward + γ · V(next_state) ]
# ```
#
# with one detail the page states in words: **nothing follows a terminal step**, so when an
# outcome has `done = True` its `V(next_state)` term is dropped.
#
# **TODO 1.** Implement `bellman_backup`: the right-hand side above, for one state.
# `policy[s]` is a list of four action probabilities.

# %%
def bellman_backup(V, s, policy, model, gamma):
    """The Bellman right-hand side for state s under `policy`. Returns a float."""
    # >>> SOLUTION: sum over actions (weighted by the policy) and outcomes (weighted by prob) of reward + gamma * V[next], dropping V[next] when done
    total = 0.0
    for a, action_prob in enumerate(policy[s]):
        for prob, s2, reward, done in model[s][a]:
            total += action_prob * prob * (reward + (0.0 if done else gamma * V[s2]))
    return total
    # <<< SOLUTION


checks.backup(bellman_backup)

# %% [markdown]
# **TODO 2.** Implement `evaluate_policy`: start from `V = 0` everywhere and keep sweeping
# over all states, replacing each `V[s]` with its backup, until the largest change in a
# sweep is below `tol`. Return `V` as a NumPy array.
#
# This is the equation being *solved* by repetition. No episodes are played and nothing is
# sampled; that is only possible because the model is known.

# %%
def evaluate_policy(policy, model, gamma=1.0, tol=1e-6):
    """Iterate the Bellman backup to convergence. Returns V as an array of length n_states."""
    # >>> SOLUTION: V = zeros; repeat sweeps of V[s] = bellman_backup(...) until the biggest change in a sweep is below tol
    V = np.zeros(len(model))
    while True:
        biggest_change = 0.0
        for s in range(len(model)):
            new_value = bellman_backup(V, s, policy, model, gamma)
            biggest_change = max(biggest_change, abs(new_value - V[s]))
            V[s] = new_value
        if biggest_change < tol:
            return V
    # <<< SOLUTION


random_policy = [[0.25] * N_ACTIONS for _ in range(N_STATES)]
V_random = evaluate_policy(random_policy, model)
print(np.round(V_random.reshape(4, 4), 1))
checks.evaluation(V_random)

# %% [markdown]
# Read the table. Cell 3 (top-right) is worth about −22: wandering at random from there, it
# takes 22 steps on average to stumble into a corner. That is what "the value of a state
# under a policy" means: the expected return from there, following that policy.
#
# ## Part B — from values to a policy
#
# The page says a table of values "directly gives you a policy for free". Make that concrete.
#
# **TODO 3.** Implement `greedy_policy`: for each state, the action whose one-step lookahead
# `Σ prob · [reward + γ·V(next)]` is largest. Return a list with one action per state
# (break ties toward the lower action number).

# %%
def greedy_policy(V, model, gamma=1.0):
    """For every state, the action with the best one-step lookahead on V. Returns a list of ints."""
    # >>> SOLUTION: for each state compute each action's lookahead value and take the argmax
    actions = []
    for s in range(len(model)):
        lookahead = []
        for a in range(len(model[s])):
            lookahead.append(sum(prob * (reward + (0.0 if done else gamma * V[s2])) for prob, s2, reward, done in model[s][a]))
        actions.append(int(np.argmax(lookahead)))
    return actions
    # <<< SOLUTION


greedy = greedy_policy(V_random, model)
ARROWS = "↑↓←→"
print("\n".join(" ".join("T" if s in envs.GRID_TERMINALS else ARROWS[greedy[s]] for s in range(r * 4, r * 4 + 4)) for r in range(4)))
checks.greedy(greedy)

# %% [markdown]
# Every arrow heads for a corner by a shortest route, even though `V_random` was the value of
# a policy that moves at *random*. Evaluating a bad policy and then acting greedily on its
# values already gives a much better one.
#
# ## Part C — when is it safe to shift the reward?
#
# The page proves that subtracting a constant from every step's reward cannot change which
# policy is optimal, and uses that to justify `reward_offset="base_pace"`. The proof has one
# assumption: **every episode has the same length**.
#
# Test it. We add a constant **+2** to every step's reward (so each step pays +1 instead of
# −1) and recompute the exactly optimal first move in every state, in two worlds:
#
# - **fixed-length:** the same grid, no terminal cells, every episode lasts exactly 6 steps
#   (entering a corner costs 0, entering any other cell costs −1);
# - **ends-early:** the GridWorld above, where reaching a corner ends the episode.
#
# **TODO — predict before you run.** In which world does the optimal policy change?

# %%
CHOICES = {
    "neither": "the optimal policy is unchanged in both worlds",
    "fixed-length": "it changes only in the fixed-length world",
    "ends-early": "it changes only in the world where episodes can end early",
    "both": "it changes in both worlds",
}
my_prediction = "ends-early"  # >>> ANSWER

predict.commit(LAB, "shift", my_prediction, CHOICES)

# %%
HORIZON, SHIFT = 6, 2.0
changed = {}
for name, world in [("fixed-length", envs.fixed_length_model()), ("ends-early", envs.gridworld_model())]:
    before = envs.optimal_first_actions(world, HORIZON, shift=0.0)
    after = envs.optimal_first_actions(world, HORIZON, shift=SHIFT)
    changed[name] = before != after
    print(f"{name:<13} optimal policy changed by the shift: {changed[name]}")
    if changed[name]:
        s = 1
        show = lambda acts: "/".join(ARROWS[a] for a in sorted(acts))
        print(f"{'':<13} e.g. in cell {s} (next to a corner): best move was {show(before[s])}, is now {show(after[s])}")

outcome = "ends-early" if changed["ends-early"] and not changed["fixed-length"] else str(changed)
predict.reveal(LAB, "shift", f"changed only in: {outcome}", correct="ends-early")
checks.shift(changed)

# %% [markdown]
# In the fixed-length world the shift adds exactly `2 × 6` to *every* policy's return, so it
# cancels out of every comparison, which is the page's proof.
#
# In the ends-early world a policy that finishes in 1 step collects the shift once, and a
# policy that dawdles for 6 steps collects it six times. The "constant" is no longer the same
# for every policy, so it does not cancel: with +1 per step, the best plan is to *avoid* the
# goal for as long as possible.
#
# This is why the real environment can centre its reward safely: a race is always exactly
# `total_laps` long. The same trick applied to an environment with variable-length episodes
# would quietly change what the agent is being asked to do.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
