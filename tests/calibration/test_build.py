"""The whole calibration on the real races. Skipped on a clone without data/interim."""

from pathlib import Path

import pytest

from src.calibration.build import build_calibrations
from src.calibration.checks.validate import validate
from src.calibration.fitting_races import load_fitting_races
from src.common.config import load_config
from src.data.spec.races import load_races

INTERIM = Path("data/interim")

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not INTERIM.exists(), reason="data/interim is not built"),
]


@pytest.fixture(scope="module")
def built():
    config = load_config("configs/defaults.yaml")["calibration"]
    laps = {c["name"]: c["total_laps"] for c in load_config("configs/circuits.yaml")["circuits"]}
    races = load_fitting_races(load_races(), INTERIM, config)
    return build_calibrations(races, laps, config), config


def test_every_circuit_passes(built):
    # Fails if the honest real-data calibration of any circuit fails a check.
    calibrations, config = built
    assert set(calibrations) == {"silverstone", "monza", "spa", "budapest", "barcelona"}
    for params in calibrations.values():
        validate(params, config)


def test_only_what_is_measured_per_circuit_is_fitted(built):
    # Fails if a pooled or assumed number is labelled as the circuit's own (D10).
    for params in built[0].values():
        fitted = {k for k, v in params["provenance"].items() if v == "fitted"}
        assert fitted == {"base_pace", "noise_std", "pit_loss"}
        assert params["provenance"]["compounds.SOFT.base_deg"] == "pooled"
        assert params["provenance"]["compounds.SOFT.cliff_age"] == "prior"


def test_rain_slowdown_scales_with_the_circuit(built):
    # Fails if the rain slowdown is not taken as a share of this circuit's own pace (D34).
    for params in built[0].values():
        share = params["diagnostics"]["weather"]["slowdown"]["DAMP"]
        prior = built[1]["weather_penalty_defaults"]["DAMP"]["INTERMEDIATE"]
        penalty = params["weather_compound_penalty"]["DAMP"]["INTERMEDIATE"]
        assert penalty == pytest.approx(prior + share * params["base_pace"])
