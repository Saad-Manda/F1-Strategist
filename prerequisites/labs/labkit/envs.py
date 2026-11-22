"""Small reference environments and models shared by more than one lab.

Everything here is given, complete code. Labs import it; nothing in this file is a TODO.
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np

# --------------------------------------------------------------------------- FrozenLake

LEFT, DOWN, RIGHT, UP = 0, 1, 2, 3  # FrozenLake's own action numbering


def make_frozen_lake(slippery: bool) -> gym.Env:
    """The classic 4x4 FrozenLake. Start top-left (state 0), goal bottom-right (state 15).

        S F F F
        F H F H        H = hole (episode ends, reward 0)
        F F F H        G = goal (episode ends, reward 1)
        H F F G
    """
    return gym.make("FrozenLake-v1", map_name="4x4", is_slippery=slippery)


# a sensible closed-loop policy for the slippery lake: one action per state
_LAKE_POLICY = [LEFT, UP, UP, UP, LEFT, LEFT, LEFT, LEFT, UP, DOWN, LEFT, LEFT, LEFT, RIGHT, DOWN, LEFT]


def lucky_sequence(seed: int, max_tries: int = 500) -> list[int]:
    """An action sequence that reaches the goal on the slippery lake *when reset with `seed`*.

    Found by playing episodes from that exact seed until one wins, then writing down the
    actions it took. It encodes nothing about the lake except what happened on that seed.
    """
    env = make_frozen_lake(slippery=True)
    for attempt in range(max_tries):
        rng = np.random.default_rng(attempt)
        obs, _ = env.reset(seed=seed)
        actions = []
        for _ in range(100):
            explore = attempt > 0 and rng.random() < 0.2
            action = int(rng.integers(4)) if explore else _LAKE_POLICY[obs]
            actions.append(action)
            obs, reward, terminated, truncated, _ = env.step(action)
            if terminated or truncated:
                break
        if reward == 1.0:
            return actions
    raise RuntimeError(f"no winning sequence found for seed {seed}")


class OpenLoopPolicy:
    """Replays a fixed list of actions and ignores the observation completely."""

    def __init__(self, actions: list[int]):
        self.actions = list(actions)
        self.t = 0

    def reset(self) -> None:
        self.t = 0

    def __call__(self, obs) -> int:
        action = self.actions[min(self.t, len(self.actions) - 1)]
        self.t += 1
        return action


# --------------------------------------------------------------------------- 4x4 GridWorld (S&B Example 4.1)

G_UP, G_DOWN, G_LEFT, G_RIGHT = 0, 1, 2, 3
GRID_N = 4
GRID_TERMINALS = (0, 15)


def _move(state: int, action: int) -> int:
    row, col = divmod(state, GRID_N)
    if action == G_UP:
        row = max(0, row - 1)
    elif action == G_DOWN:
        row = min(GRID_N - 1, row + 1)
    elif action == G_LEFT:
        col = max(0, col - 1)
    else:
        col = min(GRID_N - 1, col + 1)
    return row * GRID_N + col


def gridworld_model() -> list[list[list[tuple[float, int, float, bool]]]]:
    """Sutton & Barto Example 4.1 as a model: model[s][a] = [(prob, next_state, reward, done)].

    16 cells numbered row by row. Cells 0 and 15 are terminal. Every move costs -1; moving
    into a wall leaves you where you are (and still costs -1).
    """
    model = []
    for s in range(GRID_N * GRID_N):
        row = []
        for a in range(4):
            if s in GRID_TERMINALS:
                row.append([(1.0, s, 0.0, True)])
            else:
                s2 = _move(s, a)
                row.append([(1.0, s2, -1.0, s2 in GRID_TERMINALS)])
        model.append(row)
    return model


def fixed_length_model() -> list[list[list[tuple[float, int, float, bool]]]]:
    """The same grid with no terminal cells: an episode always lasts exactly `horizon` steps.

    Entering a corner cell (0 or 15) is free; entering any other cell costs -1.
    """
    model = []
    for s in range(GRID_N * GRID_N):
        row = []
        for a in range(4):
            s2 = _move(s, a)
            row.append([(1.0, s2, 0.0 if s2 in GRID_TERMINALS else -1.0, False)])
        model.append(row)
    return model


def optimal_first_actions(model, horizon: int, shift: float = 0.0) -> list[frozenset[int]]:
    """Exact optimal actions at the first step, for every state, over a `horizon`-step episode.

    `shift` is added to every step's reward. Returns, per state, the set of actions tied for
    best. (This is backward induction, the subject of the Phase 3.5 set; here it is a tool.)
    """
    n = len(model)
    value = np.zeros(n)
    best: list[frozenset[int]] = [frozenset()] * n
    for _ in range(horizon):
        new_value = np.zeros(n)
        for s in range(n):
            q = []
            for a in range(len(model[s])):
                total = 0.0
                for prob, s2, reward, done in model[s][a]:
                    # a terminal cell has no further steps, so no further (shifted) reward either
                    step_reward = 0.0 if (done and s2 == s) else reward + shift
                    total += prob * (step_reward + (0.0 if done else value[s2]))
                q.append(total)
            top = max(q)
            best[s] = frozenset(a for a, v in enumerate(q) if abs(v - top) < 1e-9)
            new_value[s] = top
        value = new_value
    return best


# --------------------------------------------------------------------------- Cliff Walking (S&B Example 6.6)

C_UP, C_RIGHT, C_DOWN, C_LEFT = 0, 1, 2, 3
CLIFF_ROWS, CLIFF_COLS = 4, 12
CLIFF_START, CLIFF_GOAL = (3, 0), (3, 11)


def cliff_step(position: tuple[int, int], action: int) -> tuple[tuple[int, int], float, bool]:
    """One move on the 4x12 cliff grid. Returns (next position, reward, done).

        . . . . . . . . . . . .      row 0
        . . . . . . . . . . . .      row 1
        . . . . . . . . . . . .      row 2   <- the row along the cliff edge
        S C C C C C C C C C C G      row 3   S = start, G = goal, C = cliff

    Every move costs -1. Stepping onto the cliff costs -100 and puts you back at the start
    (the episode goes on). Reaching G ends the episode. Walls leave you in place.
    """
    row, col = position
    if action == C_UP:
        row = max(0, row - 1)
    elif action == C_DOWN:
        row = min(CLIFF_ROWS - 1, row + 1)
    elif action == C_LEFT:
        col = max(0, col - 1)
    else:
        col = min(CLIFF_COLS - 1, col + 1)
    if row == 3 and 0 < col < CLIFF_COLS - 1:
        return CLIFF_START, -100.0, False
    return (row, col), -1.0, (row, col) == CLIFF_GOAL


# --------------------------------------------------------------------------- 1000-state random walk (S&B Example 9.1)

WALK_STATES = 1000
WALK_JUMP = 100
WALK_START = 500


def walk_step(state: int, rng: np.random.Generator) -> tuple[int, float, bool]:
    """One step of the random walk. States are 1..1000. Returns (next state, reward, done).

    From any state the walker jumps 1 to 100 states left or right, each of the 200 jumps
    equally likely. Jumping off the left end ends the episode with reward -1; off the right
    end, with reward +1. Every other step has reward 0. There are no actions.
    """
    jump = int(rng.integers(1, WALK_JUMP + 1)) * (1 if rng.random() < 0.5 else -1)
    nxt = state + jump
    if nxt < 1:
        return nxt, -1.0, True
    if nxt > WALK_STATES:
        return nxt, 1.0, True
    return nxt, 0.0, False


def walk_true_values() -> np.ndarray:
    """The exact value of each of the 1000 states (index 0 is state 1), from the known model."""
    n = WALK_STATES
    P = np.zeros((n, n))
    b = np.zeros(n)
    for s in range(1, n + 1):
        for d in range(1, WALK_JUMP + 1):
            for t in (s - d, s + d):
                if t < 1:
                    b[s - 1] -= 1 / (2 * WALK_JUMP)
                elif t > n:
                    b[s - 1] += 1 / (2 * WALK_JUMP)
                else:
                    P[s - 1, t - 1] += 1 / (2 * WALK_JUMP)
    return np.linalg.solve(np.eye(n) - P, b)


# --------------------------------------------------------------------------- corridor (lab p6-02)

LEFT_STEP, RIGHT_STEP = 0, 1


def corridor_step(state: int, action: int, n: int, kind: str) -> tuple[int, float, bool]:
    """A 1-D corridor of n cells, 0 to n - 1. Start at 0; reaching n - 1 ends the episode.

    Action 0 moves left (a wall at 0), action 1 moves right. Rewards:
        kind="dense"   -1 on every step: every step says "that cost you something"
        kind="sparse"  +1 on the step that reaches the end, 0 on every other step
    """
    nxt = max(0, state - 1) if action == LEFT_STEP else state + 1
    done = nxt == n - 1
    if kind == "dense":
        return nxt, -1.0, done
    return nxt, (1.0 if done else 0.0), done


# --------------------------------------------------------------------------- farming grid (lab p6-02)

FARM_SIZE, FARM_START, FARM_GOAL, FARM_TILE = 5, (0, 0), (4, 4), (2, 2)
FARM_GOAL_REWARD, FARM_RESPAWN, FARM_CAP = 10.0, 3, 40
_FARM_MOVES = ((-1, 0), (1, 0), (0, -1), (0, 1))


def farm_step(pos, timer, action, bonus):
    """One step on the 5x5 farming grid. Returns (pos, timer, reward, done, collected).

    Start top-left, goal (+10, ends the episode) bottom-right, a bonus tile in the middle worth
    `bonus` each time it is entered while available. Once taken, it comes back after 3 steps.
    """
    r_, c_ = pos[0] + _FARM_MOVES[action][0], pos[1] + _FARM_MOVES[action][1]
    nxt = (min(max(r_, 0), FARM_SIZE - 1), min(max(c_, 0), FARM_SIZE - 1))
    reward, new_timer, collected = 0.0, max(0, timer - 1), False
    if nxt == FARM_TILE and timer == 0:
        reward += bonus
        new_timer, collected = FARM_RESPAWN, True
    done = nxt == FARM_GOAL
    if done:
        reward += FARM_GOAL_REWARD
    return nxt, new_timer, reward, done, collected


def farm_learn(bonus: float, seed: int, episodes: int = 2000, alpha: float = 0.2, eps: float = 0.1, gamma: float = 0.95) -> dict:
    """Tabular Q-learning on the farming grid (state = position and tile timer), then the greedy
    policy's last 200 episodes measured: {"finish_rate", "steps", "bonuses"} (means)."""
    rng = np.random.default_rng(seed)
    Q: dict = {}
    finished = []
    for ep in range(episodes):
        pos, timer, done, taken, t = FARM_START, 0, False, 0, 0
        greedy = ep >= episodes - 200
        for t in range(1, FARM_CAP + 1):
            q = Q.setdefault((pos, timer), np.zeros(4))
            if not greedy and rng.random() < eps:
                a = int(rng.integers(4))
            else:
                a = int(rng.choice(np.flatnonzero(q == q.max())))
            pos2, timer2, r, done, got = farm_step(pos, timer, a, bonus)
            taken += got
            q2 = Q.setdefault((pos2, timer2), np.zeros(4))
            q[a] += alpha * (r + (0.0 if done else gamma * q2.max()) - q[a])
            pos, timer = pos2, timer2
            if done:
                break
        if greedy:
            finished.append((done, t, taken))
    f = np.array(finished, dtype=float)
    return {"finish_rate": float(f[:, 0].mean()), "steps": float(f[:, 1].mean()), "bonuses": float(f[:, 2].mean())}
