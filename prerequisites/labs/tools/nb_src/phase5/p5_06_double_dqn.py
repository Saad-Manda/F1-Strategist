# %% [markdown]
# # Lab p5-06 · Who chooses, who scores
#
# **Goes with:** Phase 5, page 06 — Double DQN · **Time:** about 20 minutes
#
# Page 06 makes three claims. A max over noisy estimates runs high even when no estimate is
# biased. Letting one estimator choose and another score removes that. And the fix fits in a
# batch target alongside the mask and the terminal cut-off. Here you check each one: the first
# by simulation, the second on page 06's own batch of three, the third on the textbook problem
# built to show the bias doing damage.
#
# Stuck? Run `python -m labs hint p5-06` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import predict

LAB = "p5-06"

# %% [markdown]
# ## Part A — the bias, by simulation
#
# Page 06's example: every action's true value is 5, and each estimate is 4 or 6 with equal
# chance. Two independent sets of estimates, A and B, are drawn for every trial.
#
# **TODO 1.** Finish `best_value_estimates`. For each trial, report two numbers:
#
# - **single:** the largest of A's estimates (one estimator chooses *and* scores)
# - **double:** B's estimate of the action that A rated highest (A chooses, B scores)
#
# Return the average of each over all trials.

# %%
def best_value_estimates(n_actions, trials, rng, true_value=5.0):
    """Returns (average single-estimator value, average double-estimator value) of the best action."""
    A = true_value + rng.choice([-1.0, 1.0], size=(trials, n_actions))
    B = true_value + rng.choice([-1.0, 1.0], size=(trials, n_actions))
    # >>> SOLUTION: single is A.max per row; double reads B at A's argmax per row; return both means
    single = A.max(axis=1)
    double = B[np.arange(trials), A.argmax(axis=1)]
    return float(single.mean()), float(double.mean())
    # <<< SOLUTION


rng = np.random.default_rng(0)
for n in (1, 3, 6):
    single, double = best_value_estimates(n, 40_000, rng)
    print(f"{n} action(s): true best value 5.00   single estimator {single:.3f}   double estimator {double:.3f}")
checks.bias(best_value_estimates)

# %% [markdown]
# With one action there is nothing to choose, so there is no bias. With three, the single
# estimator reports page 06's 5.75. With six, the real agent's number of actions, it reports
# nearly 6: one of six coin flips almost always lands high, and max always finds it. The
# double estimator stays at 5 however many actions there are.
#
# ## Part B — the batch target
#
# **TODO 2.** Implement `double_targets` for a batch, page 06's three-step recipe in NumPy:
#
# 1. take the online network's next-state values and set illegal actions to `−inf`
# 2. `a* = argmax` of that, row by row (this is the **choice**)
# 3. read the target network's value at `a*`, row by row (this is the **score**), and build
#    `r + γ · score · (1 − done)`
#
# `vanilla_targets` is given for comparison: the target network chooses and scores.

# %%
def vanilla_targets(rewards, dones, online_next, target_next, legal_next, gamma=1.0):
    """r + γ · max over legal a' of the TARGET network's values · (1 − done)."""
    masked = np.where(legal_next, target_next, -np.inf)
    return rewards + gamma * masked.max(axis=1) * (1.0 - dones)


def double_targets(rewards, dones, online_next, target_next, legal_next, gamma=1.0):
    """r + γ · Q_target(s', a*) · (1 − done), with a* = argmax over legal a' of Q_online(s', a')."""
    # >>> SOLUTION: mask online_next with -inf, argmax per row, gather from target_next, terminal cut-off
    chosen = np.where(legal_next, online_next, -np.inf).argmax(axis=1)
    score = target_next[np.arange(len(rewards)), chosen]
    return rewards + gamma * score * (1.0 - dones)
    # <<< SOLUTION


# page 06's batch of three
PAGE_BATCH = dict(
    rewards=np.array([-5.0, -6.0, -4.0]),
    dones=np.array([0.0, 0.0, 1.0]),
    online_next=np.array([[-40.0, -38.0, -45.0], [-30.0, -22.0, -35.0], [-9.0, -7.0, -8.0]]),
    target_next=np.array([[-41.0, -42.0, -44.0], [-31.0, -20.0, -36.0], [-9.0, -6.0, -8.0]]),
    legal_next=np.array([[True, True, True], [True, False, True], [True, True, True]]),
)
print("double DQN targets: ", double_targets(**PAGE_BATCH))
print("vanilla targets:    ", vanilla_targets(**PAGE_BATCH))
checks.batch(double_targets, PAGE_BATCH)

