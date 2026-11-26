"""Each check K1-K9 is broken on its own, and must be the only one to fail."""

import math

import pytest

from src.calibration.checks import validate as validate_module

from src.calibration.checks.validate import calibration_failures, validate
from src.common.errors import CalibrationError
from tests.calibration.checks.helpers import check_config, valid_calibration


def _keys(path: str) -> list[str]:
    """Keys along a dotted path. A provenance key is itself dotted."""
    if path.startswith("provenance."):
        return ["provenance", path.removeprefix("provenance.")]
    return path.split(".")


def _set(tree: dict, path: str, value) -> None:
    *parents, last = _keys(path)
    for key in parents:
        tree = tree[key]
    if isinstance(value, tuple) and value[0] == "+":
        value = tree[last] + value[1]
    if value is DROP:
        del tree[last]
    else:
        tree[last] = value


DROP = object()


def _move(chain: str, now: str, then: str, share: float):
    """Move `share` of row `now` from staying to `then`."""
    return [(f"{chain}.{now}.{then}", ("+", share)), (f"{chain}.{now}.{now}", ("+", -share))]


def failed(changes=(), config_changes=()) -> set[str]:
    params, config = valid_calibration(), check_config()
    for tree, edits in ((params, changes), (config, config_changes)):
        for path, value in edits:
            _set(tree, path, value)
    return {f.split(":")[0] for f in calibration_failures(params, config)}


def test_valid_calibration_passes():
    # Fails if a check rejects a sound calibration, which would make every case below meaningless.
    assert failed() == set()


@pytest.mark.parametrize(
    "changes, check",
    [
        # K1: fails if a missing, unknown, mistyped or non-finite field is accepted
        ([("pit_loss", DROP)], "K1"),
        ([("pit_window", 3)], "K1"),
        ([("compounds.WET", DROP)], "K1"),
        ([("weather_compound_penalty.DAMP.WET", DROP)], "K1"),
        ([("compounds.SOFT.base_deg", math.nan)], "K1"),
        ([("pit_loss", math.inf)], "K1"),
        ([("compounds.SOFT.cliff_age", 15.5)], "K1"),
        ([("pit_loss", True)], "K1"),
        ([("status_start", [0.8, 0.17, 0.03])], "K1"),
        ([("schema_version", 1)], "K1"),
        ([("provenance.pit_loss", "guessed")], "K1"),
        # K2: fails if the dry tyres may be out of order
        ([("compound_pace_offset.SOFT", -0.02)], "K2"),
        ([("compound_pace_offset.MEDIUM", 0.1)], "K2"),
        ([("base_pace_reference_compound", "SOFT")], "K2"),
        ([("compounds.HARD.base_deg", 0.059)], "K2"),
        ([("compounds.HARD.cliff_age", 24)], "K2"),
        # K3: fails if a number outside what is plausible is accepted
        ([("pit_loss", 31.0)], "K3"),
        ([("base_pace", 59.0)], "K3"),
        ([("safety_car.lap_time", 80.0)], "K3"),
        ([("virtual_safety_car.lap_time", 220.0)], "K3"),
        ([("pit_loss_sc_multiplier", 1.1)], "K3"),
        ([("pit_loss_vsc_multiplier", 0.0)], "K3"),
        ([("compounds.INTERMEDIATE.base_deg", 0.3)], "K3"),
        ([("compounds.WET.base_deg", 0.002)], "K3"),
        # K4: fails if the cliff can go negative or past its cap, or a long stint is implausible
        ([("compounds.WET.cliff_severity", -0.1)], "K4"),
        ([("compounds.INTERMEDIATE.cliff_cap", -1.0)], "K4"),
        ([("diagnostics.tyres.long_stint_age.SOFT", 35)], "K4"),
        ([("diagnostics.tyres.long_stint_age.MEDIUM", DROP)], "K4"),
        # K5: fails if a chain is not a chain, a step that never happens is allowed, or SC laps are implausible
        ([("status_transition.SC.GREEN", ("+", 0.1))], "K5"),
        (_move("weather_transition", "DAMP", "DRY", 0.99), "K5"),
        ([("status_start.GREEN", 0.7)], "K5"),
        (_move("weather_transition", "DRY", "WET", 0.001), "K5"),
        (_move("status_transition", "GREEN", "SC", 0.2), "K5"),
        (
            [("status_start.SC", 0.0), ("status_start.GREEN", 0.97)]
            + _move("status_transition", "GREEN", "SC", -0.01)
            + _move("status_transition", "VSC", "SC", -0.04),
            "K5",
        ),
        # K8: fails if a number has no source, two sources, or is called fitted without the data
        ([("provenance.compounds.SOFT.base_deg", DROP)], "K8"),
        ([("provenance.compounds", "prior")], "K8"),
        ([("provenance.pit_window", "prior")], "K8"),
        ([("provenance.flag_noise_std", "fitted")], "K8"),
        ([("diagnostics.tyres.clean_laps", 100)], "K8"),
        ([("diagnostics.pit_stops", DROP)], "K8"),
        # K9: fails if a noise too small to be real is accepted
        ([("noise_std", 0.2)], "K9"),
    ],
)
def test_each_check_catches_its_breakage(changes, check):
    assert failed(changes) == {check}


