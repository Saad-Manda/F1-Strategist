"""Load a race that ingest has frozen."""

import json
from pathlib import Path

import pandas as pd

from src.common.errors import CalibrationError
from src.data.spec.frames import RaceFrames


def load_race(race_id: str, interim_dir: str | Path) -> RaceFrames:
    """One frozen race in the common format."""
    folder = Path(interim_dir) / race_id
    manifest_file = folder / "manifest.json"
    if not manifest_file.exists():
        raise CalibrationError(f"{race_id}: not frozen, run python -m src.data.ingest")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    return RaceFrames(
        laps=pd.read_parquet(folder / "laps.parquet"),
        weather=pd.read_parquet(folder / "weather.parquet"),
        track_status=pd.read_parquet(folder / "track_status.parquet"),
        race_laps=manifest["race_laps"],
        dropped_laps=manifest["dropped_laps"],
    )
