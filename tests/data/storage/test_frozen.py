import json

import pandas as pd
import pytest

from src.common.errors import CalibrationError
from src.data.storage.frozen import load_race


def test_round_trip(tmp_path):
    # Fails if a table is swapped or the race distance is not taken from the manifest.
    folder = tmp_path / "toy"
    folder.mkdir()
    for name in ("laps", "weather", "track_status"):
        pd.DataFrame({"table": [name]}).to_parquet(folder / f"{name}.parquet")
    manifest = {"race_laps": 52, "dropped_laps": 3}
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    race = load_race("toy", tmp_path)
    assert [race.laps["table"][0], race.weather["table"][0], race.track_status["table"][0]] == [
        "laps",
        "weather",
        "track_status",
    ]
    assert (race.race_laps, race.dropped_laps) == (52, 3)


def test_unfrozen_race_is_refused(tmp_path):
    # Fails if a missing race gives a plain file error instead of saying what to run.
    with pytest.raises(CalibrationError, match="src.data.ingest"):
        load_race("toy", tmp_path)
