"""Freeze every race to parquet, so later stages need neither the raw files nor the network.

Run from the repo root:  python -m src.data.ingest [--force] [--race 2024_silverstone]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import fastf1
import pandas as pd

from src.common.config import ConfigSection, load_config
from src.common.errors import StratexError
from src.data.cleaning.quality import check_race
from src.data.sources import fastf1 as fastf1_source
from src.data.sources import openf1 as openf1_source
from src.data.spec.frames import RaceFrames
from src.data.spec.races import Race, load_races

READERS = {"fastf1": fastf1_source.read_race, "openf1": openf1_source.read_race}
TABLES = ("laps", "weather", "track_status")


def main(arguments: list[str] | None = None) -> int:
    """Ingest every race, report every failure, and return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="rebuild races that are up to date")
    parser.add_argument("--race", help="ingest only this race id")
    options = parser.parse_args(arguments)

    config = load_config("configs/ingest.yaml")
    races = [r for r in load_races() if options.race in (None, r.id)]
    if not races:
        print(f"unknown race id '{options.race}'")
        return 1

    failures = []
    built = 0
    for race in races:
        try:
            built += ingest_race(race, config, options.force)
        except StratexError as error:
            failures.append(str(error))
            print(f"FAILED  {error}")
    print(f"{len(races)} races: {built} built, {len(races) - built - len(failures)} up to date, "
          f"{len(failures)} failed")
    return 1 if failures else 0


def ingest_race(race: Race, config: ConfigSection, force: bool = False) -> bool:
    """Build one race. Returns False when it was already up to date."""
    folder = Path(config["paths"]["interim"]) / race.id
    if not force and _up_to_date(folder, race, config):
        return False
    frames = read_race(race, config)
    summary = check_race(race, frames, config["checks"])
    folder.mkdir(parents=True, exist_ok=True)
    manifest_file = folder / "manifest.json"
    manifest_file.unlink(missing_ok=True)
    for table in TABLES:
        getattr(frames, table).to_parquet(folder / f"{table}.parquet", index=False)
    manifest = {
        **_identity(race, config),
        "fastf1_version": fastf1.__version__ if race.source == "fastf1" else "",
        "race_laps": frames.race_laps,
        "dropped_laps": frames.dropped_laps,
        "rows": {table: len(getattr(frames, table)) for table in TABLES},
        "hash": {table: content_hash(getattr(frames, table)) for table in TABLES},
        "summary": summary,
    }
    # Written last, so an interrupted run never looks finished.
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"built   {race.id}: {summary}")
    return True


def read_race(race: Race, config: ConfigSection) -> RaceFrames:
    """Read one race from its source in the common format."""
    reader = READERS[race.source]
    return reader(race, Path(config["paths"]["raw"]), config["sector_sum_tolerance_s"])


def content_hash(frame: pd.DataFrame) -> str:
    """Hash of a table's values, independent of the parquet library."""
    text = frame.to_csv(index=False, lineterminator="\n", na_rep="")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _identity(race: Race, config: ConfigSection) -> dict[str, Any]:
    return {
        "version": config["version"],
        "id": race.id,
        "circuit": race.circuit,
        "year": race.year,
        "source": race.source,
        "event": race.event,
        "session_key": race.session_key,
        "role": race.role,
        "repairs": list(race.repairs),
        "sector_sum_tolerance_s": config["sector_sum_tolerance_s"],
    }


def _up_to_date(folder: Path, race: Race, config: ConfigSection) -> bool:
    manifest_file = folder / "manifest.json"
    if not manifest_file.exists():
        return False
    if not all((folder / f"{table}.parquet").exists() for table in TABLES):
        return False
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    identity = _identity(race, config)
    return all(key in manifest and manifest[key] == value for key, value in identity.items())


if __name__ == "__main__":
    sys.exit(main())
