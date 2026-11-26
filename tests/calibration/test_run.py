from pathlib import Path

import pandas as pd
import pytest

from src.calibration import run
from src.calibration.checks.landscape import landscape
from src.common.schema import read_calibration
from tests.calibration.checks.helpers import check_config, valid_calibration

CIRCUITS = ("silverstone", "monza", "spa")


@pytest.fixture
def fake_models(monkeypatch):
    """Skip the real fits: every circuit gets the valid test calibration, unless listed in `broken`."""
    broken = set()

    def build(races, total_laps, config):
        built = {}
        for circuit in total_laps:
            params = valid_calibration() | {"circuit": circuit}
            params["diagnostics"]["landscape"] = landscape(params, check_config()["checks"]["landscape"])
            if circuit in broken:
                params["pit_loss"] = 40.0
            built[circuit] = params
        return built

    monkeypatch.setattr(run, "load_fitting_races", lambda *args: [])
    monkeypatch.setattr(run, "build_calibrations", build)
    monkeypatch.setattr(run, "circuit_traces", lambda c, *args: (pd.DataFrame({"race_id": [c], "lap": [1]}), []))
    return broken


def test_every_circuit_is_written(fake_models, tmp_path, capsys):
    # Fails if a passing run writes nothing, a file the loader refuses, or no provenance summary.
    assert run.main(["--out", str(tmp_path)]) == 0
    for circuit in CIRCUITS:
        assert read_calibration(tmp_path / circuit / "calibration.json")["circuit"] == circuit
        assert pd.read_parquet(tmp_path / circuit / "scenarios.parquet")["race_id"].tolist() == [circuit]
    assert "monza: 3 fitted" in capsys.readouterr().out


def test_one_failure_writes_nothing(fake_models, tmp_path, capsys):
    # Fails if an implausible circuit exits 0, or the passing circuits are written beside it.
    fake_models.add("spa")
    assert run.main(["--out", str(tmp_path)]) == 1
    assert list(tmp_path.iterdir()) == []
    out = capsys.readouterr().out
    assert "FAILED K3: pit_loss" in out and "Nothing written: spa failed" in out


def test_dry_run_writes_nothing(fake_models, tmp_path):
    # Fails if a dry run overwrites the files the environment loads.
    assert run.main(["--dry-run", "--out", str(tmp_path)]) == 0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.slow
@pytest.mark.skipif(not Path("data/interim").exists(), reason="data/interim is not built")
def test_real_traces():
    # Fails if a fit or holdout race is missing from the replays, or a race without laps is replayed.
    config = run.load_config("configs/defaults.yaml")["calibration"]
    traces, rejected = run.circuit_traces("spa", 44, run.load_races(), Path("data/interim"), config)
    assert rejected == []
    by_race = traces.groupby("race_id")["role"].first().to_dict()
    assert by_race == {"2022_spa": "fit", "2023_spa": "fit", "2024_spa": "fit", "2025_spa": "holdout"}
    assert traces.groupby("race_id").size().eq(44).all()
