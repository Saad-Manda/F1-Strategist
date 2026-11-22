"""Checks for lab p9-05. Given code: nothing to edit here."""

import hashlib
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "labs" / "labkit").exists())))

import detectors as d  # noqa: E402
from labs.labkit import minipg  # noqa: E402

FINGERPRINT = "0b6f39"  # of the sorted LOUD set: no peeking at the answer in plain text


@pytest.fixture(scope="module")
def traces():
    return {bug: minipg.inspect_update(bug, seed=0) for bug in (None, "stale_old", "gae_next", "no_norm")}


def test_task1_loud_and_quiet():
    if d.LOUD is None or d.QUIET is None:
        raise NotImplementedError("TODO p9-05: set LOUD and QUIET in detectors.py after running run_variants.py")
    names = set(minipg.BUGS) - {None}
    assert set(d.LOUD) | set(d.QUIET) == names and not set(d.LOUD) & set(d.QUIET), f"Put each of {sorted(names)} in exactly one of the two sets."
    digest = hashlib.sha256(",".join(sorted(d.LOUD)).encode()).hexdigest()[:6]
    assert digest == FINGERPRINT, (
        "Not quite. A loud bug is one you would notice from the curve: does it get better at all? "
        "Rerun with --gaps: several curves that look like learning end far from the optimum."
    )


@pytest.mark.parametrize("detector, bug", [("ratio_moves", "stale_old"), ("gae_matches_returns", "gae_next"), ("advantages_standardised", "no_norm")])
def test_task2_detector_passes_the_correct_trainer(traces, detector, bug):
    assert getattr(d, detector)(traces[None]) is True, f"{detector} should return True for the correct trainer."


@pytest.mark.parametrize("detector, bug", [("ratio_moves", "stale_old"), ("gae_matches_returns", "gae_next"), ("advantages_standardised", "no_norm")])
def test_task2_detector_catches_its_bug(traces, detector, bug):
    assert getattr(d, detector)(traces[bug]) is False, (
        f"{detector} should return False for the trainer with the '{bug}' bug: that bug's whole point is that the curve hides it."
    )
