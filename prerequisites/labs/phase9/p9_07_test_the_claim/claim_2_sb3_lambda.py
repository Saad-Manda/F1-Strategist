"""Claim 2, given script: the real plan's make_vec_masked_envs, with its lambda, under spawn.

    python labs/phase9/p9_07_test_the_claim/claim_2_sb3_lambda.py

This is the plan's code shape exactly: a closure factory per worker, and inside it
ActionMasker(env, lambda e: e.action_masks()). Only the environment is the toy race.
"""

import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path(__file__).resolve().parents if (p / "labs" / "labkit").exists())))

from sb3_contrib import MaskablePPO  # noqa: E402
from sb3_contrib.common.wrappers import ActionMasker  # noqa: E402
from stable_baselines3.common.vec_env import SubprocVecEnv  # noqa: E402

from labs.labkit.racegym import TinyRaceEnv  # noqa: E402


def make_vec_masked_envs(n_envs=2, seed=0):
    def make_env(rank):
        def _init():
            env = TinyRaceEnv()
            env.reset(seed=seed + rank)
            return ActionMasker(env, lambda e: e.action_masks())
        return _init

    return SubprocVecEnv([make_env(i) for i in range(n_envs)], start_method="spawn")


if __name__ == "__main__":
    venv = make_vec_masked_envs()
    print("masks from the workers:", venv.env_method("action_masks"))
    MaskablePPO("MlpPolicy", venv, n_steps=64, batch_size=64, n_epochs=1, verbose=0).learn(128)
    venv.close()
    print("OUTCOME: works")
