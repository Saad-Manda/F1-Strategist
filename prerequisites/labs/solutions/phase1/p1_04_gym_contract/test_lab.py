"""Checks for lab p1-04. Given code: nothing to edit here."""

import hashlib
import os
import sys
import warnings

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import diagnosis  # noqa: E402
from corridor_env import LEFT, MAX_STEPS, N_CELLS, RIGHT, CorridorEnv  # noqa: E402


@pytest.fixture
def env():
    return CorridorEnv()


def test_observation_matches_declared_space(env):
    obs, _ = env.reset(seed=0)
    assert isinstance(obs, np.ndarray), "The observation should be a NumPy array."
    assert obs.shape == (1,), f"Declared shape is (1,), the observation has shape {obs.shape}."
    assert obs.dtype == np.float32, f"Declared dtype is float32, the observation is {obs.dtype}."
    assert env.observation_space.contains(obs), "The first observation is not inside the declared observation space."
    assert obs[0] == 0.0, "The agent should start in cell 0."


def test_reset_returns_obs_and_info(env):
    result = env.reset(seed=0)
    assert isinstance(result, tuple) and len(result) == 2, "reset() returns exactly two things: (observation, info)."
    assert isinstance(result[1], dict), "The second value returned by reset() is the info dictionary."


def test_reset_starts_a_fresh_episode(env):
    env.reset(seed=0)
    for _ in range(3):
        env.step(RIGHT)
    obs, _ = env.reset(seed=0)
    assert obs[0] == 0.0, "reset() should put the agent back in cell 0, wherever the previous episode left it."
    for _ in range(MAX_STEPS - 1):
        _, _, _, truncated, _ = env.step(LEFT)
        assert not truncated, "The step counter should restart at reset(): a new episode was truncated early."


def test_step_returns_five_values(env):
    env.reset(seed=0)
    result = env.step(RIGHT)
    assert len(result) == 5, "step() returns (observation, reward, terminated, truncated, info)."
    obs, reward, terminated, truncated, info = result
    assert env.observation_space.contains(obs)
    assert reward == -1.0, "Every step costs -1."
    assert isinstance(terminated, (bool, np.bool_)) and isinstance(truncated, (bool, np.bool_))
    assert isinstance(info, dict)
    assert obs[0] == pytest.approx(1 / (N_CELLS - 1)), "One step RIGHT from cell 0 should land in cell 1."


def test_reaching_the_goal_terminates(env):
    env.reset(seed=0)
    for i in range(N_CELLS - 1):
        obs, _, terminated, truncated, _ = env.step(RIGHT)
        if i < N_CELLS - 2:
            assert not terminated and not truncated, "The episode ended before the goal was reached."
    assert terminated, "Arriving in the last cell finishes the task: terminated should be True."
    assert not truncated, "Reaching the goal is not a time-out: truncated should stay False."
    assert obs[0] == 1.0


def test_step_limit_truncates_and_does_not_terminate(env):
    env.reset(seed=0)
    for i in range(MAX_STEPS):
        _, _, terminated, truncated, _ = env.step(LEFT)
        assert not terminated, "The agent never reached the goal, so the task is not finished: terminated must stay False."
        if i < MAX_STEPS - 1:
            assert not truncated, f"Truncated after only {i + 1} steps; the limit is {MAX_STEPS}."
    assert truncated, f"After {MAX_STEPS} steps without reaching the goal the episode should be truncated."


def test_mask_forbids_walking_into_the_wall(env):
    env.reset(seed=0)
    mask = np.asarray(env.action_masks())
    assert mask.dtype == bool and mask.shape == (2,), "action_masks() returns a boolean array, one entry per action."
    assert not mask[LEFT] and mask[RIGHT], "In cell 0, LEFT is illegal and RIGHT is legal."
    obs, reward, _, _, _ = env.step(LEFT)
    assert obs[0] == 0.0 and reward == -1.0, "LEFT in cell 0, taken anyway, leaves the agent in place and still costs -1."
    env.step(RIGHT)
    mask = np.asarray(env.action_masks())
    assert mask[LEFT] and mask[RIGHT], "Away from the wall both actions are legal."


def test_episode_return_is_minus_step_count(env):
    env.reset(seed=0)
    total, steps, done = 0.0, 0, False
    actions = [RIGHT, LEFT, RIGHT, RIGHT] * 10
    while not done:
        _, reward, terminated, truncated, _ = env.step(actions[steps])
        total += reward
        steps += 1
        done = terminated or truncated
    assert total == -steps, "With -1 per step, the return of an episode is minus its length."


def test_check_env_passes(env):
    from stable_baselines3.common.env_checker import check_env

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        check_env(env)


# ---- task 2: the diagnoses are compared by fingerprint so the answers are not sitting here in plain text

FINGERPRINTS = {
    "DIAGNOSIS_ENV_ONE": "86cf84",
    "DIAGNOSIS_ENV_TWO": "3fbc9d",
    "DIAGNOSIS_ENV_THREE": "41ab5b",
}
ALLOWED = {"dtype", "bounds", "limit"}


@pytest.mark.parametrize("name", sorted(FINGERPRINTS))
def test_diagnosis(name):
    answer = getattr(diagnosis, name)
    if answer is None:
        raise NotImplementedError(f"TODO p1-04: set {name} in diagnosis.py")
    assert answer in ALLOWED, f"{name} should be one of {sorted(ALLOWED)}."
    digest = hashlib.sha256(f"{name}:{answer}".encode()).hexdigest()[:6]
    assert digest == FINGERPRINTS[name], f"{name} = {answer!r} is not what is wrong with that environment. Run check_env on it and step it by hand."
