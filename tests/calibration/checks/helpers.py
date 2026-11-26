"""A calibration that passes every check, to break one check at a time."""

import copy
from typing import Any

from src.common.config import ConfigSection, load_config
from src.common.schema import COMPOUNDS, STATUSES, WEATHERS, calibrated_fields

LAPS = 40


def _tyre(base_deg: float, cliff_age: int) -> dict[str, Any]:
    return {
        "base_deg": base_deg,
        "cliff_age": cliff_age,
        "cliff_severity": 0.3,
        "cliff_cap": 4.0,
        "warmup_penalty": 0.0,
    }


def _rows(states: tuple[str, ...], move: dict[tuple[str, str], float]) -> dict:
    """A chain with these steps; the rest of each row stays put."""
    rows = {}
    for now in states:
        row = {then: move.get((now, then), 0.0) for then in states}
        row[now] = 1 - sum(row.values())
        rows[now] = row
    return rows


FITTED = ("base_pace", "noise_std", "pit_loss")

_VALID: dict[str, Any] = {
    "schema_version": 2,
    "circuit": "test",
    "total_laps": LAPS,
    "base_pace": 85.0,
    "base_pace_reference_compound": "MEDIUM",
    "noise_std": 0.4,
    "flag_noise_std": 1.0,
    "pit_loss": 22.0,
    "pit_loss_sc_multiplier": 0.68,
    "pit_loss_vsc_multiplier": 0.62,
    "warmup_second_lap_share": 0.3,
    "fuel": {"consumption_kg_per_lap": 1.9, "sensitivity_s_per_kg": 0.033},
    "compound_pace_offset": dict(zip(COMPOUNDS, (-0.4, 0.0, 0.3, 0.0, 0.0))),
    "compounds": {
        "SOFT": _tyre(0.10, 15),
        "MEDIUM": _tyre(0.06, 24),
        "HARD": _tyre(0.04, 34),
        "INTERMEDIATE": _tyre(0.05, 28),
        "WET": _tyre(0.05, 28),
    },
    "weather_compound_penalty": {
        "DRY": dict(zip(COMPOUNDS, (0.0, 0.0, 0.0, 4.0, 10.0))),
        "DAMP": dict(zip(COMPOUNDS, (15.0, 13.0, 12.0, 9.0, 11.5))),
        "WET": dict(zip(COMPOUNDS, (33.0, 30.0, 28.0, 21.0, 18.0))),
    },
    "safety_car": {"lap_time": 150.0},
    "virtual_safety_car": {"lap_time": 116.0},
    "status_start": {"GREEN": 0.8, "SC": 0.17, "VSC": 0.03},
    "status_transition": _rows(
        STATUSES,
        {("GREEN", "SC"): 0.01, ("GREEN", "VSC"): 0.007, ("SC", "GREEN"): 0.3, ("VSC", "GREEN"): 0.67, ("VSC", "SC"): 0.04},
    ),
    "weather_start": {"DRY": 0.9, "DAMP": 0.09, "WET": 0.01},
    "weather_transition": _rows(
        WEATHERS,
        {("DRY", "DAMP"): 0.001, ("DAMP", "DRY"): 0.024, ("DAMP", "WET"): 0.003, ("WET", "DAMP"): 0.087},
    ),
    "provenance": {f: "fitted" if f in FITTED else "prior" for f in calibrated_fields()},
    "diagnostics": {
        "tyres": {"clean_laps": 1000, "long_stint_age": {"SOFT": 15, "MEDIUM": 25, "HARD": 30}},
        "pit_stops": {"green_stops": 50},
    },
}


def valid_calibration() -> dict[str, Any]:
    return copy.deepcopy(_VALID)


def plain(section: Any) -> Any:
    """A config section as plain, editable dicts and lists."""
    if isinstance(section, ConfigSection):
        return {key: plain(section[key]) for key in section}
    if isinstance(section, tuple):
        return [plain(item) for item in section]
    return section


def check_config() -> dict[str, Any]:
    """The `calibration` config, editable."""
    return plain(load_config("configs/defaults.yaml")["calibration"])
