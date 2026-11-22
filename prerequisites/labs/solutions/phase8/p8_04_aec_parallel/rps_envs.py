"""Lab p8-04 · Two ways to formalise "everyone acts".

Rock-paper-scissors twice. ParallelRPS is page 04's Parallel API: both players submit an action,
the environment resolves both, and everything comes back as dicts keyed by agent. SequentialRPS is
a turn-based game in which the second player sees the first one's move before choosing. Then you
measure what that information is worth, and what happens when PettingZoo's own parallel_to_aec
turns the Parallel game into an AEC one.

Actions: 0 = rock, 1 = paper, 2 = scissors. a beats b when (a - b) % 3 == 1.
Observations: the other player's most recent move (0, 1 or 2), or 3 if there is none to see.

Run the checks:  python -m labs check p8-04
"""

from __future__ import annotations

import numpy as np

try:  # use PettingZoo's base class when it is installed, so its API test can run on your env
    from pettingzoo import ParallelEnv as _Base
except ImportError:  # the lab works without it
    _Base = object

NONE_SEEN = 3
ROUNDS = 5  # rounds per episode


def winner_reward(a: int, b: int) -> int:
    """+1 if a beats b, -1 if b beats a, 0 on a tie."""
    return 0 if a == b else (1 if (a - b) % 3 == 1 else -1)


def beats(move: int) -> int:
    """The action that beats `move`."""
    return (move + 1) % 3


class ParallelRPS(_Base):
    metadata = {"name": "parallel_rps_v0", "render_modes": []}

    def __init__(self):
        self.possible_agents = ["player_a", "player_b"]
        self.agents: list[str] = []
        from gymnasium import spaces

        self._obs_space = spaces.Discrete(4)
        self._act_space = spaces.Discrete(3)

    def observation_space(self, agent):
        return self._obs_space

    def action_space(self, agent):
        return self._act_space

    def reset(self, seed=None, options=None):
        """Start an episode. Returns (observations, infos), dicts keyed by every agent. Nobody has
        seen a move yet."""
        # >>> SOLUTION: agents = all possible agents; round counter 0; both observe NONE_SEEN
        self.agents = self.possible_agents[:]
        self.round = 0
        return {a: NONE_SEEN for a in self.agents}, {a: {} for a in self.agents}
        # <<< SOLUTION

    def step(self, actions: dict):
        """Resolve BOTH actions together. Returns five dicts keyed by agent: observations (each sees
        the OTHER's move from this round), rewards (zero-sum), terminations (True after ROUNDS
        rounds), truncations (always False), infos. When the episode ends, self.agents becomes []."""
        # >>> SOLUTION: score both moves, swap them into observations, end after ROUNDS
        x, y = int(actions["player_a"]), int(actions["player_b"])
        r = winner_reward(x, y)
        self.round += 1
        done = self.round >= ROUNDS
        agents = self.agents
        obs = {"player_a": y, "player_b": x}
        out = (obs, {"player_a": r, "player_b": -r}, {a: done for a in agents}, {a: False for a in agents}, {a: {} for a in agents})
        if done:
            self.agents = []
        return out
        # <<< SOLUTION


class SequentialRPS:
    """Turn-based: player_a moves, then player_b moves having SEEN player_a's move, then the round is
    scored. AEC-style: `agent_selection` names whose turn it is."""

    agents_order = ("player_a", "player_b")

    def reset(self, seed=None):
        self.agent_selection = "player_a"
        self.pending = None  # player_a's move this round, once made
        self.last = {"player_a": NONE_SEEN, "player_b": NONE_SEEN}  # each player's last completed move
        self.rewards = {"player_a": 0, "player_b": 0}
        self.round = 0
        self.done = False

    def observe(self, agent: str) -> int:
        """player_b sees player_a's move THIS round once it has been made; otherwise each player
        sees the other's last completed move."""
        # >>> SOLUTION: the pending move for player_b when there is one; else the other's last move
        if agent == "player_b" and self.pending is not None:
            return self.pending
        other = "player_b" if agent == "player_a" else "player_a"
        return self.last[other]
        # <<< SOLUTION

    def step(self, action: int) -> None:
        """Act for agent_selection. After player_b's move, score the round into self.rewards."""
        # >>> SOLUTION: record a's move and pass the turn; on b's move score, store last moves, reset pending
        if self.agent_selection == "player_a":
            self.pending = int(action)
            self.agent_selection = "player_b"
            return
        r = winner_reward(self.pending, int(action))
        self.rewards = {"player_a": r, "player_b": -r}
        self.last = {"player_a": self.pending, "player_b": int(action)}
        self.pending = None
        self.agent_selection = "player_a"
        self.round += 1
        self.done = self.round >= ROUNDS
        # <<< SOLUTION


def second_mover_edge(kind: str, rounds: int = 2000, seed: int = 0) -> float:
    """player_a plays uniformly at random; player_b plays the move that beats whatever it OBSERVES
    (randomly if it observes NONE_SEEN). Returns player_b's mean reward per round.

    kind "sequential": SequentialRPS, player_b observing when its turn comes.
    kind "parallel":   ParallelRPS, player_b's observation from the previous step.
    """
    rng = np.random.default_rng(seed)

    def reply(o):
        return int(rng.integers(3)) if o == NONE_SEEN else beats(o)

    total, n = 0.0, 0
    # >>> SOLUTION: run episodes until `rounds` rounds have been played, summing player_b's reward
    if kind == "sequential":
        env = SequentialRPS()
        while n < rounds:
            env.reset()
            while not env.done and n < rounds:
                env.step(int(rng.integers(3)))
                env.step(reply(env.observe("player_b")))
                total += env.rewards["player_b"]
                n += 1
    elif kind == "parallel":
        env = ParallelRPS()
        while n < rounds:
            obs, _ = env.reset()
            while env.agents and n < rounds:
                obs, rew, *_ = env.step({"player_a": int(rng.integers(3)), "player_b": reply(obs["player_b"])})
                total += rew["player_b"]
                n += 1
    else:
        raise ValueError(kind)
    # <<< SOLUTION
    return total / n


def aec_wrapped_edge(rounds: int = 2000, seed: int = 0) -> float:
    """Given: the same measurement on pettingzoo.utils.parallel_to_aec(ParallelRPS()).

    In each AEC cycle player_a steps first, then player_b observes (env.last()) and steps. The
    wrapper resolves the round only once both have stepped, then sets env.rewards.
    """
    from pettingzoo.utils import parallel_to_aec

    rng = np.random.default_rng(seed)
    total, n = 0.0, 0
    while n < rounds:
        env = parallel_to_aec(ParallelRPS())
        env.reset(seed=int(rng.integers(1 << 30)))
        for agent in env.agent_iter():
            obs, _, term, trunc, _ = env.last()
            if term or trunc:
                env.step(None)
            elif agent == "player_a":
                env.step(int(rng.integers(3)))
            else:
                o = int(obs)
                env.step(int(rng.integers(3)) if o == NONE_SEEN else beats(o))
                total += env.rewards["player_b"]
                n += 1
                if n >= rounds:
                    break
    return total / n
