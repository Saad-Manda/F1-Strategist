"""Small deterministic gridworlds with an exact solver, for the reward-shaping labs.

Everything here is given, complete code. Labs import it; nothing in this file is a TODO.

A grid is drawn as a list of strings:

    S   start            .   floor           #   wall
    *   bonus tile       A-Z exits: stepping onto one ends the episode (except S)

Every step costs `step_reward` (default -1). Stepping onto an exit also pays that exit's value.
Stepping onto a bonus tile pays `tile_bonus` (default 0) every time. Moving into a wall or off
the grid leaves you where you were (the step is still paid).

`solve(grid, reward_fn, gamma)` runs value iteration with any reward function you give it and
returns the optimal values and, for every non-terminal cell, the SET of optimal actions (ties
kept, so two solutions can be compared exactly).
"""

from __future__ import annotations

MOVES = {0: (-1, 0), 1: (1, 0), 2: (0, -1), 3: (0, 1)}  # up, down, left, right
MOVE_NAMES = ("up", "down", "left", "right")


class Grid:
    def __init__(self, rows: list[str], exits: dict[str, float], step_reward: float = -1.0, tile_bonus: float = 0.0):
        self.rows = [list(r) for r in rows]
        self.height, self.width = len(rows), len(rows[0])
        self.exits = dict(exits)
        self.step_reward = step_reward
        self.tile_bonus = tile_bonus
        self.start = next((r, c) for r in range(self.height) for c in range(self.width) if self.rows[r][c] == "S")
        self.cells = [(r, c) for r in range(self.height) for c in range(self.width) if self.rows[r][c] != "#"]
        self.states = [s for s in self.cells if not self.is_exit(s)]

    def char(self, s) -> str:
        return self.rows[s[0]][s[1]]

    def is_exit(self, s) -> bool:
        return self.char(s) in self.exits

    def move(self, s, a):
        """(next cell, whether the episode ends there)."""
        dr, dc = MOVES[a]
        r, c = s[0] + dr, s[1] + dc
        if not (0 <= r < self.height and 0 <= c < self.width) or self.rows[r][c] == "#":
            r, c = s
        return (r, c), self.is_exit((r, c))

    def reward(self, s, a, s2, done) -> float:
        """The grid's own reward for the step s --a--> s2."""
        r = self.step_reward
        if self.char(s2) == "*":
            r += self.tile_bonus
        if done:
            r += self.exits[self.char(s2)]
        return r

    def distance(self, target_chars: str):
        """Steps from every cell to the nearest cell whose char is in `target_chars` (walls block)."""
        frontier = [s for s in self.cells if self.char(s) in target_chars]
        dist = {s: 0 for s in frontier}
        while frontier:
            nxt = []
            for s in frontier:
                for a in MOVES:
                    dr, dc = MOVES[a]
                    t = (s[0] + dr, s[1] + dc)
                    if t in dist or not (0 <= t[0] < self.height and 0 <= t[1] < self.width) or self.rows[t[0]][t[1]] == "#":
                        continue
                    dist[t] = dist[s] + 1
                    nxt.append(t)
            frontier = nxt
        return dist


def solve(grid: Grid, reward_fn=None, gamma: float = 0.95, tol: float = 1e-12, max_sweeps: int = 100_000):
    """Exact optimal values and optimal-action sets.

    `reward_fn(s, a, s2, done)` defaults to `grid.reward`. Returns (V, best) where V maps every
    non-terminal cell to its value and best maps it to a frozenset of optimal actions.
    """
    reward_fn = reward_fn or grid.reward
    V = {s: 0.0 for s in grid.states}

    def q(s, a):
        s2, done = grid.move(s, a)
        return reward_fn(s, a, s2, done) + (0.0 if done else gamma * V[s2])

    for _ in range(max_sweeps):
        delta = 0.0
        for s in grid.states:
            v = max(q(s, a) for a in MOVES)
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < tol:
            break
    best = {}
    for s in grid.states:
        qs = {a: q(s, a) for a in MOVES}
        top = max(qs.values())
        best[s] = frozenset(a for a, v in qs.items() if v >= top - 1e-7)
    return V, best


def greedy_path(grid: Grid, best: dict, max_steps: int = 60) -> list:
    """Follow the lowest-numbered optimal action from the start. Ends at an exit or after max_steps."""
    s, path = grid.start, [grid.start]
    for _ in range(max_steps):
        s, done = grid.move(s, min(best[s]))
        path.append(s)
        if done:
            break
    return path


# ---------------------------------------------------------------------------- the lab's grids

OPEN = Grid(
    [
        "S....#...",
        ".##..#.#.",
        "....*..#.",
        ".#.###...",
        ".#.....#G",
    ],
    exits={"G": 10.0},
)
"""A small maze with one exit worth 10 and a bonus tile (worth nothing unless you set tile_bonus)."""

TWO_EXITS = Grid(
    [
        "N.......",
        "........",
        "...S....",
        "........",
        ".......F",
    ],
    exits={"N": 8.0, "F": 10.0},
)
"""A near exit worth 8 and a far exit worth 10. Which one is best depends on the step cost and gamma."""


def farming(tile_bonus: float) -> Grid:
    """p6-02's farming grid, without the respawn timer: the tile pays every time it is entered."""
    return Grid(
        [
            "S....",
            ".....",
            "..*..",
            ".....",
            "....G",
        ],
        exits={"G": 10.0},
        step_reward=0.0,
        tile_bonus=tile_bonus,
    )
