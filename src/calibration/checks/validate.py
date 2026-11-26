"""The checks K1-K9 a calibration must pass before anything trains on it. All failures are reported at once."""

from math import ceil
from typing import Any

import numpy as np

from src.calibration.checks.landscape import landscape
from src.common.config import ConfigSection
from src.common.errors import CalibrationError
from src.common.schema import (
    DRY_COMPOUNDS,
    STATUSES,
    WEATHERS,
    calibrated_fields,
    schema_problems,
)
from src.env.dynamics import Compound, tyre_degradation

Params = dict[str, Any]


def validate(params: Params, config: ConfigSection) -> None:
    """Raise one error naming every failed check."""
    failures = calibration_failures(params, config)
    if failures:
        raise CalibrationError(f"calibration fails {len(failures)} check(s):\n  " + "\n  ".join(failures))


def calibration_failures(params: Params, config: ConfigSection) -> list[str]:
    """Each failure as 'K<n>: what is wrong'. Without a valid schema (K1) nothing else is checked."""
    problems = schema_problems(params)
    if problems:
        return [f"K1: {p}" for p in problems]
    checks = {
        "K2": _ordering,
        "K3": _ranges,
        "K4": _cliffs,
        "K5": _chains,
        "K6": _timing,
        "K7": _compounds,
        "K8": _provenance,
        "K9": _noise,
    }
    rules = config["checks"]
    found = landscape(params, rules["landscape"])
    return [
        f"{name}: {failure}"
        for name, check in checks.items()
        for failure in check(params, rules, found)
    ]


def _ordering(params: Params, rules: ConfigSection, _: dict) -> list[str]:
    """SOFT is fastest new, wears most and falls off first; HARD the reverse."""
    rules = rules["ordering"]
    offset = params["compound_pace_offset"]
    tyres = params["compounds"]
    failures = []
    if params["base_pace_reference_compound"] != "MEDIUM" or offset["MEDIUM"] != 0:
        failures.append("pace is not measured from MEDIUM")
    for faster, slower in zip(DRY_COMPOUNDS, DRY_COMPOUNDS[1:]):
        if offset[slower] - offset[faster] < rules["offset_gap_s"]:
            failures.append(f"{faster} is not faster than {slower} by {rules['offset_gap_s']} s")
        if tyres[faster]["base_deg"] < rules["wear_ratio"] * tyres[slower]["base_deg"]:
            failures.append(f"{faster} does not wear {rules['wear_ratio']}x faster than {slower}")
        if tyres[slower]["cliff_age"] - tyres[faster]["cliff_age"] < rules["cliff_gap_laps"]:
            failures.append(f"{faster} does not reach its cliff before {slower}")
    return failures


def _ranges(params: Params, rules: ConfigSection, _: dict) -> list[str]:
    rules = rules["ranges"]
    pace = params["base_pace"]
    checked = [
        ("pit_loss", params["pit_loss"], "pit_loss"),
        ("base_pace", pace, "base_pace"),
        ("pit_loss_sc_multiplier", params["pit_loss_sc_multiplier"], "pit_loss_multiplier"),
        ("pit_loss_vsc_multiplier", params["pit_loss_vsc_multiplier"], "pit_loss_multiplier"),
        ("SC lap / base_pace", params["safety_car"]["lap_time"] / pace, "flag_lap_share"),
        ("VSC lap / base_pace", params["virtual_safety_car"]["lap_time"] / pace, "flag_lap_share"),
    ]
    checked += [(f"{c} base_deg", t["base_deg"], "base_deg") for c, t in params["compounds"].items()]
    failures = []
    for name, value, rule in checked:
        low, high = rules[rule]
        if not low < value < high:
            failures.append(f"{name} {value:.4g} is outside {low}-{high}")
    return failures


def _cliffs(params: Params, rules: ConfigSection, _: dict) -> list[str]:
    """The cliff stays within its cap, and a long stint stays plausible."""
    tolerance = rules["tolerance"]
    rules = rules["cliffs"]
    longest = _diagnostic(params, "tyres.long_stint_age") or {}
    failures = []
    for compound in Compound:
        tyre = params["compounds"][compound.name]
        ages = range(1, params["total_laps"] + 1)
        cliff = [tyre_degradation(compound, a, params) - tyre["base_deg"] * a for a in ages]
        if min(cliff) < 0 or max(cliff) > tyre["cliff_cap"] + tolerance:
            failures.append(f"{compound.name} cliff leaves 0-{tyre['cliff_cap']} s")
    for name in DRY_COMPOUNDS:
        if name not in longest:
            failures.append(f"{name} has no long stint age in the diagnostics")
            continue
        age = ceil(rules["stint_factor"] * longest[name])
        lost = tyre_degradation(Compound[name], age, params)
        if lost >= rules["max_degradation_s"]:
            failures.append(f"{name} loses {lost:.1f} s at age {age}, limit {rules['max_degradation_s']}")
    return failures


