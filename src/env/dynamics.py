"""The race model: lap times, pit loss, legal actions and the two-compound rule.

Pure functions. `params` is one circuit's calibration (schema v2). Times are in seconds.
"""

from enum import IntEnum
from typing import Any

import numpy as np

Params = dict[str, Any]


class Compound(IntEnum):
    SOFT = 0
    MEDIUM = 1
    HARD = 2
    INTERMEDIATE = 3
    WET = 4


class Weather(IntEnum):
    DRY = 0
    DAMP = 1
    WET = 2


class TrackStatus(IntEnum):
    GREEN = 0
    SC = 1
    VSC = 2


class Action(IntEnum):
    STAY_OUT = 0
    PIT_SOFT = 1
    PIT_MEDIUM = 2
    PIT_HARD = 3
    PIT_INTER = 4
    PIT_WET = 5


DRY_COMPOUNDS = frozenset({Compound.SOFT, Compound.MEDIUM, Compound.HARD})
FITTABLE = {
    Weather.DRY: DRY_COMPOUNDS,
    Weather.DAMP: DRY_COMPOUNDS | {Compound.INTERMEDIATE},
    Weather.WET: frozenset({Compound.INTERMEDIATE, Compound.WET}),
}


def compound_pace_offset(compound: Compound, params: Params) -> float:
    """Pace of a fresh tyre relative to MEDIUM."""
    return params["compound_pace_offset"][compound.name]


def tyre_degradation(compound: Compound, tyre_age: int, params: Params) -> float:
    """Time lost to wear: linear, plus a cliff that grows quadratically up to `cliff_cap`."""
    tyre = params["compounds"][compound.name]
    past_cliff = max(0, tyre_age - tyre["cliff_age"])
    cliff = min(tyre["cliff_severity"] * past_cliff**2, tyre["cliff_cap"])
    return tyre["base_deg"] * tyre_age + cliff


def out_lap_warmup(compound: Compound, tyre_age: int, params: Params) -> float:
    """Time lost while a new tyre warms up, over its first two laps."""
    penalty = params["compounds"][compound.name]["warmup_penalty"]
    if tyre_age == 1:
        return penalty
    if tyre_age == 2:
        return penalty * params["warmup_second_lap_share"]
    return 0.0


def fuel_effect(laps_after: int, params: Params) -> float:
    """Time lost to the fuel still needed for the laps after this one."""
    fuel = params["fuel"]
    return laps_after * fuel["consumption_kg_per_lap"] * fuel["sensitivity_s_per_kg"]


def weather_compound_penalty(weather: Weather, compound: Compound, params: Params) -> float:
    """Time lost on this compound in this weather."""
    return params["weather_compound_penalty"][weather.name][compound.name]


def lap_time_components(
    compound: Compound,
    tyre_age: int,
    laps_after: int,
    weather: Weather,
    track_status: TrackStatus,
    params: Params,
    noise: float = 0.0,
) -> dict[str, float]:
    """The parts of a lap time. Behind a safety car the lap does not depend on the car."""
    if track_status == TrackStatus.SC:
        return {"flag_lap": params["safety_car"]["lap_time"], "noise": noise}
    if track_status == TrackStatus.VSC:
        return {"flag_lap": params["virtual_safety_car"]["lap_time"], "noise": noise}
    return {
        "base_pace": params["base_pace"],
        "compound_offset": compound_pace_offset(compound, params),
        "degradation": tyre_degradation(compound, tyre_age, params),
        "warmup": out_lap_warmup(compound, tyre_age, params),
        "fuel": fuel_effect(laps_after, params),
        "weather": weather_compound_penalty(weather, compound, params),
        "noise": noise,
    }


def compute_lap_time(
    compound: Compound,
    tyre_age: int,
    laps_after: int,
    weather: Weather,
    track_status: TrackStatus,
    params: Params,
    noise: float = 0.0,
) -> float:
    """Lap time without pit loss. With `noise=0.0` it is the exact expectation."""
    parts = lap_time_components(
        compound, tyre_age, laps_after, weather, track_status, params, noise
    )
    return sum(parts.values())


def compute_pit_loss(track_status: TrackStatus, params: Params) -> float:
    """Time a stop adds to the lap, cheaper while the field is slow."""
    if track_status == TrackStatus.SC:
        return params["pit_loss"] * params["pit_loss_sc_multiplier"]
    if track_status == TrackStatus.VSC:
        return params["pit_loss"] * params["pit_loss_vsc_multiplier"]
    return params["pit_loss"]


def action_compound(action: Action) -> Compound | None:
    """The compound an action fits, or None for STAY_OUT."""
    return None if action == Action.STAY_OUT else Compound(action - 1)


def update_rule(rule_met: bool, current: Compound, new: Compound) -> bool:
    """Two-compound rule after fitting `new` (D4)."""
    return rule_met or new not in DRY_COMPOUNDS or new != current


def compute_action_mask(
    compound: Compound, weather: Weather, laps_to_go: int, rule_met: bool
) -> np.ndarray:
    """Legal actions (C3). `laps_to_go` includes the lap about to be run."""
    mask = np.zeros(len(Action), dtype=bool)
    if laps_to_go == 1:
        mask[Action.STAY_OUT] = True
        return mask
    last_chance = laps_to_go == 2 and not rule_met
    mask[Action.STAY_OUT] = not last_chance
    for action in Action:
        new = action_compound(action)
        if new in FITTABLE[weather]:
            mask[action] = not last_chance or update_rule(rule_met, compound, new)
    return mask


def lap_time_table(params: Params) -> np.ndarray:
    """Expected lap times, indexed [status, weather, compound, tyre_age - 1, laps_after]."""
    laps = params["total_laps"]
    table = np.empty((len(TrackStatus), len(Weather), len(Compound), laps, laps))
    for status, weather, compound, age, after in np.ndindex(table.shape):
        table[status, weather, compound, age, after] = compute_lap_time(
            Compound(compound), age + 1, after, Weather(weather), TrackStatus(status), params
        )
    return table