# %% [markdown]
# Row 1 is one unit less optimistic than vanilla, as the page says. Row 2 is built on a legal
# action even though the online network rated the illegal one highest. Row 3 is the reward
# alone. The real `update()` does exactly this with 64 rows, using `gather` where you used
# NumPy indexing.
#
# ## Part C — where the bias does damage
#
# Sutton and Barto's Example 6.7, the maximization-bias MDP. Every episode starts in state A
# with two actions:
#
# - **right:** the episode ends, reward 0
# - **left:** move to state B, reward 0. B has 10 actions, each ending the episode with a
#   reward drawn from a normal distribution with mean **−0.1** and spread 1
#
# Going left is worse on average, by 0.1. But B's ten noisy estimates make `max over B`
# look positive early on, and that optimism is copied straight into A's value for "left".
# Both learners use ε = 0.1, α = 0.1, γ = 1. The best achievable rate of going left is 5%,
# the exploration rate's random half.
#
# Q-learning's update is given. **TODO 3.** Write the Double Q-learning update: keep two
# tables. On each update flip a fair coin to pick which table learns. The learning table
# **chooses** the best next action, the other table **scores** it. Acting uses the sum of
# both tables.

# %%
N_B = 10
A_STATE, B_STATE, END = "A", "B", None
LEFT, RIGHT = 0, 1


def fresh_table():
    return {A_STATE: np.zeros(2), B_STATE: np.zeros(N_B)}


def step(state, action, rng):
    """The MDP. Returns (reward, next state, done)."""
    if state == A_STATE:
        return (0.0, B_STATE, False) if action == LEFT else (0.0, END, True)
    return float(rng.normal(-0.1, 1.0)), END, True


def epsilon_greedy(values, rng, eps=0.1):
    if rng.random() < eps:
        return int(rng.integers(len(values)))
    return int(rng.choice(np.flatnonzero(values == values.max())))


def q_learning_update(tables, state, action, reward, next_state, done, rng, alpha=0.1):
    """Given. One table: target = r + max over the next state's values."""
    Q = tables[0]
    target = reward if done else reward + Q[next_state].max()
    Q[state][action] += alpha * (target - Q[state][action])


def double_q_update(tables, state, action, reward, next_state, done, rng, alpha=0.1):
    """Two tables. A coin flip (rng.random() < 0.5) picks which one learns."""
    # >>> SOLUTION: pick learner i and other j by coin flip; target = r (done) or r + Q_j[next][argmax Q_i[next]]; move Q_i[state][action]
    i = int(rng.random() < 0.5)
    learn, other = tables[i], tables[1 - i]
    if done:
        target = reward
    else:
        target = reward + other[next_state][int(np.argmax(learn[next_state]))]
    learn[state][action] += alpha * (target - learn[state][action])
    # <<< SOLUTION


def left_rate(update, n_tables, episodes=300, runs=200):
    """Share of runs that go left from A, episode by episode."""
    lefts = np.zeros(episodes)
    for run in range(runs):
        rng = np.random.default_rng(run)
        tables = [fresh_table() for _ in range(n_tables)]
        for ep in range(episodes):
            state, done = A_STATE, False
            while not done:
                values = sum(t[state] for t in tables)
                action = epsilon_greedy(values, rng)
                if state == A_STATE:
                    lefts[ep] += action == LEFT
                reward, next_state, done = step(state, action, rng)
                update(tables, state, action, reward, next_state, done, rng)
                state = next_state
    return lefts / runs


checks.double_update(double_q_update, fresh_table)

# %% [markdown]
# **TODO — predict before you run.** Over episodes 10 to 30, roughly how often does
# Q-learning go left?

# %%
CHOICES = {
    "near-5": "about 5%: going left is worse, and the learner can see that from the rewards",
    "near-50": "about half: it cannot tell the two apart yet",
    "most": "most of the time",
}
my_prediction = "most"  # >>> ANSWER

predict.commit(LAB, "left", my_prediction, CHOICES)

# %%
single = left_rate(q_learning_update, 1)
double = left_rate(double_q_update, 2)
plt.figure(figsize=(8, 3.5))
plt.plot(single * 100, label="Q-learning")
plt.plot(double * 100, label="Double Q-learning")
plt.axhline(5, color="gray", linestyle="--", label="best possible, 5%")
plt.xlabel("episode")
plt.ylabel("% of runs going left from A")
plt.legend()
plt.show()
early = slice(10, 31)
print(f"episodes 10-30:  Q-learning goes left {single[early].mean():.0%} of the time, Double Q-learning {double[early].mean():.0%}")
print(f"last 50 episodes: Q-learning {single[-50:].mean():.0%}, Double Q-learning {double[-50:].mean():.0%}")
predict.reveal(LAB, "left", f"Q-learning went left {single[early].mean():.0%} of the time in episodes 10-30", correct="most")
checks.mdp(single, double)

# %% [markdown]
# Q-learning goes left most of the time for dozens of episodes, choosing the action that is
# worse on average because a max over ten noisy numbers says it is better. Double Q-learning
# is fooled much less, and settles close to the best possible 5% much sooner.
#
# Map it onto the race. B's ten actions are the rarely tried pit stops: few visits, noisy
# estimates, exactly where page 06 says the bias is largest. A is the lap before, whose value
# inherits the optimism. With 52 laps that inheritance is chained 52 times.
#
# **Done.** Run `python -m labs status` in a terminal to tick this lab off.
