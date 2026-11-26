from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.calibration.conditions.table import RaceConditions
from src.calibration.fitting_races import FittingRace
from src.calibration.models.pit_stops import collect_stops, pit_fields, race_stops
from src.common.errors import CalibrationError
from src.data.spec.frames import RaceFrames

CONFIG = {"pit_stops": {"min_lap": 4, "min_peers": 4}}
LAPS = 20
CARS = 8
PACE = {f"C{i}": 90.0 + 0.2 * i for i in range(CARS)}


def make_race(stops, trend=0.0, flags=None, status=None, regime="DRY", circuit="toy", role="fit", bunched=()):
    """Eight cars of different pace. `stops` maps (car, lap) to the time the stop costs."""
    rows = []
    for car, pace in PACE.items():
        clock = 0.0
        for lap in range(1, LAPS + 1):
            time = 140.0 if lap in bunched else pace + trend * lap
            time += 0.8 * stops.get((car, lap), 0.0) + 0.2 * stops.get((car, lap - 1), 0.0)
            clock += time
            rows.append(
                {
                    "driver": car,
                    "lap": lap,
                    "lap_time_s": time,
                    "lap_end_s": clock,
                    "is_in_lap": (car, lap) in stops,
                    "is_out_lap": (car, lap - 1) in stops,
                    "track_status": (flags or {}).get(lap, "1"),
                }
            )
    table = pd.DataFrame({"status": "GREEN", "regime": regime}, index=range(1, LAPS + 1))
    for lap, value in (status or {}).items():
        table.loc[lap, "status"] = value
    race = SimpleNamespace(id="2022_" + circuit, circuit=circuit, year=2022, role=role)
    frames = RaceFrames(pd.DataFrame(rows), pd.DataFrame(), pd.DataFrame(), LAPS, 0)
    return FittingRace(frames, RaceConditions(race, table, ""))


def test_green_stop_is_recovered_whatever_the_car_and_the_trend():
    # Fails if a slow car's pace, or a track that gets faster, counts as pit loss.
    race = make_race({("C0", 6): 21.0, ("C7", 12): 25.0}, trend=-0.1)
    stops = race_stops(race, CONFIG).set_index("car")
    assert stops["loss"].to_dict() == pytest.approx({"C0": 21.0, "C7": 25.0}, abs=0.21)
    assert stops["kind"].tolist() == ["GREEN", "GREEN"]
    assert stops.loc["C7", ["race", "circuit", "lap"]].tolist() == ["2022_toy", "toy", 12]


def test_cars_that_stop_too_are_not_peers():
    # Fails if a rival's own stop, on the same lap or the one before or after, hides the cost.
    stops = {("C0", 8): 20.0, ("C1", 8): 20.0, ("C2", 7): 20.0, ("C3", 9): 20.0}
    found = race_stops(make_race(stops), CONFIG)
    assert found["loss"].tolist() == pytest.approx([20.0] * 4, abs=1e-6)


def test_cars_about_to_stop_are_not_peers():
    # Fails if a rival's in-lap, one lap later, hides the cost.
    stops = {("C0", 8): 20.0} | {(f"C{i}", 9): 20.0 for i in range(1, 5)}
    rules = {"pit_stops": {"min_lap": 4, "min_peers": 3}}
    found = race_stops(make_race(stops), rules).set_index("car")["loss"]
    assert found["C0"] == pytest.approx(20.0, abs=1e-6)


def test_usual_pace_comes_from_green_laps():
    # Fails if a long safety car makes every car look equally fast.
    late = range(9, LAPS + 1)
    race = make_race({("C7", 6): 20.0}, status={lap: "SC" for lap in late}, bunched=late)
    assert race_stops(race, CONFIG)["loss"].tolist() == pytest.approx([20.0], abs=1e-6)


def test_first_allowed_lap():
    # Fails if the limit itself is left out.
    assert len(race_stops(make_race({("C0", 4): 20.0}), CONFIG)) == 1


def test_too_few_peers():
    # Fails if a stop is measured against three cars.
    stops = {(f"C{i}", 8): 20.0 for i in range(5)}
    assert race_stops(make_race(stops), CONFIG).empty
    del stops["C4", 8]
    race = make_race(stops)
    assert len(race_stops(race, CONFIG)) == 4
    # Fails if a peer without a time counts as one.
    laps = race.frames.laps
    laps.loc[(laps["driver"] == "C7") & (laps["lap"] == 9), "lap_end_s"] = np.nan
    assert race_stops(race, CONFIG).empty


@pytest.mark.parametrize("lap", [2, 3, LAPS])
def test_stops_at_the_ends_of_the_race_are_left_out(lap):
    # Fails if the opening laps or a stop on the last lap are used.
    assert race_stops(make_race({("C0", lap): 20.0}), CONFIG).empty


