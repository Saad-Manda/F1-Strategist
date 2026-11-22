"""Checks for lab p1-03. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np

from labs.labkit import envs
from labs.labkit.checks import close, passed, require

LAB = "p1-03"

# Sutton & Barto, Figure 4.1: values of the uniform random policy
TEXTBOOK = np.array([0, -14, -20, -22, -14, -18, -20, -20, -20, -20, -18, -14, -22, -20, -14, 0], dtype=float)


def backup(bellman_backup):
    model = envs.gridworld_model()
    uniform = [[0.25] * 4 for _ in range(16)]
    zeros = np.zeros(16)

    got = bellman_backup(zeros, 5, uniform, model, 1.0)
    require(close(got, -1.0), f"With V = 0 everywhere, one backup of an interior cell is just the expected immediate reward, -1. Got {got}.")

    V = np.arange(16, dtype=float)
    want = -1.0 + 0.25 * (V[1] + V[9] + V[4] + V[6])
    got = bellman_backup(V, 5, uniform, model, 1.0)
    require(close(got, want), f"For cell 5 with V[s] = s the backup should be {want}, got {got}. Each of the four moves has probability 0.25.")

    got = bellman_backup(V, 5, uniform, model, 0.5)
    require(close(got, -1.0 + 0.5 * 0.25 * (V[1] + V[9] + V[4] + V[6])), "gamma should multiply the next state's value, and only that.")

    only_left = [[0.0, 0.0, 1.0, 0.0] for _ in range(16)]
    V_big = np.full(16, 100.0)
    got = bellman_backup(V_big, 1, only_left, model, 1.0)
    require(
        close(got, -1.0),
        f"Moving from cell 1 into the terminal corner should be worth exactly its reward, -1: nothing follows a terminal step. Got {got}, "
        "which means the terminal cell's value was added in.",
    )
    passed(LAB, "backup", "TODO 1: the backup weights actions and outcomes correctly and stops at terminal steps.")


def evaluation(V):
    V = np.asarray(V, dtype=float)
    require(V.shape == (16,), f"evaluate_policy should return one value per state (16), got shape {V.shape}.")
    require(close(V[0], 0) and close(V[15], 0), "Terminal cells have value 0: no reward is ever collected from them.")
    worst = np.max(np.abs(V - TEXTBOOK))
    require(worst < 0.01, f"Values should match the textbook table for the random policy within 0.01; the largest difference is {worst:.3f}.")
    passed(LAB, "evaluation", "TODO 2: your values match Sutton & Barto's Figure 4.1 (-14, -20, -22, ...).")


def greedy(actions):
    model = envs.gridworld_model()
    require(len(actions) == 16, "greedy_policy should return one action per state.")
    for start in range(16):
        s, steps = start, 0
        while s not in envs.GRID_TERMINALS and steps < 10:
            s = model[s][int(actions[s])][0][1]
            steps += 1
        row, col = divmod(start, 4)
        shortest = min(row + col, (3 - row) + (3 - col))
        require(s in envs.GRID_TERMINALS, f"Following your greedy policy from cell {start} never reaches a corner.")
        require(steps == shortest, f"From cell {start} the greedy policy took {steps} steps; the shortest route is {shortest}.")
    passed(LAB, "greedy", "TODO 3: acting greedily on the random policy's values reaches a corner by a shortest route from every cell.")


def shift(changed):
    require(changed.get("fixed-length") is False, "In the fixed-length world the shift must not change the optimal policy.")
    require(changed.get("ends-early") is True, "In the ends-early world the shift should change the optimal policy.")
    passed(LAB, "C", "Part C: a constant shift is harmless only when every episode has the same length.")
