"""Claim 3, given script: a correct, lambda-free factory, in a script with no __main__ guard.

    python labs/phase9/p9_07_test_the_claim/claim_3_no_guard.py

Everything below runs at import time, the way a quick training script often looks.
"""

import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path(__file__).resolve().parents if (p / "labs" / "labkit").exists())))

from stable_baselines3.common.vec_env import SubprocVecEnv  # noqa: E402

from labs.labkit.racegym import TinyRaceEnv  # noqa: E402

venv = SubprocVecEnv([TinyRaceEnv, TinyRaceEnv], start_method="spawn")
print("masks from the workers:", venv.env_method("action_masks"))
venv.close()
print("OUTCOME: works")
