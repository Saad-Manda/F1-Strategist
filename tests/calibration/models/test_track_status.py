from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.calibration.conditions.table import RaceConditions
from src.calibration.fitting_races import FittingRace
from src.calibration.models.track_status import (
    FlagPeriod,
    flag_lap_ratio,
    flag_periods,
    status_counts,
    status_fields,
)
from src.common.errors import CalibrationError

CONFIG = {"flag_laps": {"min_lap": 4, "noise_std": 1.5}}
CODES = {"G": "GREEN", "S": "SC", "V": "VSC", "R": "RED"}
LAP = 80.0


def make_race(letters, slow=None, regime=None, circuit="toy", rejection="", green=LAP):
    """One letter per lap; `slow` maps a lap to its time in green laps."""
    laps = range(1, len(letters) + 1)
    times = pd.Series(green, index=laps)
    for lap, ratio in (slow or {}).items():
        times[lap] = ratio * green
    end = times.cumsum()
    regimes = pd.Series("DRY", index=laps, dtype="string")
    for lap, value in (regime or {}).items():
        regimes[lap] = value
    if rejection:
        regimes[:] = pd.NA
    table = pd.DataFrame(
        {
            "start_s": end - times,
            "end_s": end,
            "status": pd.array([CODES[x] for x in letters], dtype="string"),
            "regime": regimes,
        }
    )
    race = SimpleNamespace(id="2022_" + circuit, circuit=circuit, year=2022, role="fit")
    return FittingRace(None, RaceConditions(race, table, rejection))


def test_counts_by_hand():
    # Fails if rows and columns are swapped, or the last lap makes a step.
    start, counts = status_counts([make_race("GGSSG"), make_race("SGVSG")])
    assert start.to_dict() == {"GREEN": 1, "SC": 1, "VSC": 0}
    assert counts.loc["GREEN"].to_dict() == {"GREEN": 1, "SC": 1, "VSC": 1}
    assert counts.loc["SC"].to_dict() == {"GREEN": 3, "SC": 1, "VSC": 0}
    assert counts.loc["VSC"].to_dict() == {"GREEN": 0, "SC": 1, "VSC": 0}


def test_red_flags_leave_the_chain_alone():
    # Fails if a red flag is counted as green, or joins the laps around it.
    start, counts = status_counts([make_race("RRGGSRRG")])
    assert start.sum() == 0
    assert counts.sum().sum() == 2
    assert counts.loc["GREEN", "GREEN"] == counts.loc["GREEN", "SC"] == 1


def test_a_known_chain_is_recovered():
    # Fails if the chain is transposed or normalised over columns.
    true = np.array([[0.94, 0.04, 0.02], [0.3, 0.7, 0.0], [0.6, 0.1, 0.3]])
    rng = np.random.default_rng(5)
    races = []
    for _ in range(150):
        state, letters = 0, ""
        for _ in range(60):
            letters += "GSV"[state]
            state = rng.choice(3, p=true[state])
        races.append(make_race(letters))
    chain = status_fields("toy", races, CONFIG).values["status_transition"]
    found = np.array([list(row.values()) for row in chain.values()])
    assert found == pytest.approx(true, abs=0.04)
    assert found.sum(axis=1) == pytest.approx(1.0)


def test_lost_time_includes_the_slow_lap_after_the_period():
    # Fails if the restart lap is left out (D31): 0.2 + 0.7 + 0.6 green laps are lost.
    (period,) = flag_periods(make_race("GGGGGSSGGG", {6: 1.2, 7: 1.7, 8: 1.6}), CONFIG)
    assert (period.status, period.laps) == ("SC", 2)
    assert period.extra == pytest.approx(1.5)


def test_lost_time_is_relative_to_the_dry_laps():
    # Fails if damp laps make the green lap slower, so the safety car looks faster.
    damp = {lap: "DAMP" for lap in range(8, 17)}
    slow = {lap: 1.3 for lap in damp} | {5: 1.5, 6: 1.5}
    (period,) = flag_periods(make_race("GGGGSG" + "G" * 10, slow, regime=damp), CONFIG)
    assert period.extra == pytest.approx(1.0)


