import pytest

from src.calibration.models.tyre_fit import fit_pattern
from src.calibration.models.tyres import tyre_fields
from src.common.errors import CalibrationError
from src.env.dynamics import Compound, TrackStatus, Weather, compute_lap_time
from tests.calibration.models.helpers import OFFSET, TRUE_PACE, WEAR, make_laps

CONFIG = {
    "warmup_defaults": {"SOFT": 1.0, "MEDIUM": 1.5, "HARD": 2.5, "INTERMEDIATE": 0.7, "WET": 0.5},
    "tyres": {
        "long_stint_quantile": 0.95,
        "cliff_cap": 4.0,
        "cliff": {
            "SOFT": {"age": 18, "severity": 0.35},
            "MEDIUM": {"age": 12, "severity": 0.30},
            "HARD": {"age": 38, "severity": 0.25},
            "INTERMEDIATE": {"age": 28, "severity": 0.31},
            "WET": {"age": 29, "severity": 0.32},
        },
        "rain_tyre_wear": {"INTERMEDIATE": 0.05, "WET": 0.06},
    },
}


@pytest.fixture(scope="module")
def laps():
    return make_laps({"a": 1.0, "b": 2.0})


def params(laps, circuit, config=CONFIG):
    return tyre_fields(circuit, laps, fit_pattern(laps[laps["circuit"] == "a"]), config)


def test_wear_is_scaled_and_offsets_are_not(laps):
    # Fails if another circuit's laps are used, or the scale touches the offsets.
    for circuit, scale in (("a", 1.0), ("b", 2.0)):
        values = params(laps, circuit).values
        for compound, wear in WEAR.items():
            assert values["compounds"][compound]["base_deg"] == pytest.approx(scale * wear)
            offset = values["compound_pace_offset"][compound]
            assert offset == pytest.approx(OFFSET[compound], abs=1e-8)


def test_rain_tyres_are_priors(laps):
    # Fails if rain tyres take a dry value, or INTERMEDIATE and WET are swapped.
    values = params(laps, "b").values
    assert values["compound_pace_offset"]["INTERMEDIATE"] == 0.0
    assert values["compound_pace_offset"]["WET"] == 0.0
    assert values["compounds"]["INTERMEDIATE"] == {
        "base_deg": 0.05,
        "cliff_age": 28,
        "cliff_severity": 0.31,
        "cliff_cap": 4.0,
        "warmup_penalty": 0.7,
    }
    assert values["compounds"]["WET"]["base_deg"] == 0.06


def test_cliff_comes_after_the_longest_stints(laps):
    # Fails if a cliff falls where cars were seen to run, or the prior is ignored.
    # Only the MEDIUM prior (12 laps) is shorter than the stints.
    found = {c: t["cliff_age"] for c, t in params(laps, "a").values["compounds"].items()}
    longest = params(laps, "a").diagnostics["long_stint_age"]
    assert 12 < longest["MEDIUM"] <= found["MEDIUM"] < longest["MEDIUM"] + 1
    assert (found["SOFT"], found["HARD"]) == (18, 38)
    assert all(isinstance(age, int) for age in found.values())


def test_compound_never_used_at_the_circuit(laps):
    # Fails if a compound without laps here loses its wear or its cliff prior.
    no_soft = laps[(laps["circuit"] == "a") | (laps["compound"] != "SOFT")]
    result = params(no_soft, "b")
    assert result.values["compounds"]["SOFT"]["base_deg"] == pytest.approx(2 * WEAR["SOFT"])
    assert result.values["compounds"]["SOFT"]["cliff_age"] == 18
    assert "SOFT" not in result.diagnostics["stints"]


def test_every_number_has_a_source(laps):
    # Fails if a field has no provenance, or a prior is called fitted (D10).
    result = params(laps, "a")
    numbers = {"base_pace", "noise_std"}
    numbers |= {f"compound_pace_offset.{c}" for c in result.values["compound_pace_offset"]}
    for compound, tyre in result.values["compounds"].items():
        numbers |= {f"compounds.{compound}.{field}" for field in tyre}
    assert set(result.provenance) == numbers
    by_source = {
        source: {k for k, v in result.provenance.items() if v == source}
        for source in ("fitted", "pooled", "prior")
    }
    assert by_source["fitted"] == {"base_pace", "noise_std"}
    assert by_source["pooled"] == {
        field
        for c in ("SOFT", "MEDIUM", "HARD")
        for field in (f"compound_pace_offset.{c}", f"compounds.{c}.base_deg")
    }
    assert len(by_source["prior"]) == len(numbers) - 8


def test_diagnostics(laps):
    # Fails if the support of the numbers is reported for other circuits.
    diagnostics = params(laps, "b").diagnostics
    assert diagnostics["races"] == ["2022_b", "2023_b", "2024_b"]
    assert diagnostics["clean_laps"] == (laps["circuit"] == "b").sum()
    assert diagnostics["stints"] == {"SOFT": 18, "MEDIUM": 24, "HARD": 24}
    assert diagnostics["wear_scale"] == pytest.approx(2.0)


def test_the_simulator_reproduces_the_laps(toy_params):
    # Fails if the fit and dynamics.py disagree on what a parameter means.
    toy_params.update(params(make_laps({"a": 1.0, "b": 2.0}, trend=0.0), "b").values)
    expected = TRUE_PACE + OFFSET["SOFT"] + 2 * WEAR["SOFT"] * 10
    lap = compute_lap_time(Compound.SOFT, 10, 0, Weather.DRY, TrackStatus.GREEN, toy_params)
    assert lap == pytest.approx(expected)


@pytest.mark.parametrize("circuit, message", [("x", "x: no clean"), ("c", "c: tyres get faster")])
def test_errors_name_the_circuit(circuit, message):
    # Fails if a circuit that cannot be calibrated is skipped or not named.
    laps = make_laps({"a": 1.0, "c": -1.0})
    with pytest.raises(CalibrationError, match=message):
        params(laps, circuit)