def _chains(params: Params, rules: ConfigSection, _: dict) -> list[str]:
    tolerance = rules["tolerance"]
    rules = rules["chains"]
    failures = []
    for name, states in (("status", STATUSES), ("weather", WEATHERS)):
        rows = {"start": params[f"{name}_start"]} | params[f"{name}_transition"]
        for row, chances in rows.items():
            values = np.array([chances[s] for s in states])
            if values.min() < 0 or abs(values.sum() - 1) > tolerance:
                failures.append(f"{name} {row} is not a probability row")
        for now, then in rules["forbidden"][name]:
            if params[f"{name}_transition"][now][then] != 0:
                failures.append(f"{name} steps from {now} to {then}, which never happens")
    expected = _expected_laps(params, "SC")
    low, high = rules["safety_car_laps"]
    if not low <= expected <= high:
        failures.append(f"{expected:.2f} SC laps per race, expected {low}-{high}")
    return failures


def _expected_laps(params: Params, status: str) -> float:
    chain = np.array([[params["status_transition"][a][b] for b in STATUSES] for a in STATUSES])
    share = np.array([params["status_start"][s] for s in STATUSES])
    total = 0.0
    for _ in range(params["total_laps"]):
        total += share[STATUSES.index(status)]
        share = share @ chain
    return total


def _timing(params: Params, rules: ConfigSection, found: dict) -> list[str]:
    """Moving the best stop costs time, but the good stop laps are not a point."""
    rules = rules["timing"]
    failures = []
    if found["stop_shift_cost"] < rules["min_shift_cost_s"]:
        failures.append(f"moving the stop costs only {found['stop_shift_cost']:.2f} s")
    if found["window_laps"] > rules["max_window_laps"]:
        failures.append(f"{found['window_laps']} stop laps within the window, limit {rules['max_window_laps']}")
    return failures


def _compounds(params: Params, rules: ConfigSection, found: dict) -> list[str]:
    """The tyres chosen matter, and more than one choice is sensible. Each choice runs its best number of stops."""
    rules = rules["compounds"]
    gaps = found["tyre_choices"]
    failures = []
    if max(gaps.values()) < rules["min_spread_s"]:
        failures.append(f"all tyre choices are within {max(gaps.values()):.2f} s")
    close = sum(gap <= rules["close_s"] for gap in gaps.values())
    if close < rules["min_close_choices"]:
        failures.append(f"only {close} tyre choice(s) within {rules['close_s']} s of the best")
    return failures


def _provenance(params: Params, rules: ConfigSection, _: dict) -> list[str]:
    """Every number says where it comes from; a fitted one has the data to back it (D10)."""
    provenance = params["provenance"]
    fields = calibrated_fields()
    failures = []
    for field in fields:
        sources = [k for k in provenance if field == k or field.startswith(k + ".")]
        if len(sources) != 1:
            failures.append(f"{field} has {len(sources)} sources")
    for key in provenance:
        if not any(f == key or f.startswith(key + ".") for f in fields):
            failures.append(f"provenance names {key}, which is not a field")
    support = rules["fitted_support"]
    for key, source in provenance.items():
        if source != "fitted":
            continue
        if key not in support:
            failures.append(f"{key} is fitted, but nothing says how much data it needs")
            continue
        seen = _diagnostic(params, support[key]["diagnostic"])
        if seen is None or seen < support[key]["min"]:
            failures.append(f"{key} is fitted on {seen} {support[key]['diagnostic']}, needs {support[key]['min']}")
    return failures


def _noise(params: Params, rules: ConfigSection, _: dict) -> list[str]:
    """`noise_std` is the tyre fit's residual sd (tyres.py); too small means an overfit."""
    if params["noise_std"] <= rules["min_noise_std"]:
        return [f"noise_std {params['noise_std']:.3f} is not above {rules['min_noise_std']}"]
    return []


def _diagnostic(params: Params, path: str) -> Any:
    """A diagnostic by dotted path, or None when it was not recorded."""
    value: Any = params["diagnostics"]
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value