@pytest.mark.parametrize(
    "config_changes, check",
    [
        # fails if K6 does not read the landscape
        ([("checks.timing.min_shift_cost_s", 20.0)], "K6"),
        ([("checks.timing.max_window_laps", 1)], "K6"),
        # fails if K7 does not read the landscape
        ([("checks.compounds.min_spread_s", 20.0)], "K7"),
        ([("checks.compounds.close_s", 0.5)], "K7"),
    ],
)
def test_landscape_checks(config_changes, check):
    assert failed(config_changes=config_changes) == {check}


def test_flat_tyres_fail_timing():
    # Fails if a race where the stop lap barely matters passes K6 (K2 and K7 fail too: the tyres are alike).
    changes = []
    for compound, wear in (("SOFT", 0.0045), ("MEDIUM", 0.004), ("HARD", 0.0035)):
        changes += [(f"compounds.{compound}.cliff_severity", 0.0), (f"compounds.{compound}.base_deg", wear)]
        changes += [(f"compound_pace_offset.{compound}", 0.0)]
    assert "K6" in failed(changes)


def test_a_source_may_cover_a_whole_table():
    # Fails if one provenance entry for a whole tyre is refused.
    params, config = valid_calibration(), check_config()
    for field in list(params["provenance"]):
        if field.startswith("compounds.SOFT."):
            del params["provenance"][field]
    params["provenance"]["compounds.SOFT"] = "prior"
    assert calibration_failures(params, config) == []


def test_all_failures_are_reported_at_once():
    # Fails if the first failure hides the others.
    params, config = valid_calibration(), check_config()
    params["pit_loss"] = 40.0
    params["noise_std"] = 0.1
    with pytest.raises(CalibrationError, match="2 check") as error:
        validate(params, config)
    assert "K3: pit_loss" in str(error.value) and "K9: noise_std" in str(error.value)
    validate(valid_calibration(), config)


def test_a_malformed_file_stops_at_k1():
    # Fails if the other checks run on a file they cannot read, and crash instead of reporting.
    params, config = valid_calibration(), check_config()
    del params["compounds"]
    assert {f.split(":")[0] for f in calibration_failures(params, config)} == {"K1"}


def test_a_cliff_past_its_cap_is_caught(monkeypatch):
    # Fails if K4 trusts the race model to cap the cliff, instead of checking it.
    def uncapped(compound, age, params):
        tyre = params["compounds"][compound.name]
        return tyre["base_deg"] * age + tyre["cliff_severity"] * max(0, age - tyre["cliff_age"]) ** 2

    monkeypatch.setattr(validate_module, "tyre_degradation", uncapped)
    failures = calibration_failures(valid_calibration(), check_config())
    assert any(f.startswith("K4: SOFT cliff leaves") for f in failures)
