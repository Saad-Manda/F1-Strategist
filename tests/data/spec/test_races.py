"""Each test names the code change that would make it fail."""

from collections import Counter
from pathlib import Path

import pytest

from src.common.config import load_config
from src.common.errors import ConfigError
from src.data.spec.races import load_cross_checks, load_races

HEADER = "holdout_years: [2025]\nlast_allowed_year: 2025\nraces:\n"
RACE = "  - {{id: {id}, circuit: spa, year: {year}, source: {source}, session_key: 1, role: {role}}}\n"


@pytest.fixture
def races_file(tmp_path: Path):
    def write(*rows: dict) -> Path:
        base = {"id": "a", "year": 2024, "source": "openf1", "role": "fit"}
        file = tmp_path / "races.yaml"
        file.write_text(HEADER + "".join(RACE.format(**{**base, **row}) for row in rows))
        return file

    return write


def test_real_list_has_the_agreed_races():
    # Fails if a race is lost, added, or given another role (D24, D25).
    roles = Counter(race.role for race in load_races())
    assert roles == {"fit": 88, "holdout": 23, "conditions_only": 1, "frequency_only": 1}


def test_real_list_keeps_2025_out_of_fitting():
    # Fails if any 2025 race can be used for fitting (D25).
    assert {race.role for race in load_races() if race.year == 2025} == {"holdout"}
    assert max(race.year for race in load_races()) == 2025


def test_every_calibrated_circuit_has_races_to_fit():
    # Fails if a circuit in circuits.yaml has no race of its own.
    fitted = {race.circuit for race in load_races() if race.role == "fit"}
    assert {c["name"] for c in load_config("configs/circuits.yaml")["circuits"]} <= fitted


def test_cross_checks_use_the_other_source():
    # Fails if a race would be compared with itself.
    sources = {race.id: race.source for race in load_races()}
    cross_checks = load_cross_checks()
    assert len(cross_checks) == 3
    for race in cross_checks:
        assert sources[race.id] != race.source


def test_repeated_id_is_rejected(races_file):
    # Fails if two races could overwrite each other's files.
    with pytest.raises(ConfigError, match="repeated"):
        load_races(races_file({"id": "a"}, {"id": "a"}))


@pytest.mark.parametrize(
    "row, message",
    [
        ({"year": 2025, "role": "fit"}, "holdout rule"),
        ({"year": 2024, "role": "holdout"}, "holdout rule"),
        ({"year": 2026, "role": "fit"}, "transfer check"),
        ({"role": "training"}, "unknown role"),
        ({"source": "kaggle"}, "unknown source"),
    ],
)
def test_bad_rows_are_rejected(races_file, row, message):
    # Fails if the matching check in _parse is removed.
    with pytest.raises(ConfigError, match=message):
        load_races(races_file(row))
