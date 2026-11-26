from types import SimpleNamespace

import pandas as pd
import pytest

from src.calibration.conditions.table import race_conditions
from src.common.errors import CalibrationError
from src.data.spec.frames import RaceFrames

RULES = {
    "min_known_tyre_share": 0.5,
    "damp_start_share": 0.3,
    "damp_end_share": 0.7,
    "wet_share": 0.5,
    "median_filter_laps": 3,
}
RACE = SimpleNamespace(id="toy", role="fit")


def frames(known_cars, race_laps=2):
    rows = []
    for lap in (1, 2):
        for car in range(5):
            known = car < known_cars
            rows.append(
                {
                    "lap": lap,
                    "lap_start_s": 100.0 * (lap - 1),
                    "lap_end_s": 100.0 * lap + car,
                    "compound": "SOFT" if known else "UNKNOWN",
                    "label": "raw" if known else "missing",
                }
            )
    weather = pd.DataFrame(
        {"time_s": [0.0], "rainfall": [False], "air_temp_c": [20.0], "track_temp_c": [30.0]}
    )
    status = pd.DataFrame({"time_s": [0.0, 150.0], "code": ["1", "4"]})
    return RaceFrames(pd.DataFrame(rows), weather, status, race_laps, 0)


def test_labelled_race():
    # Fails if a column is lost or status and regime are swapped.
    conditions = race_conditions(RACE, frames(known_cars=5), RULES)
    assert conditions.weather_rejection == ""
    assert conditions.table["status"].tolist() == ["GREEN", "SC"]
    assert conditions.table["regime"].tolist() == ["DRY", "DRY"]


def test_rejected_weather_keeps_the_track_status():
    # Fails if a rejected race still gets regimes, or loses its safety cars (D29).
    conditions = race_conditions(RACE, frames(known_cars=2), RULES)
    assert conditions.weather_rejection.startswith("known tyres fall to 40%")
    assert conditions.table["regime"].isna().all()
    assert conditions.table["status"].tolist() == ["GREEN", "SC"]


def test_errors_name_the_race():
    # Fails if the race id is missing from the message.
    with pytest.raises(CalibrationError, match="toy"):
        race_conditions(RACE, frames(known_cars=5, race_laps=3), RULES)
