"""The models on the real races. Skipped on a clone without data/interim."""

from pathlib import Path

import pytest

from src.calibration.fitting_races import load_fitting_races
from src.calibration.models.clean_laps import collect_clean_laps
from src.calibration.models.pit_stops import collect_stops, pit_fields
from src.calibration.models.track_status import status_fields
from src.calibration.models.tyre_fit import fit_pattern
from src.calibration.models.tyres import tyre_fields
from src.calibration.models.weather import weather_fields
from src.common.config import load_config
from src.data.spec.races import load_races

INTERIM = Path("data/interim")
CIRCUITS = ("silverstone", "monza", "spa")

pytestmark = pytest.mark.skipif(not INTERIM.exists(), reason="data/interim is not built")


@pytest.fixture(scope="module")
def config():
    return load_config("configs/defaults.yaml")["calibration"]


@pytest.fixture(scope="module")
def races(config):
    return load_fitting_races(load_races(), INTERIM, config)


def test_no_held_out_race(races):
    # Fails if 2025 or 2026 reaches a fit (D23, D25).
    assert {r.race.year for r in races} == {2021, 2022, 2023, 2024}


def test_tyres(races, config):
    # Fails if the real data no longer gives SOFT fastest and wearing most, HARD the reverse.
    laps, _ = collect_clean_laps(races, config)
    assert set(laps["race"].str[:4]) == {"2022", "2023", "2024"}
    assert "2024_silverstone" not in set(laps["race"])
    pattern = fit_pattern(laps)
    assert pattern.offset["SOFT"] < 0 < pattern.offset["HARD"]
    assert pattern.wear["SOFT"] > pattern.wear["MEDIUM"] > pattern.wear["HARD"] > 0
    scale = {}
    for circuit in CIRCUITS:
        result = tyre_fields(circuit, laps, pattern, config)
        scale[circuit] = result.diagnostics["wear_scale"]
        cliffs = [result.values["compounds"][c]["cliff_age"] for c in ("SOFT", "MEDIUM", "HARD")]
        assert cliffs == sorted(set(cliffs))
        assert result.values["noise_std"] > 0.2
    assert scale["silverstone"] < scale["monza"] < scale["spa"]


def test_pit_stops(races, config):
    # Fails if the pit losses leave what is known of these circuits, or a stop under a safety
    # car costs as much as a green one.
    stops = collect_stops(races, config)
    loss = {c: pit_fields(c, stops).values["pit_loss"] for c in CIRCUITS}
    assert loss["spa"] < loss["silverstone"] < loss["monza"]
    assert loss == pytest.approx({"silverstone": 20.5, "monza": 25.4, "spa": 18.2}, abs=0.5)
    values = pit_fields("monza", stops).values
    assert 0.5 < values["pit_loss_sc_multiplier"] < 0.9
    assert 0.5 < values["pit_loss_vsc_multiplier"] < 0.9


def test_track_status(races, config):
    # Fails if safety cars become implausibly rare, long or fast.
    fields = status_fields("monza", races, config)
    chain = fields.values["status_transition"]
    assert 0.005 < chain["GREEN"]["SC"] < 0.02
    assert 2 < 1 / (1 - chain["SC"]["SC"]) < 5
    assert 1 < 1 / (1 - chain["VSC"]["VSC"]) < 2
    ratio = fields.diagnostics["flag_lap_ratio"]
    assert 1.2 < ratio["VSC"] < 1.5 < ratio["SC"] < 2.0


def test_weather(races, config):
    # Fails if the chain stops matching how often it rained, or rain stops slowing the cars.
    fields = weather_fields(races, 90.0, config)
    chain = fields.values["weather_transition"]
    assert chain["DRY"]["WET"] == chain["WET"]["DRY"] == 0.0
    assert 0.05 < 1 - fields.values["weather_start"]["DRY"] < 0.2
    slowdown = fields.diagnostics["slowdown"]
    assert 0.05 < slowdown["DAMP"] < slowdown["WET"] < 0.4
