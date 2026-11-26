from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.calibration.conditions.table import RaceConditions
from src.calibration.fitting_races import FittingRace
from src.calibration.models.chains import count_steps, shares
from src.calibration.models.weather import rain_slowdown, weather_fields
from src.common.errors import CalibrationError
from src.data.spec.frames import RaceFrames

PENALTY = {
    "DRY": {"SOFT": 0.0, "MEDIUM": 0.0, "HARD": 0.0, "INTERMEDIATE": 4.0, "WET": 10.0},
    "DAMP": {"SOFT": 6.0, "MEDIUM": 4.0, "HARD": 3.0, "INTERMEDIATE": 0.0, "WET": 2.5},
    "WET": {"SOFT": 15.0, "MEDIUM": 12.0, "HARD": 10.0, "INTERMEDIATE": 3.0, "WET": 0.0},
}
CONFIG = {
    "weather": {"min_lap": 4},
    "fuel": {"consumption_kg_per_lap": 2.0, "sensitivity_s_per_kg": 0.05},
    "weather_penalty_defaults": PENALTY,
}
LETTERS = {".": "DRY", "d": "DAMP", "W": "WET"}
LAPS = 12


def make_race(weather, slower=None, race_id="2022_toy", rejection="", cars=(("A", 80.0), ("B", 100.0))):
    """One letter of weather per lap; `slower` maps a regime to its share slower."""
    weather = weather.ljust(LAPS, ".")
    regimes = [LETTERS[x] for x in weather]
    rows = []
    for car, pace in cars:
        for lap, regime in enumerate(regimes, start=1):
            share = (slower or {}).get(regime, 0.0)
            fuel = 0.1 * (LAPS - lap)
            compound = {"DAMP": "INTERMEDIATE", "WET": "WET"}.get(regime, "MEDIUM")
            rows.append(
                {
                    "driver": car,
                    "lap": lap,
                    "lap_time_s": pace * (1 + share) + fuel,
                    "compound": compound,
                    "is_accurate": True,
                    "track_status": "1",
                }
            )
    table = pd.DataFrame(
        {"status": "GREEN", "regime": pd.array(regimes, dtype="string")}, index=range(1, LAPS + 1)
    )
    if rejection:
        table["regime"] = pd.NA
    frames = RaceFrames(pd.DataFrame(rows), pd.DataFrame(), pd.DataFrame(), LAPS, 0)
    return FittingRace(frames, RaceConditions(SimpleNamespace(id=race_id), table, rejection))


def test_counts_by_hand():
    # Fails if rows and columns are swapped, or labels outside the chain join it.
    sequences = [pd.Series(list("aab")), pd.Series(list("bxa")), pd.Series([], dtype=object)]
    start, counts = count_steps(sequences, ("a", "b"))
    assert start.to_dict() == {"a": 1, "b": 1}
    assert counts.loc["a"].to_dict() == {"a": 1, "b": 1}
    assert counts.loc["b"].to_dict() == {"a": 0, "b": 0}


def test_unseen_state_is_refused():
    # Fails if a state without data gets made-up chances.
    with pytest.raises(CalibrationError, match="'WET' was never seen"):
        shares(pd.Series([0, 0], index=["DRY", "WET"], name="WET"))


def test_rain_makes_every_car_slower_by_the_same_share():
    # Fails if fuel or a car's own pace counts as rain, or the shares are taken in seconds.
    race = make_race("....dddddWWW", {"DAMP": 0.1, "WET": 0.2})
    assert rain_slowdown([race], "DAMP", "INTERMEDIATE", CONFIG) == (pytest.approx(0.1), 1)
    assert rain_slowdown([race], "WET", "WET", CONFIG) == (pytest.approx(0.2), 1)


def slowdown_with(weather, *changes):
    """Damp slowdown (truly 0.1) after `changes`: (laps, column, value)."""
    race = make_race(weather, {"DAMP": 0.1, "WET": 0.3})
    laps = race.frames.laps
    for chosen, column, value in changes:
        laps.loc[laps["lap"].isin(chosen), column] = value
    return rain_slowdown([race], "DAMP", "INTERMEDIATE", CONFIG)[0]


FIRST_RAIN = (5, 6, 7, 8)
LATE_DRY = (7, 8, 9, 10, 11)


@pytest.mark.parametrize(
    "weather, changes",
    [
        # fails if a lap under a flag or with broken timing counts
        ("....dddddd..", [(FIRST_RAIN, "track_status", "14"), (FIRST_RAIN, "lap_time_s", 500.0)]),
        ("....dddddd..", [(FIRST_RAIN, "is_accurate", False), (FIRST_RAIN, "lap_time_s", 500.0)]),
        # fails if the opening laps count
        ("ddddd.......", [((1, 2, 3), "lap_time_s", 500.0)]),
        # fails if slicks on a damp track count as the rain tyre
        ("....dddddd..", [(FIRST_RAIN, "compound", "MEDIUM"), (FIRST_RAIN, "lap_time_s", 500.0)]),
        # fails if a dry lap on rain tyres counts as dry pace
        ("....dd......", [(LATE_DRY, "compound", "INTERMEDIATE"), (LATE_DRY, "lap_time_s", 50.0)]),
        # fails if slicks on a wet track count as dry pace
        (".....ddWWWWW", [((8, 9, 10, 11, 12), "compound", "MEDIUM")]),
    ],
)
def test_unusable_laps_are_left_out(weather, changes):
    assert slowdown_with(weather, *changes) == pytest.approx(0.1)


