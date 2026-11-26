"""Each test names the code change that would make it fail."""

import json

import pandas as pd
import pytest

from src.common.config import load_config
from src.common.errors import CalibrationError
from src.data import ingest
from src.data.spec.frames import LAP_DTYPES, STATUS_DTYPES, WEATHER_DTYPES
from src.data.spec.races import Race
from tests.data.helpers import make_frames

RACE = Race("2024_toy", "toy", 2024, "openf1", "fit", session_key=1)
CONFIG = """
version: {version}
paths: {{raw: raw, interim: {interim}}}
sector_sum_tolerance_s: 0.01
checks:
  min_cars: 15
  min_known_compound_share: 0.75
  max_missing_lap_time_share: 0.2
  max_suspect_label_share: 0.25
"""


@pytest.fixture
def make_config(tmp_path):
    def make(version=1):
        file = tmp_path / f"ingest_{version}.yaml"
        text = CONFIG.format(version=version, interim=(tmp_path / "interim").as_posix())
        file.write_text(text, encoding="utf-8")
        return load_config(file)

    return make


@pytest.fixture
def source(monkeypatch):
    """Replaces the OpenF1 reader; `frames` can be changed by a test."""

    class Source:
        frames = make_frames()
        reads = 0

        def read(self, race, raw_dir, tolerance):
            self.reads += 1
            return self.frames

    fake = Source()
    monkeypatch.setitem(ingest.READERS, "openf1", fake.read)
    return fake


def manifest(tmp_path):
    return json.loads((tmp_path / "interim/2024_toy/manifest.json").read_text())


def test_files_keep_every_type(make_config, source, tmp_path):
    # Fails if parquet turns status codes into numbers or whole numbers into floats.
    ingest.ingest_race(RACE, make_config())
    for table, dtypes in (("laps", LAP_DTYPES), ("weather", WEATHER_DTYPES), ("track_status", STATUS_DTYPES)):
        stored = pd.read_parquet(tmp_path / f"interim/2024_toy/{table}.parquet")
        pd.testing.assert_frame_equal(stored, getattr(source.frames, table))
        assert {c: str(t) for c, t in stored.dtypes.items()} == dtypes


def test_second_run_does_nothing(make_config, source, tmp_path):
    # Fails if an up-to-date race is read again or its files change.
    assert ingest.ingest_race(RACE, make_config()) is True
    before = manifest(tmp_path)
    assert ingest.ingest_race(RACE, make_config()) is False
    assert source.reads == 1
    assert manifest(tmp_path) == before


def test_force_rebuilds_with_the_same_hashes(make_config, source, tmp_path):
    # Fails if --force is ignored or the hash depends on the run.
    ingest.ingest_race(RACE, make_config())
    before = manifest(tmp_path)
    assert ingest.ingest_race(RACE, make_config(), force=True) is True
    assert manifest(tmp_path)["hash"] == before["hash"]


def test_hash_follows_the_content(make_config, source, tmp_path):
    # Fails if the hash ignores a changed value.
    ingest.ingest_race(RACE, make_config())
    before = manifest(tmp_path)["hash"]["laps"]
    source.frames = make_frames(lap_time_s=91.0)
    ingest.ingest_race(RACE, make_config(), force=True)
    assert manifest(tmp_path)["hash"]["laps"] != before


def test_new_version_or_changed_race_rebuilds(make_config, source):
    # Fails if the manifest is not compared with the current settings.
    ingest.ingest_race(RACE, make_config())
    assert ingest.ingest_race(RACE, make_config(version=2)) is True
    changed = Race("2024_toy", "toy", 2024, "openf1", "fit", session_key=1, repairs=("opening_compound",))
    assert ingest.ingest_race(changed, make_config(version=2)) is True


def test_unfinished_race_is_rebuilt(make_config, source, tmp_path):
    # Fails if a race without its manifest or a table counts as done.
    ingest.ingest_race(RACE, make_config())
    (tmp_path / "interim/2024_toy/weather.parquet").unlink()
    assert ingest.ingest_race(RACE, make_config()) is True


@pytest.mark.parametrize(
    "frames, message",
    [
        (make_frames(cars=14), "cars 14"),
        (make_frames(compound="UNKNOWN"), "known compounds 0.0"),
        (make_frames(lap_time_s=float("nan")), "missing lap times 1.0"),
        (make_frames(label="suspect"), "suspect labels 1.0"),
    ],
)
def test_incomplete_race_is_refused_and_not_written(make_config, source, tmp_path, frames, message):
    # Fails if the matching check is removed, or files are written before it.
    source.frames = frames
    with pytest.raises(CalibrationError, match=f"2024_toy: {message}"):
        ingest.ingest_race(RACE, make_config())
    assert not (tmp_path / "interim").exists()


def test_frequency_only_race_may_be_incomplete(make_config, source):
    # Fails if 2021 Spa is refused.
    source.frames = make_frames(compound="UNKNOWN")
    race = Race("2021_toy", "toy", 2021, "openf1", "frequency_only", session_key=1)
    assert ingest.ingest_race(race, make_config()) is True


def test_run_reports_every_failure_and_exits_non_zero(make_config, monkeypatch, capsys):
    # Fails if the first bad race stops the run, or a failure exits 0.
    races = [Race(f"2024_{n}", n, 2024, "openf1", "fit", session_key=1) for n in ("a", "b", "c")]

    def read(race, raw_dir, tolerance):
        if race.id in ("2024_a", "2024_c"):
            raise CalibrationError(f"{race.id}: broken")
        return make_frames()

    monkeypatch.setitem(ingest.READERS, "openf1", read)
    monkeypatch.setattr(ingest, "load_races", lambda: races)
    monkeypatch.setattr(ingest, "load_config", lambda file: make_config())
    assert ingest.main([]) == 1
    output = capsys.readouterr().out
    assert "2024_a: broken" in output
    assert "2024_c: broken" in output
    assert "1 built" in output


def test_clean_run_exits_zero(make_config, source, monkeypatch):
    # Fails if a good run reports failure.
    monkeypatch.setattr(ingest, "load_races", lambda: [RACE])
    monkeypatch.setattr(ingest, "load_config", lambda file: make_config())
    assert ingest.main([]) == 0
    assert ingest.main(["--race", "2024_nowhere"]) == 1
