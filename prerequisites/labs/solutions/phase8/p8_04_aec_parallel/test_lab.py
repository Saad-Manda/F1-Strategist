"""Checks for lab p8-04. Given code: nothing to edit here."""

import importlib.util
import pathlib
import sys
import warnings

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import rps_envs as r  # noqa: E402

HAVE_PZ = importlib.util.find_spec("pettingzoo") is not None
needs_pz = pytest.mark.skipif(not HAVE_PZ, reason="PettingZoo is not installed; this check is optional")


def test_parallel_reset_and_step_are_dicts():
    env = r.ParallelRPS()
    obs, infos = env.reset(seed=0)
    assert set(obs) == set(env.possible_agents) and set(infos) == set(env.possible_agents), "reset returns (observations, infos), each keyed by every agent."
    assert all(o == r.NONE_SEEN for o in obs.values()), "At the start nobody has seen a move."
    out = env.step({"player_a": 0, "player_b": 1})
    assert len(out) == 5 and all(isinstance(d, dict) for d in out), "step returns five dicts."
    obs, rew, term, trunc, _ = out
    assert obs == {"player_a": 1, "player_b": 0}, "Each player observes the OTHER's move from this round."
    assert rew == {"player_a": -1, "player_b": 1}, "Paper (1) beats rock (0)."


def test_rewards_are_zero_sum():
    env = r.ParallelRPS()
    env.reset()
    for a in range(3):
        for b in range(3):
            env.reset()
            _, rew, *_ = env.step({"player_a": a, "player_b": b})
            assert rew["player_a"] + rew["player_b"] == 0


def test_agents_empty_at_the_end():
    env = r.ParallelRPS()
    env.reset()
    for k in range(r.ROUNDS):
        assert env.agents, f"The episode should still be running at round {k + 1}."
        _, _, term, _, _ = env.step({"player_a": 0, "player_b": 0})
    assert all(term.values()) and env.agents == [], f"After {r.ROUNDS} rounds every agent is terminated and env.agents is empty."


def test_sequential_second_mover_sees_the_move():
    env = r.SequentialRPS()
    env.reset()
    assert env.agent_selection == "player_a" and env.observe("player_b") == r.NONE_SEEN
    env.step(2)
    assert env.agent_selection == "player_b" and env.observe("player_b") == 2, "In the sequential game player_b sees player_a's move this round."
    env.step(0)
    assert env.rewards == {"player_a": -1, "player_b": 1}, "Rock (0) beats scissors (2)."
    assert env.observe("player_a") == 0 and env.agent_selection == "player_a"


def test_second_mover_edge_sequential_vs_parallel():
    seq, par = r.second_mover_edge("sequential"), r.second_mover_edge("parallel")
    print(f"second mover's mean reward: sequential {seq:+.3f}, parallel {par:+.3f}")
    assert seq == pytest.approx(1.0), "Seeing the move first, player_b wins every round."
    assert abs(par) < 0.08, f"In the Parallel game nothing is seen in time to use: the edge should be about 0, not {par:+.3f}."


@needs_pz
def test_aec_wrapper_reveals_nothing():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        edge = r.aec_wrapped_edge()
    print(f"second mover's mean reward under parallel_to_aec: {edge:+.3f}")
    assert abs(edge) < 0.08, "Going second in an AEC cycle is not the same as seeing the first move."


@needs_pz
def test_pettingzoo_parallel_api_test():
    from pettingzoo.test import parallel_api_test

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        parallel_api_test(r.ParallelRPS(), num_cycles=20)
