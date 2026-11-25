"""Fixtures shared by every test."""

import copy
from typing import Any

import pytest

COMPOUNDS = ("SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET")


def _tyre(base_deg: float, cliff_age: int, warmup_penalty: float) -> dict[str, float]:
    return {
        "base_deg": base_deg,
        "cliff_age": cliff_age,
        "cliff_severity": 1.0,
        "cliff_cap": 4.0,
        "warmup_penalty": warmup_penalty,
    }


_TOY_PARAMS: dict[str, Any] = {
    "schema_version": 2,
    "circuit": "toy",
    "total_laps": 8,
    "base_pace": 90.0,
    "base_pace_reference_compound": "MEDIUM",
    "noise_std": 0.5,
    "flag_noise_std": 1.0,
    "pit_loss": 20.0,
    "pit_loss_sc_multiplier": 0.4,
    "pit_loss_vsc_multiplier": 0.6,
    "warmup_second_lap_share": 0.3,
    "fuel": {"consumption_kg_per_lap": 2.0, "sensitivity_s_per_kg": 0.05},
    "compound_pace_offset": dict(zip(COMPOUNDS, (-1.0, 0.0, 1.0, 5.0, 8.0))),
    "compounds": {
        "SOFT": _tyre(0.3, 2, 1.0),
        "MEDIUM": _tyre(0.2, 3, 2.0),
        "HARD": _tyre(0.1, 4, 3.0),
        "INTERMEDIATE": _tyre(0.2, 5, 1.0),
        "WET": _tyre(0.1, 6, 1.0),
    },
    "weather_compound_penalty": {
        "DRY": dict(zip(COMPOUNDS, (0.0, 0.0, 0.0, 4.0, 10.0))),
        "DAMP": dict(zip(COMPOUNDS, (6.0, 6.0, 6.0, 0.0, 2.0))),
        "WET": dict(zip(COMPOUNDS, (16.0, 16.0, 16.0, 4.0, 0.0))),
    },
    "safety_car": {"lap_time": 130.0},
    "virtual_safety_car": {"lap_time": 120.0},
    "status_transition": {
        "GREEN": {"GREEN": 0.9, "SC": 0.06, "VSC": 0.04},
        "SC": {"GREEN": 0.25, "SC": 0.75, "VSC": 0.0},
        "VSC": {"GREEN": 0.5, "SC": 0.0, "VSC": 0.5},
    },
    "weather_transition": {
        "DRY": {"DRY": 0.9, "DAMP": 0.1, "WET": 0.0},
        "DAMP": {"DRY": 0.2, "DAMP": 0.7, "WET": 0.1},
        "WET": {"DRY": 0.0, "DAMP": 0.2, "WET": 0.8},
    },
    "weather_start": {"DRY": 0.8, "DAMP": 0.15, "WET": 0.05},
}


@pytest.fixture
def toy_params() -> dict[str, Any]:
    """An 8-lap circuit with numbers that can be checked by hand (calibration schema v2)."""
    return copy.deepcopy(_TOY_PARAMS)
