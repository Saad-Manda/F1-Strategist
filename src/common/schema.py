"""calibration.json, schema v2: the exact fields, their types, and reading and writing the file."""

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from src.common.errors import CalibrationError

SCHEMA_VERSION = 2
COMPOUNDS = ("SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET")
DRY_COMPOUNDS = COMPOUNDS[:3]
WEATHERS = ("DRY", "DAMP", "WET")
STATUSES = ("GREEN", "SC", "VSC")
PROVENANCE = ("fitted", "pooled", "prior")

# Fields that name the circuit rather than measure it; they carry no provenance.
IDENTITY = ("schema_version", "circuit", "total_laps", "base_pace_reference_compound")


def _each(keys: tuple[str, ...], inner: Any) -> dict[str, Any]:
    return dict.fromkeys(keys, inner)


TYRE = _each(("base_deg", "cliff_severity", "cliff_cap", "warmup_penalty"), float) | {"cliff_age": int}

FIELDS: dict[str, Any] = {
    "schema_version": int,
    "circuit": str,
    "total_laps": int,
    "base_pace": float,
    "base_pace_reference_compound": str,
    "noise_std": float,
    "flag_noise_std": float,
    "pit_loss": float,
    "pit_loss_sc_multiplier": float,
    "pit_loss_vsc_multiplier": float,
    "warmup_second_lap_share": float,
    "fuel": {"consumption_kg_per_lap": float, "sensitivity_s_per_kg": float},
    "compound_pace_offset": _each(COMPOUNDS, float),
    "compounds": _each(COMPOUNDS, TYRE),
    "weather_compound_penalty": _each(WEATHERS, _each(COMPOUNDS, float)),
    "safety_car": {"lap_time": float},
    "virtual_safety_car": {"lap_time": float},
    "status_start": _each(STATUSES, float),
    "status_transition": _each(STATUSES, _each(STATUSES, float)),
    "weather_start": _each(WEATHERS, float),
    "weather_transition": _each(WEATHERS, _each(WEATHERS, float)),
    "provenance": dict,
    "diagnostics": dict,
}


def schema_problems(params: Any) -> list[str]:
    """Every missing, unknown, mistyped or non-finite field. Empty when the file is well formed."""
    problems = _compare(params, FIELDS, "")
    if not problems:
        if params["schema_version"] != SCHEMA_VERSION:
            problems.append(f"schema_version is {params['schema_version']}, expected {SCHEMA_VERSION}")
        bad = {k: v for k, v in params["provenance"].items() if v not in PROVENANCE}
        if bad:
            problems.append(f"provenance must be one of {PROVENANCE}: {bad}")
    return problems


def calibrated_fields(spec: dict[str, Any] = FIELDS, prefix: str = "") -> list[str]:
    """Dotted paths of every calibrated number, such as `compounds.SOFT.base_deg`."""
    paths = []
    for key, inner in spec.items():
        if prefix == "" and (key in IDENTITY or inner is dict):
            continue
        path = f"{prefix}{key}"
        paths += calibrated_fields(inner, path + ".") if isinstance(inner, dict) else [path]
    return paths


def read_calibration(path: str | Path) -> dict[str, Any]:
    """Load a calibration file, refusing one that does not match the schema."""
    try:
        params = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CalibrationError(f"{path}: no calibration file") from error
    problems = schema_problems(params)
    if problems:
        raise CalibrationError(f"{path}: " + "; ".join(problems))
    return params


def write_calibration(params: dict[str, Any], path: str | Path) -> None:
    """Write a calibration file; a malformed one is never written."""
    problems = schema_problems(params)
    if problems:
        raise CalibrationError(f"{path}: " + "; ".join(problems))
    text = json.dumps(params, indent=2, allow_nan=False, default=_plain)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text + "\n", encoding="utf-8")


def _compare(value: Any, spec: Any, path: str) -> list[str]:
    where = path or "calibration"
    if isinstance(spec, dict):
        if not isinstance(value, dict):
            return [f"{where} must be a mapping"]
        problems = [f"{path}{k} is missing" for k in spec if k not in value]
        problems += [f"{path}{k} is unknown" for k in value if k not in spec]
        for key in spec.keys() & value.keys():
            problems += _compare(value[key], spec[key], f"{path}{key}.")
        return problems
    where = path.rstrip(".")
    if spec is float:
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
        if ok and not math.isfinite(value):
            return [f"{where} is not finite"]
    else:
        ok = isinstance(value, spec) and not isinstance(value, bool)
    return [] if ok else [f"{where} must be {spec.__name__}, got {type(value).__name__}"]


def _plain(value: Any) -> Any:
    """numpy values, as JSON can hold them."""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"cannot write {type(value).__name__} to a calibration file")
