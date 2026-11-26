"""Checks on the real frozen data. Skipped on a clone without data/interim."""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.common.config import load_config
from src.data.ingest import TABLES, content_hash, read_race
from src.data.spec.races import load_cross_checks, load_races

INTERIM = Path("data/interim")
RACES = {race.id: race for race in load_races()}

pytestmark = pytest.mark.skipif(not INTERIM.exists(), reason="data/interim is not built")


def laps_of(race_id: str) -> pd.DataFrame:
    return pd.read_parquet(INTERIM / race_id / "laps.parquet")


def test_every_race_is_frozen():
    # Fails if a race in races.yaml was not ingested.
    missing = [r for r in RACES if not (INTERIM / r / "manifest.json").exists()]
    assert missing == []


def test_files_match_their_manifest():
    # Fails if a frozen table was edited or corrupted after ingest.
    for race_id in RACES:
        manifest = json.loads((INTERIM / race_id / "manifest.json").read_text())
        for table in TABLES:
            frame = pd.read_parquet(INTERIM / race_id / f"{table}.parquet")
            assert content_hash(frame) == manifest["hash"][table], (race_id, table)


def test_laps_run_from_one_without_gaps():
    # Fails if a reader loses or renumbers laps.
    for race_id in RACES:
        for driver, group in laps_of(race_id).groupby("driver"):
            assert group["lap"].tolist() == list(range(1, len(group) + 1)), (race_id, driver)


def test_red_flag_on_lap_one_is_seen():
    # Fails if lap 1 starts at the restart (2024 Monaco).
    laps = laps_of("2024_monaco")
    assert laps.loc[laps["lap"] == 1, "track_status"].str.contains("5").mean() > 0.5


def test_spa_2025_starts_on_intermediates():
    # Fails if the opening_compound repair is not applied to the real race.
    laps = laps_of("2025_spa")
    early = laps[laps["lap"].between(2, 8)]
    assert (early["compound"] == "INTERMEDIATE").all()
    assert (early["label"] == "repaired").all()


@pytest.mark.slow
@pytest.mark.parametrize("race", load_cross_checks(), ids=lambda race: race.id)
def test_both_sources_agree(race):
    # Fails if a reader drifts: tyres, stops, status and timing must match on the same race.
    config = load_config("configs/ingest.yaml")
    first = laps_of(race.id)
    second = read_race(race, config).laps
    both = first.merge(second, on=["driver_number", "lap"], suffixes=("_a", "_b"))
    assert len(both) / max(len(first), len(second)) > 0.99
    for column in ("compound", "tyre_age", "is_in_lap", "is_out_lap", "track_status"):
        agree = (both[f"{column}_a"] == both[f"{column}_b"]).fillna(False)
        assert agree.mean() > 0.99, column
    timed = both[both["lap"] > 1]
    gap = (timed["lap_time_s_a"] - timed["lap_time_s_b"]).abs().dropna()
    assert (gap <= 0.01).mean() > 0.99
    offset = both["lap_end_s_a"] - both["lap_end_s_b"]
    assert (offset - offset.median()).abs().quantile(0.95) < 0.25