def test_ratio_puts_the_lost_time_on_the_labelled_laps():
    # Fails if periods are averaged without their length, or SC and VSC are mixed.
    periods = [
        FlagPeriod("a", "SC", 1, 0.9),
        FlagPeriod("b", "SC", 4, 2.6),
        FlagPeriod("c", "VSC", 1, 0.4),
    ]
    assert flag_lap_ratio(periods, "SC") == pytest.approx(1.7)
    assert flag_lap_ratio(periods, "VSC") == pytest.approx(1.4)


@pytest.mark.parametrize(
    "race",
    [
        make_race("GGSSGGGG"),  # fails if a period of the opening laps is used
        make_race("SSSSSGGG"),
        make_race("GGGGGGSS"),  # fails if a period at the flag is used
        make_race("GGGGSRRG"),  # fails if a period that ends in a red flag is used
        make_race("GGGRSSGG"),
        make_race("GGGGRRGG"),  # fails if a red flag is a period of its own
        make_race("GGGGVSGG"),  # fails if a VSC that becomes an SC is used
        make_race("GGGGSSGG", regime={4: "DAMP"}),  # fails if rain looks like a safety car
        make_race("GGGGSSGG", regime={7: "DAMP"}),
        make_race("GGGGSSGG", rejection="x"),  # fails if unknown weather counts as dry
    ],
)
def test_unusable_periods(race):
    assert flag_periods(race, CONFIG) == []


def test_every_period_of_a_race_is_found():
    # Fails if two periods are joined, or one is dropped.
    found = flag_periods(make_race("GGGSGGVVGSSSGG"), CONFIG)
    assert [(p.status, p.laps) for p in found] == [("SC", 1), ("VSC", 2), ("SC", 3)]


def test_fields():
    # Fails if SC and VSC lap times are swapped, or another circuit's green lap is used.
    races = [
        make_race("GGGGGSGGGG", {6: 1.8, 7: 1.0}),
        make_race("VGGGGVGGGG", {1: 3.0, 6: 1.3, 7: 1.1}),
        make_race("GGGGGGGGGG", circuit="other", green=100.0),
        make_race("SSGGGGGGGG", circuit="other", green=102.0),
        make_race("GGGGGGGGGG", regime={9: "WET"}, circuit="other", green=500.0),
    ]
    fields = status_fields("other", races, CONFIG)
    assert fields.values["safety_car"]["lap_time"] == pytest.approx(1.8 * 101.0)
    assert fields.values["virtual_safety_car"]["lap_time"] == pytest.approx(1.4 * 101.0)
    assert fields.values["flag_noise_std"] == 1.5
    assert fields.values["status_start"] == pytest.approx({"GREEN": 0.6, "SC": 0.2, "VSC": 0.2})
    assert fields.provenance == {
        "status_start": "pooled",
        "status_transition": "pooled",
        "flag_noise_std": "prior",
        "safety_car.lap_time": "pooled",
        "virtual_safety_car.lap_time": "pooled",
    }
    assert fields.diagnostics["races"] == 5
    assert fields.diagnostics["flag_periods"] == {"SC": 1, "VSC": 1}
    assert fields.diagnostics["start_counts"] == {"GREEN": 3, "SC": 1, "VSC": 1}
    assert fields.diagnostics["transition_counts"]["GREEN"]["SC"] == 1
    assert fields.diagnostics["transition_counts"]["SC"]["GREEN"] == 2


def test_green_lap_ignores_the_opening_and_slow_laps():
    # Fails if the green lap includes the standing start or flags, or is the fastest lap.
    slow = {1: 2.0, 2: 2.0, 3: 2.0, 4: 0.9, 5: 1.8, 6: 1.5}
    races = [make_race("GGGGSGGGG", slow), make_race("GGGGVGGSG")]
    assert status_fields("toy", races, CONFIG).diagnostics["green_lap"] == pytest.approx(LAP)


def test_missing_data_is_refused():
    # Fails if an unseen status gets made-up chances or a made-up lap time.
    with pytest.raises(CalibrationError, match="never seen"):
        status_fields("toy", [make_race("GGGGSGGG")], CONFIG)
    with pytest.raises(CalibrationError, match="no VSC period"):
        flag_lap_ratio([FlagPeriod("a", "SC", 1, 0.9)], "VSC")
    with pytest.raises(CalibrationError, match="elsewhere: no dry race"):
        status_fields("elsewhere", [make_race("GGGGSGGG")], CONFIG)