def test_neutralised_laps_by_the_leader_are_left_out():
    # Fails if laps the leader ran behind a safety car count, although the car's flag is clear.
    race = make_race("....dddddd..", {"DAMP": 0.1})
    race.conditions.table.loc[5:8, "status"] = "SC"
    laps = race.frames.laps
    laps.loc[laps["lap"].between(5, 8), "lap_time_s"] = 500.0
    assert rain_slowdown([race], "DAMP", "INTERMEDIATE", CONFIG)[0] == pytest.approx(0.1)


def test_median_over_cars():
    # Fails if one car's odd rain pace moves the result.
    race = make_race("....dddddd..", {"DAMP": 0.1}, cars=(("A", 80.0), ("B", 90.0), ("C", 100.0)))
    laps = race.frames.laps
    laps.loc[(laps["driver"] == "C") & laps["lap"].between(5, 10), "lap_time_s"] *= 3
    assert rain_slowdown([race], "DAMP", "INTERMEDIATE", CONFIG)[0] == pytest.approx(0.1)


def test_median_over_races():
    # Fails if one odd race, or the race with the most laps, sets the slowdown.
    races = [
        make_race("....dd", {"DAMP": 0.08}, race_id="a"),
        make_race("....dddd", {"DAMP": 0.10}, race_id="b"),
        make_race("....dddddd", {"DAMP": 0.60}, race_id="c"),
        make_race("............", race_id="dry"),
    ]
    assert rain_slowdown(races, "DAMP", "INTERMEDIATE", CONFIG) == (pytest.approx(0.10), 3)


def test_no_rain_running_is_refused():
    # Fails if a weather without data gets a made-up slowdown.
    with pytest.raises(CalibrationError, match="no race with WET running in WET"):
        rain_slowdown([make_race("....dd", {"DAMP": 0.1})], "WET", "WET", CONFIG)


def races_for_fields():
    return [
        make_race("....dddWWWWW", {"DAMP": 0.1, "WET": 0.2}, race_id="a"),
        make_race("dddddd", {"DAMP": 0.1}, race_id="b"),
        make_race("", race_id="c"),
        make_race("WW", race_id="rejected", rejection="known tyres fall to 30%"),
    ]


def test_fields():
    # Fails if rain is added to some tyres only (D34), or a rejected race is counted.
    fields = weather_fields(races_for_fields(), 90.0, CONFIG)
    penalty = fields.values["weather_compound_penalty"]
    assert penalty["DRY"] == PENALTY["DRY"]
    for weather, share in (("DAMP", 0.1), ("WET", 0.2)):
        for compound, prior in PENALTY[weather].items():
            assert penalty[weather][compound] == pytest.approx(prior + share * 90.0)
    start = fields.values["weather_start"]
    assert start == pytest.approx({"DRY": 2 / 3, "DAMP": 1 / 3, "WET": 0.0})
    chain = fields.values["weather_transition"]
    assert chain["DAMP"] == pytest.approx({"DRY": 1 / 9, "DAMP": 7 / 9, "WET": 1 / 9})
    assert chain["WET"]["WET"] == 1.0
    assert fields.diagnostics["races"] == 3
    assert fields.diagnostics["rejected"] == ["rejected"]
    assert fields.diagnostics["slowdown_races"] == {"DAMP": 2, "WET": 1}
    assert fields.diagnostics["transition_counts"]["DAMP"]["WET"] == 1
    assert fields.diagnostics["transition_counts"]["WET"]["DAMP"] == 0


def test_provenance():
    # Fails if a prior is called measured, or a field has no source (D10).
    provenance = weather_fields(races_for_fields(), 90.0, CONFIG).provenance
    measured = {k for k, v in provenance.items() if v == "pooled"}
    assert measured == {
        "weather_start",
        "weather_transition",
        "weather_compound_penalty.DAMP.INTERMEDIATE",
        "weather_compound_penalty.WET.WET",
    }
    assert len(provenance) == 2 + 15
    assert set(provenance.values()) == {"pooled", "prior"}


def test_tyre_choice_in_the_rain_is_unchanged():
    # Fails if the slowdown changes which tyre is fastest in any weather (D34).
    penalty = weather_fields(races_for_fields(), 90.0, CONFIG).values["weather_compound_penalty"]
    for weather, prior in PENALTY.items():
        order = np.argsort(list(penalty[weather].values())).tolist()
        assert order == np.argsort(list(prior.values())).tolist()


def test_rain_tyre_must_be_clear():
    # Fails if a penalty table without one rain tyre per weather is used.
    two_rain_tyres = PENALTY | {"WET": PENALTY["WET"] | {"INTERMEDIATE": 0.0}}
    config = CONFIG | {"weather_penalty_defaults": two_rain_tyres}
    with pytest.raises(CalibrationError, match="WET need one tyre"):
        weather_fields(races_for_fields(), 90.0, config)
    # Fails if a small penalty is taken for none.
    close = PENALTY | {"WET": PENALTY["WET"] | {"INTERMEDIATE": 0.4}}
    weather_fields(races_for_fields(), 90.0, CONFIG | {"weather_penalty_defaults": close})
