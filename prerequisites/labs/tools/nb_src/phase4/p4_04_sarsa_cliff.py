# %% [markdown]
# # Lab p4-04 · SARSA on the cliff
#
# **Goes with:** Phase 4, page 04 — On-policy vs. off-policy: SARSA · **Time:** about 20 minutes
#
# The page's worked example is a three-episode miniature of a famous experiment. Here you run
# the real one: implement SARSA's update, predict what each algorithm will learn, and watch
# them disagree.
#
# **Environment:** Cliff Walking, from Sutton & Barto, Example 6.6.
#
# ```
# . . . . . . . . . . . .      row 0
# . . . . . . . . . . . .      row 1
# . . . . . . . . . . . .      row 2   <- the row along the cliff edge
# S C C C C C C C C C C G      row 3   S = start, G = goal, C = cliff
# ```
#
# Every move costs −1. Stepping onto the cliff costs −100 and sends you back to the start.
# The shortest route runs along row 2, right beside the cliff: 13 moves. A state is a
# `(row, col)` pair, and the table `Q[row, col, action]` has four actions per cell.
#
# Stuck? Run `python -m labs hint p4-04` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import envs, predict
from labs.labkit.envs import CLIFF_COLS, CLIFF_GOAL, CLIFF_ROWS, CLIFF_START

LAB = "p4-04"

# %% [markdown]
# ## Part A — the one term that differs
#
# Q-learning's update, written for this table. It is given, so you can see what yours has to
# differ from:

# %%
def q_learning_update(Q, s, a, r, s2, a2, done, alpha):
    """Off-policy: the target uses the BEST next action, whatever a2 turns out to be."""
    target = r if done else r + Q[s2].max()
    Q[s][a] += alpha * (target - Q[s][a])

# %% [markdown]
# **TODO 1.** Implement `sarsa_update`. It receives the same arguments. `a2` is the action the
# agent has already chosen to take next, in state `s2`. SARSA's target uses the value of
# **that** action. When `done` is True nothing follows, exactly as above. (γ is 1 here.)

# %%
def sarsa_update(Q, s, a, r, s2, a2, done, alpha):
    """On-policy: the target uses the next action that will actually be taken."""
    # >>> SOLUTION: the same two lines as q_learning_update, with Q[s2][a2] in place of Q[s2].max()
    target = r if done else r + Q[s2][a2]
    Q[s][a] += alpha * (target - Q[s][a])
    # <<< SOLUTION


checks.update(sarsa_update)

# %% [markdown]
# ## Part B — predict, then run
#
# Both learners will train for 500 episodes with ε fixed at 0.1 and α = 0.5, on identical
# seeds. Two routes are possible:
#
# - the **edge route** along row 2: shortest, and one exploratory step from the cliff the
#   whole way;
# - a **safe route** up and over through rows 0 or 1: a few moves longer, well clear of it.
#
# **TODO — predict before you run.** Which statement will turn out true?

# %%
CHOICES = {
    "q-edge-wins": "Q-learning walks the edge and scores better during training",
    "q-edge-loses": "Q-learning walks the edge and scores worse during training",
    "sarsa-edge-wins": "SARSA walks the edge and scores better during training",
    "same": "both learn the same route and score the same",
}
my_prediction = "q-edge-loses"  # >>> ANSWER

predict.commit(LAB, "routes", my_prediction, CHOICES)

# %%
def choose(Q, s, epsilon, rng):
    """ε-greedy over the four moves, breaking ties between equal values at random."""
    if rng.random() < epsilon:
        return int(rng.integers(4))
    return int(rng.choice(np.flatnonzero(Q[s] == Q[s].max())))


