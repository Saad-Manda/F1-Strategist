# %% [markdown]
# # Lab p8-02 · Best responses, cycles, and fictitious play
#
# **Goes with:** Phase 8, page 02 — Nash equilibria and fictitious self-play · **Time:** about 20 minutes
#
# Page 02's argument in three steps: best-responding to the opponent's *latest* move can chase
# forever; best-responding to the *average* of everything the opponent has played (fictitious
# play) settles on an equilibrium; and "how far from an equilibrium" has a number, exploitability.
# You write the three functions and run them on three small games, one of which does not do what
# a first glance suggests.
#
# **Games:** `labs/labkit/games.py`. U[i, j] is the row player's payoff; the column player gets
# −U[i, j]. Row maximises, column minimises.
#
# Stuck? Run `python -m labs hint p8-02` in a terminal.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import checks
from labs.labkit import games, predict

LAB = "p8-02"
for name, U, labels in (("matching pennies", games.MATCHING_PENNIES, games.PENNIES_NAMES),
                        ("rock-paper-scissors", games.RPS, games.RPS_NAMES),
                        ("page 02's old R/P game", games.DOMINATED, games.DOMINATED_NAMES)):
    print(f"{name}  (rows and columns: {', '.join(labels)})\n{U}\n")

# %% [markdown]
# ## Part A — best response and exploitability
#
# **TODO 1.** `best_response(U, opp_mix, player)`: the index of the best pure action for
# `player` ("row" or "col") against the opponent's mixed strategy `opp_mix`. Row's expected
# payoffs are `U @ opp_mix`; column's are minus `opp_mix @ U`. On a tie take the lowest index.
#
# **TODO 2.** `exploitability(U, row_mix, col_mix)`: what row could gain by switching to its best
# response, plus what column could gain by switching to its. Zero exactly at an equilibrium.

# %%
def best_response(U, opp_mix, player):
    # >>> SOLUTION: argmax of U @ opp_mix for row; argmin of opp_mix @ U for column
    if player == "row":
        return int(np.argmax(U @ opp_mix))
    return int(np.argmin(opp_mix @ U))
    # <<< SOLUTION


def exploitability(U, row_mix, col_mix):
    v = row_mix @ U @ col_mix
    # >>> SOLUTION: (best row payoff against col_mix - v) + (v - lowest payoff column can hold row to)
    return float(((U @ col_mix).max() - v) + (v - (row_mix @ U).min()))
    # <<< SOLUTION


checks.part_a(best_response, exploitability)

# %% [markdown]
# **Predict.** Page 02 (as first written) worked its example on the R/P game printed above and
# said best-responding to the latest move would chase forever. Look at the matrix before running.

# %%
CHOICES = {
    "cycle": "it cycles: R and P chase each other forever",
    "settle": "it settles at once, on (P, P), and stays there",
    "mix": "it ends up alternating evenly, 50/50",
}
my_prediction = "settle"  # >>> ANSWER
predict.commit(LAB, "cycle", my_prediction, CHOICES)

# %% [markdown]
# ## Part B — chasing the latest move
#
# **TODO 3.** `latest_only(U, start, rounds)`: start from the pure pair `start`; each round the
# row player best-responds to the column player's last action, then the column player
# best-responds to that new row action. Return the list of (row, col) pairs.

# %%
def latest_only(U, start, rounds):
    i, j = start
    out = []
    # >>> SOLUTION: best responses to one-hot vectors of the other's last action, row first
    for _ in range(rounds):
        i = best_response(U, games.pure(U.shape[1], j), "row")
        j = best_response(U, games.pure(U.shape[0], i), "col")
        out.append((i, j))
    # <<< SOLUTION
    return out


periods = {}
for name, U, labels in (("old R/P", games.DOMINATED, games.DOMINATED_NAMES), ("pennies", games.MATCHING_PENNIES, games.PENNIES_NAMES),
                        ("RPS", games.RPS, games.RPS_NAMES)):
    seq = latest_only(U, (0, 0), 24)
    periods[name] = games.find_period(seq)
    print(f"{name:8s}: " + " ".join(f"({labels[i]},{labels[j]})" for i, j in seq[:8]) + f" ...   repeats every {periods[name]}")
predict.reveal(LAB, "cycle", f"old R/P settles on (P, P) at once (period {periods['old R/P']})", correct="settle")
checks.part_b(periods)

# %% [markdown]
# Paper beats Rock and ties Paper; Rock ties Rock and loses to Paper. Whatever the column player
# does, P is better for the row player than R: P **dominates** R. There is nothing to chase. The
# only equilibrium is (P, P), not page 02's old 50/50. Matching pennies and RPS have no action that
# is best against everything, and that is what makes best-responding to the latest move cycle.

# %% [markdown]
# ## Part C — fictitious play
#
# **TODO 4.** `fictitious_play(U, iters)`: keep counts of how often each player has played each
# action (start both at action 0, count 1). Each round, each player best-responds to the *other's
# empirical frequencies* (counts / total) and adds one to that action's count. Record the
# exploitability of the two empirical frequencies after every round. Return (row_freq, col_freq,
# list of exploitabilities).

# %%
def fictitious_play(U, iters):
    cr, cc = games.pure(U.shape[0], 0), games.pure(U.shape[1], 0)
    trace = []
    # >>> SOLUTION: both best-respond to the other's frequencies, add to counts, record exploitability
    for _ in range(iters):
        cr[best_response(U, cc / cc.sum(), "row")] += 1
        cc[best_response(U, cr / cr.sum(), "col")] += 1
        trace.append(exploitability(U, cr / cr.sum(), cc / cc.sum()))
    # <<< SOLUTION
    return cr / cr.sum(), cc / cc.sum(), trace


results = {}
fig, ax = plt.subplots(figsize=(6, 3.5))
for name, U in (("pennies", games.MATCHING_PENNIES), ("RPS", games.RPS)):
    r, c, tr = fictitious_play(U, 2000)
    results[name] = (r, c, tr)
    ax.loglog(range(1, 2001), tr, label=name)
    print(f"{name:8s}: row plays {np.round(r, 3)}, column {np.round(c, 3)}; exploitability {tr[9]:.3f} after 10 rounds, {tr[-1]:.4f} after 2,000")
ax.set_xlabel("round"); ax.set_ylabel("exploitability of the averages"); ax.legend(); plt.show()
checks.part_c(results)

# %% [markdown]
# The *play* in fictitious play still jumps from one pure action to another, every round. What
# converges is the **average**: the frequencies close in on 50/50 and on 1/3 each, and the
# exploitability of the averages falls roughly like one over the number of rounds. The checkpoint
# pool on page 03 is the plan's stand-in for that average: it cannot average network weights, so it
# keeps past policies and samples them.
