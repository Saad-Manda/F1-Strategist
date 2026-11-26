from types import SimpleNamespace

import pandas as pd
import pytest

from src.calibration import fitting_races as module
from src.calibration.conditions.table import RaceConditions
from src.calibration.fitting_races import FittingRace, load_fitting_races


@pytest.mark.parametrize(
    "regimes, rejection, expected",
    [
        (["DRY", "DRY"], "", True),
        (["DRY", "DAMP"], "", False),  # fails if one damp lap is ignored
        (["WET", "WET"], "", False),
        ([pd.NA, pd.NA], "known tyres fall to 40%", False),  # fails if unknown counts as dry
    ],
)
def test_fully_dry(regimes, rejection, expected):
    table = pd.DataFrame({"regime": pd.array(regimes, dtype="string")})
    race = FittingRace(None, RaceConditions(SimpleNamespace(id="toy"), table, rejection))
    assert race.fully_dry is expected


def test_only_fitting_roles_are_loaded(monkeypatch):
    # Fails if a held-out race is read at all (D25), or a rain-frequency race is fitted on.
    read = []
    monkeypatch.setattr(module, "load_race", lambda race_id, folder: read.append(race_id))
    monkeypatch.setattr(
        module, "race_conditions", lambda race, frames, rules: RaceConditions(race, None, "")
    )
    roles = ("fit", "holdout", "conditions_only", "frequency_only")
    races = [SimpleNamespace(id=role, role=role) for role in roles]
    loaded = load_fitting_races(races, "unused", {"conditions": {}})
    assert [r.race.id for r in loaded] == ["fit", "conditions_only"]
    assert read == ["fit", "conditions_only"]