def train(update, epsilon, seed, episodes=500, alpha=0.5):
    """Returns (reward of each episode, share of late-training moves made in each row, Q)."""
    rng = np.random.default_rng(seed)
    Q = np.zeros((CLIFF_ROWS, CLIFF_COLS, 4))
    rewards, row_visits = [], np.zeros(CLIFF_ROWS)
    for episode in range(episodes):
        s, total, done = CLIFF_START, 0.0, False
        a = choose(Q, s, epsilon, rng)
        while not done:
            s2, r, done = envs.cliff_step(s, a)
            a2 = choose(Q, s2, epsilon, rng)
            update(Q, s, a, r, s2, a2, done, alpha)
            total += r
            if episode >= episodes - 100:
                row_visits[s[0]] += 1
            s, a = s2, a2
        rewards.append(total)
    return np.array(rewards), row_visits / row_visits.sum(), Q


def summarise(update, epsilon, seeds=range(6)):
    runs = [train(update, epsilon, seed) for seed in seeds]
    rewards = np.mean([r for r, _, _ in runs], axis=0)
    rows = np.mean([v for _, v, _ in runs], axis=0)
    return rewards, rows


results = {}
for name, update in (("Q-learning", q_learning_update), ("SARSA", sarsa_update)):
    rewards, rows = summarise(update, epsilon=0.1)
    results[name] = {"late_reward": float(rewards[-100:].mean()), "edge_share": float(rows[2]), "curve": rewards}
    print(f"{name:<10}  reward per episode, last 100: {results[name]['late_reward']:7.1f}"
          f"    moves made on the edge row, last 100: {results[name]['edge_share']:.0%}")

plt.figure(figsize=(7, 3.5))
for name in results:
    smooth = np.convolve(results[name]["curve"], np.ones(20) / 20, mode="valid")
    plt.plot(smooth, label=name)
plt.ylim(-120, 0)
plt.xlabel("episode")
plt.ylabel("reward per episode (20-episode average)")
plt.legend()
plt.show()

predict.reveal(LAB, "routes", "Q-learning spends its time on the edge row and collects less reward while training", correct="q-edge-loses")
checks.compare(results)

# %% [markdown]
# Q-learning learned the shortest route and is right that it is the best one **for an agent
# that never explores**. But this agent still takes a random move one time in ten, and on
# the edge row a random move is often a fall. Its target, `max`, never sees that.
#
# SARSA's target is the value of the move it will really make, random ones included. Cells
# next to the cliff are therefore worth less to it, and it learns to keep its distance. It is
# answering a different question: not "what is the best route" but "what is the best route
# for me, as I currently behave".
#
# ## Part C — turn exploration down
#
# If the difference comes from exploration, it should shrink as ε does.
#
# **TODO — predict before you run.** At ε = 0.01, the gap in reward per episode between the
# two will be

# %%
CHOICES = {
    "same-gap": "about as large as at ε = 0.1",
    "small": "much smaller: they nearly agree",
    "reversed": "reversed: Q-learning clearly ahead",
}
my_prediction = "small"  # >>> ANSWER

predict.commit(LAB, "low-epsilon", my_prediction, CHOICES)

# %%
low = {}
for name, update in (("Q-learning", q_learning_update), ("SARSA", sarsa_update)):
    rewards, rows = summarise(update, epsilon=0.01)
    low[name] = float(rewards[-100:].mean())
    print(f"{name:<10}  reward per episode, last 100, at ε = 0.01: {low[name]:7.1f}")

gap_high = results["SARSA"]["late_reward"] - results["Q-learning"]["late_reward"]
gap_low = low["SARSA"] - low["Q-learning"]
predict.reveal(LAB, "low-epsilon", f"the gap went from {gap_high:.1f} at ε = 0.1 to {gap_low:.1f} at ε = 0.01", correct="small")
checks.low_epsilon(gap_high, gap_low)

# %% [markdown]
# With almost no exploration there is almost nothing for SARSA to be cautious about, and the
# two agree. In the limit ε = 0, SARSA's "the action I will take" **is** the best action, and
# the two updates are the same line of code.
#
# For the real project this means the two agents should be compared as trained (what did
# each learn while exploring?) and again with exploration switched off. A difference in the
# first and not the second is this effect, and not a bug in either.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
