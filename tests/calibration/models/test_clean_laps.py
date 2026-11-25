from types import SimpleNamespace

import pandas as pd
import pytest

from src.calibration.conditions.table import RaceConditions
from src.calibration.models import clean_laps as module
from src.calibration.models.clean_laps import clean_laps, collect_clean_laps, is_fully_dry
from src.common.errors import CalibrationError
from src.data.spec.frames import RaceFrames

CONFIG = {
    "conditions": {},
    "fuel": {"consumption_kg_per_lap": 2.0, "sensitivity_s_per_kg": 0.05},
    "tyres": {
        "fit_seasons": (2022, 2023),
        "min_lap": 4,
        "min_tyre_age": 3,
        "max_gap_to_median_s": 3.0,
    },
}
LAPS = 12


def race(race_id="2022_toy", role="fit"):
    return SimpleNamespace(id=race_id, circuit="toy", year=int(race_id[:4]), role=role)


def frames(**changes):
    """One car, one stint; `changes` maps a column to {lap: value}."""
    laps = pd.DataFrame(
        {
            "driver": "VER",
            "lap": range(1, LAPS + 1),
            "lap_time_s": 90.0,
            "stint": 1,
            "compound": "MEDIUM",
            "tyre_age": pd.array(range(1, LAPS + 1), dtype="Int64"),
            "label": "raw",
            "is_accurate": True,
            "track_status": "1",
        }
    )
    for column, values in changes.items():
        for lap, value in values.items():
            laps.loc[laps["lap"] == lap, column] = value
    return RaceFrames(laps, pd.DataFrame(), pd.DataFrame(), LAPS, 0)


def conditions(status=None, regime=None, rejection="", of=None):
    table = pd.DataFrame({"status": "GREEN", "regime": "DRY"}, index=range(1, LAPS + 1))
    for column, values in (("status", status), ("regime", regime)):
        for lap, value in (values or {}).items():
            table.loc[lap, column] = value
    return RaceConditions(of or race(), table, rejection)


def kept(changed_frames, given=None):
    table, _ = clean_laps(changed_frames, given or conditions(), CONFIG)
    return table["lap"].astype(int).tolist()


ALL = list(range(4, LAPS + 1))
NOT_8 = [lap for lap in ALL if lap != 8]


@pytest.mark.parametrize(
    "changes",
    [
        {"compound": {8: "INTERMEDIATE"}},  # fails if a rain tyre is kept
        {"compound": {8: "UNKNOWN"}},
        {"label": {8: "suspect"}},  # fails if an untrusted tyre is kept
        {"label": {8: "missing"}},
        {"track_status": {8: "12"}},  # fails if a lap with a yellow flag is kept
        {"is_accurate": {8: False}},  # fails if pit laps or broken timing are kept
        {"tyre_age": {8: 2}},  # fails if warm-up laps are kept
        {"tyre_age": {8: pd.NA}},  # fails if an unknown age is kept
        {"lap_time_s": {8: 93.1}},  # fails if slow laps are kept
        {"lap_time_s": {8: 86.9}},  # fails if only slow laps are cut
    ],
)
def test_lap_is_dropped(changes):
    assert kept(frames(**changes)) == NOT_8


@pytest.mark.parametrize(
    "changes",
    [
        {"lap_time_s": {8: 93.0}},  # fails if the limit itself is cut
        {"tyre_age": {8: 3}},  # fails if the first settled lap is cut
        {"label": {8: "shifted"}},  # fails if repaired labels are thrown away
        {"label": {8: "repaired"}},
        {"compound": {8: "HARD"}},
    ],
)
def test_lap_is_kept(changes):
    assert kept(frames(**changes)) == ALL


def test_opening_laps_are_dropped():
    # Fails if laps 1-3 of cars on old tyres are kept.
    assert kept(frames(tyre_age={1: 9, 2: 9, 3: 9})) == ALL


