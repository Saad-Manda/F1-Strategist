"""The Phase 0.5 gate: the calibration files the environment loads pass every check (K1-K9).

No Phase 1 work starts until this passes.
"""

from pathlib import Path

import pytest

from src.calibration.checks.validate import validate
from src.common.config import load_config
from src.common.schema import read_calibration

CIRCUITS = load_config("configs/circuits.yaml")["circuits"]


@pytest.mark.parametrize("circuit", CIRCUITS, ids=lambda c: c["name"])
def test_calibration_file(circuit):
    # Fails if a circuit's calibration.json is missing, malformed, implausible, or not this circuit's.
    params = read_calibration(Path("data/processed") / circuit["name"] / "calibration.json")
    assert params["circuit"] == circuit["name"]
    assert params["total_laps"] == circuit["total_laps"]
    validate(params, load_config("configs/defaults.yaml")["calibration"])