def test_in_lap_without_an_out_lap_is_no_stop():
    # Fails if a car that retires in the pits counts.
    race = make_race({("C0", 8): 20.0})
    race.frames.laps["is_out_lap"] = False
    assert race_stops(race, CONFIG).empty


def test_unknown_times_are_left_out():
    # Fails if a missing time becomes a loss, or removes the other stops (E5).
    race = make_race({("C0", 8): 20.0, ("C1", 8): 22.0})
    laps = race.frames.laps
    laps.loc[(laps["driver"] == "C0") & (laps["lap"] == 9), "lap_end_s"] = np.nan
    laps.loc[(laps["driver"] == "C7") & (laps["lap"] == 9), "lap_end_s"] = np.nan
    assert race_stops(race, CONFIG)["loss"].tolist() == pytest.approx([22.0])


@pytest.mark.parametrize(
    "status, flags, kind",
    [
        ({8: "SC", 9: "SC"}, {8: "14", 9: "4"}, "SC"),
        ({8: "SC"}, {8: "4", 9: "14"}, "SC"),
        ({8: "VSC"}, {8: "16", 9: "17"}, "VSC"),  # fails if SC and VSC are swapped
        ({}, {8: "12"}, None),  # fails if a stop under a yellow flag is green
        ({}, {9: "14"}, None),  # fails if a safety car on the out-lap is ignored
        ({7: "SC", 8: "SC"}, {7: "4", 8: "4", 9: "1"}, None),  # fails if late SC stops are used
        ({7: "VSC", 8: "SC"}, {8: "4"}, None),
        ({8: "SC", 9: "RED"}, {8: "4", 9: "45"}, None),  # fails if a red flag is used
        ({8: "RED", 9: "RED"}, {8: "5", 9: "5"}, None),
    ],
)
def test_kind_of_stop(status, flags, kind):
    stops = race_stops(make_race({("C0", 8): 14.0}, flags=flags, status=status), CONFIG)
    assert stops["kind"].tolist() == ([kind] if kind else [])


def test_only_fully_dry_fit_races_are_used():
    # Fails if rain, or a conditions-only race, reaches the pit loss.
    stop = {("C0", 8): 20.0}
    races = [
        make_race(stop, circuit="dry"),
        make_race(stop, circuit="wet", regime="DAMP"),
        make_race(stop, circuit="spare", role="conditions_only"),
        make_race(stop, circuit="dry_too"),
    ]
    stops = collect_stops(races, CONFIG)
    assert stops["circuit"].tolist() == ["dry", "dry_too"]
    assert stops.index.is_unique
    with pytest.raises(CalibrationError, match="no dry race"):
        collect_stops(races[1:3], CONFIG)


def stop_table():
    rows = [("a", "GREEN", loss) for loss in (19.0, 20.0, 21.0, 60.0, 20.0)]
    rows += [("b", "GREEN", loss) for loss in (30.0, 30.0)]
    rows += [("a", "SC", 14.0), ("b", "SC", 18.0), ("b", "SC", 24.0), ("c", "SC", 1.0)]
    rows += [("a", "VSC", 12.0), ("b", "VSC", 15.0)]
    table = pd.DataFrame(rows, columns=["circuit", "kind", "loss"])
    return table.assign(race="2022_" + table["circuit"], car="C0", lap=8)


def test_fields():
    # Fails if a slow stop moves the pit loss, SC seconds are not taken relative to their own
    # circuit, or a circuit without green stops (c) is used.
    fields = pit_fields("a", stop_table())
    assert fields.values == pytest.approx(
        {"pit_loss": 20.0, "pit_loss_sc_multiplier": 0.7, "pit_loss_vsc_multiplier": 0.55}
    )
    assert fields.provenance == {
        "pit_loss": "fitted",
        "pit_loss_sc_multiplier": "pooled",
        "pit_loss_vsc_multiplier": "pooled",
    }
    assert fields.diagnostics == {
        "green_stops": 5,
        "green_quartiles": [20.0, 21.0],
        "SC_stops": 3,
        "SC_races": 2,
        "SC_quartiles": pytest.approx([0.65, 0.75]),
        "VSC_stops": 2,
        "VSC_races": 2,
        "VSC_quartiles": pytest.approx([0.525, 0.575]),
    }
    assert pit_fields("b", stop_table()).values["pit_loss"] == 30.0


def test_missing_stops_are_refused():
    # Fails if a circuit or a multiplier without data gets a made-up number.
    stops = stop_table()
    with pytest.raises(CalibrationError, match="c: no green"):
        pit_fields("c", stops)
    with pytest.raises(CalibrationError, match="no VSC"):
        pit_fields("a", stops[stops["kind"] != "VSC"])