@pytest.mark.parametrize("status", ["SC", "VSC", "RED"])
def test_neutralised_laps_are_dropped(status):
    # Fails if the status of the race is ignored when the car's own flag is clear.
    assert kept(frames(), conditions(status={8: status})) == NOT_8


def test_median_is_per_driver():
    # Fails if a slow car is compared with the fast ones.
    fast, slow = frames().laps, frames().laps.assign(driver="SAR", lap_time_s=99.0)
    both = RaceFrames(
        pd.concat([fast, slow], ignore_index=True), pd.DataFrame(), pd.DataFrame(), LAPS, 0
    )
    table, _ = clean_laps(both, conditions(), CONFIG)
    assert table.groupby("car").size().to_dict() == {"2022_toy VER": 9, "2022_toy SAR": 9}


def test_fuel_matches_the_simulator():
    # Fails if the last lap still carries fuel, or the sign is wrong.
    table, _ = clean_laps(frames(), conditions(), CONFIG)
    pace = table.set_index("lap")["pace"]
    assert pace[LAPS] == pytest.approx(90.0)
    assert pace[LAPS - 5] == pytest.approx(90.0 - 5 * 0.1)


def test_cars_and_stints_of_two_races_differ():
    # Fails if a driver shares one pace, or one stint, over two races.
    a, _ = clean_laps(frames(stint={9: 2, 10: 2, 11: 2, 12: 2}), conditions(), CONFIG)
    b, _ = clean_laps(frames(), conditions(of=race("2023_toy")), CONFIG)
    assert a["stint"].nunique() == 2
    assert not set(a["car"]) & set(b["car"])
    assert not set(a["stint"]) & set(b["stint"])


def test_counts_after_each_step():
    # Fails if the report does not add up.
    changed = frames(compound={5: "WET"}, track_status={6: "4"}, lap_time_s={7: 120.0})
    _, counts = clean_laps(changed, conditions(), CONFIG)
    assert counts == {
        "all": 12,
        "known_dry_tyre": 11,
        "green": 10,
        "accurate": 10,
        "settled": 7,
        "near_median": 6,
    }


def test_fully_dry():
    # Fails if a race with one damp lap, or without weather labels, counts as dry.
    assert is_fully_dry(conditions())
    assert not is_fully_dry(conditions(regime={5: "DAMP"}))
    assert not is_fully_dry(conditions(rejection="known tyres fall to 40%"))


@pytest.fixture
def season(monkeypatch):
    """Frozen races replaced by the toy race; one race can be made damp."""
    monkeypatch.setattr(module, "load_race", lambda race_id, interim_dir: frames())

    def build(one_race, _frames, _rules):
        damp = {5: "DAMP"} if "damp" in one_race.id else None
        return conditions(regime=damp, of=one_race)

    monkeypatch.setattr(module, "race_conditions", build)


def test_only_dry_fit_races_of_the_seasons_are_used(season):
    # Fails if 2021, a damp race or a conditions-only race reaches the fit.
    races = [
        race("2021_old"),
        race("2022_dry"),
        race("2023_dry"),
        race("2022_damp"),
        race("2023_spare", role="conditions_only"),
        race("2025_held", role="holdout"),
    ]
    laps, counts = collect_clean_laps(races, "unused", CONFIG)
    assert laps["race"].unique().tolist() == ["2022_dry", "2023_dry"]
    assert counts.index.tolist() == ["2022_dry", "2023_dry"]
    assert laps.index.is_unique


def test_held_out_race_is_refused(season):
    # Fails if a wrong season list lets the holdout into the fit (D25).
    with pytest.raises(CalibrationError, match="2023_held"):
        collect_clean_laps([race("2023_held", role="holdout")], "unused", CONFIG)


def test_no_dry_race_is_refused(season):
    # Fails if an empty fit goes on.
    with pytest.raises(CalibrationError, match="no dry race"):
        collect_clean_laps([race("2022_damp")], "unused", CONFIG)
