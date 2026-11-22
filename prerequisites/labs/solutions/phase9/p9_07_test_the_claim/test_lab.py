"""Checks for lab p9-07. Given code: nothing to edit here."""

import os
import pathlib
import subprocess
import sys
import threading
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "labs" / "labkit").exists())
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import vec  # noqa: E402

SCRIPTS = ("claim_1_plain_lambda", "claim_2_sb3_lambda", "claim_3_no_guard")
ALLOWED = {"works", "PicklingError", "RuntimeError"}


MARKERS = ("PicklingError", "Can't pickle", "bootstrapping phase")
CEILING = 180  # seconds; a loaded machine can take a minute to start two torch workers


def _kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def observed(script: str) -> str:
    """Run one claim script in a fresh Python and classify what happened.

    The output is read as it arrives. The run is stopped as soon as an error that settles the
    question appears, because the main script can then wait forever on workers that died.
    """
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.Popen([sys.executable, str(HERE / f"{script}.py")], cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=env)
    lines: list[str] = []
    reader = threading.Thread(target=lambda: lines.extend(iter(proc.stdout.readline, "")), daemon=True)
    reader.start()
    deadline = time.monotonic() + CEILING
    code = None
    while time.monotonic() < deadline:
        code = proc.poll()
        if code is not None or any(m in "".join(lines) for m in MARKERS):
            break
        time.sleep(0.2)
    if code is None:
        _kill_tree(proc)
    else:
        reader.join(5)
    out = "".join(lines)
    if "PicklingError" in out or "Can't pickle" in out:
        return "PicklingError"
    if "bootstrapping phase" in out:
        return "RuntimeError"
    if code is None:
        return "hung, with no error message"
    return "works" if code == 0 and "OUTCOME: works" in out else f"something else (exit {code})"


@pytest.fixture(scope="module")
def what_happened():
    return {s: observed(s) for s in SCRIPTS}


@pytest.mark.parametrize("script", SCRIPTS)
def test_task1_outcome(what_happened, script):
    if vec.OUTCOMES is None:
        raise NotImplementedError("TODO p9-07: set OUTCOMES in vec.py (predict first, then run the three scripts)")
    guess = vec.OUTCOMES.get(script)
    assert guess in ALLOWED, f"OUTCOMES[{script!r}] should be one of {sorted(ALLOWED)}."
    assert guess == what_happened[script], f"You wrote {guess!r} for {script}; when the check ran it, the result was {what_happened[script]!r}. Run it yourself and read the last lines."


@pytest.fixture(scope="module")
def subproc():
    venv = vec.make_vec(2, "subproc")
    yield venv
    venv.close()


def test_task2_dummy_steps_and_masks():
    venv = vec.make_vec(3, "dummy")
    masks = venv.env_method("action_masks")
    assert len(masks) == 3 and all(m.tolist() == [True, False, True] for m in masks), "Every copy starts on compound A: PIT_A is masked."
    venv.close()


def test_task2_subproc_works_under_spawn(subproc):
    masks = subproc.env_method("action_masks")
    assert len(masks) == 2 and all(m.tolist() == [True, False, True] for m in masks), "The masks must come back from both worker processes."


def test_task2_maskable_ppo_trains_on_it(subproc):
    from sb3_contrib import MaskablePPO

    MaskablePPO("MlpPolicy", subproc, n_steps=64, batch_size=64, n_epochs=1, verbose=0, seed=0).learn(128)


def test_task2_plain_multiprocessing_can_ship_it():
    """A named, module-level mask function survives plain pickle too, not only cloudpickle."""
    import pickle

    env = vec.make_env(0)
    clone = pickle.loads(pickle.dumps(env))
    assert clone.action_masks().tolist() == [True, False, True], "Your ActionMasker should pickle with the standard pickle module: no lambdas inside."


def test_task3_dummy_is_faster(subproc):
    dummy = vec.make_vec(2, "dummy")
    fast, slow = vec.steps_per_second(dummy, 2000), vec.steps_per_second(subproc, 1000)
    dummy.close()
    print(f"DummyVecEnv {fast:,.0f} steps/s, SubprocVecEnv {slow:,.0f} steps/s")
    assert slow > 0 and fast > 3 * slow, (
        f"On an environment this cheap, DummyVecEnv should be several times faster (measured about 14×); got {fast:,.0f} vs {slow:,.0f} steps/s."
    )
