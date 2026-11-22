"""Lab p9-07 · Test the claim.

TASK 1. Page 07 (before this lab) and audit finding J1 said the plan's SubprocVecEnv + lambda
crashes on Windows. Three small scripts sit next to this file. Before running each, predict what
it does, and write your predictions in OUTCOMES below: "works", "PicklingError" or "RuntimeError".
Then run them from the prerequisites/ folder:

    python labs/phase9/p9_07_test_the_claim/claim_1_plain_lambda.py
    python labs/phase9/p9_07_test_the_claim/claim_2_sb3_lambda.py
    python labs/phase9/p9_07_test_the_claim/claim_3_no_guard.py

Each forces the "spawn" start method, Windows' only one, so the result is the same on any OS. The
check runs them too and compares what happened with what you wrote; update OUTCOMES once you have
seen them. Being wrong first is the point. If a script prints an error and then sits there, that is
part of its outcome: press Ctrl+C and record the error it printed.

TASK 2. `make_env` and `make_vec`: the toy race behind an ActionMasker, in a DummyVecEnv or a
SubprocVecEnv, written so that it works under spawn and with plain multiprocessing as well.

TASK 3. `steps_per_second`: how fast each kind steps this cheap environment.

Run `python -m labs check p9-07`. The check starts several worker processes; it takes about a
minute.
"""

from __future__ import annotations

import functools
import time

import numpy as np
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

from labs.labkit.racegym import TinyRaceEnv

# A dict with the three script names as keys, e.g. {"claim_1_plain_lambda": "works", ...}
OUTCOMES = None  # TODO: your answer


def mask_fn(env) -> np.ndarray:
    """The mask function, at module level so that any pickler can find it by name."""
    return env.action_masks()


def make_env(seed: int) -> ActionMasker:
    """One toy race, reset with `seed`, wrapped in an ActionMasker that uses mask_fn."""
    # TODO: build TinyRaceEnv(), reset it with seed, return ActionMasker(env, mask_fn)
    raise NotImplementedError("TODO p9-07: build TinyRaceEnv(), reset it with seed, return ActionMasker(env, mask_fn)")


def make_vec(n_envs: int, kind: str, seed: int = 0):
    """n_envs toy races in a "dummy" or "subproc" VecEnv. A SubprocVecEnv uses start_method="spawn".

    Each worker needs a factory it can call with no arguments. Use functools.partial of the
    module-level make_env, not a lambda or a nested function.
    """
    # TODO: factories = [functools.partial(make_env, seed + i) ...]; DummyVecEnv(factories) or SubprocVecEnv(factories, start_method="spawn")
    raise NotImplementedError("TODO p9-07: factories = [functools.partial(make_env, seed + i) ...]; DummyVecEnv(factories) or SubprocVecEnv(factories, start_method=\"spawn\")")


def steps_per_second(venv, n: int = 2000) -> float:
    """Reset, then time n calls of venv.step with STAY_OUT (0) in every copy. Environment steps per second."""
    venv.reset()
    actions = np.zeros(venv.num_envs, dtype=int)
    # TODO: time.perf_counter() around n venv.step(actions) calls; return n * venv.num_envs / elapsed
    raise NotImplementedError("TODO p9-07: time.perf_counter() around n venv.step(actions) calls; return n * venv.num_envs / elapsed")
