import numpy as np
import pandas as pd
import pytest

from src.calibration.models.tyre_fit import TyrePattern, fit_circuit, fit_pattern
from src.common.errors import CalibrationError
from tests.calibration.models.helpers import OFFSET, TRUE_PACE, WEAR, make_laps

TRUE = TyrePattern(offset=OFFSET, wear=WEAR, standard_error={})


def test_exact_data_gives_exact_parameters():
    # Fails if car pace or the race trend leaks into the tyres, or a compound is mislabelled.
    pattern = fit_pattern(make_laps({"a": 1.0, "b": 1.0}))
    assert pattern.offset == pytest.approx(OFFSET, abs=1e-8)
    assert pattern.wear == pytest.approx(WEAR, abs=1e-8)


def test_medium_is_the_reference():
    # Fails if MEDIUM gets an offset of its own.
    assert fit_pattern(make_laps({"a": 1.0}, noise=0.3)).offset["MEDIUM"] == 0.0


def test_circuits_with_different_wear_are_recovered_from_noisy_laps():
    # Fails if a circuit gets the average wear, or the scale multiplies the wrong thing.
    scales = {"smooth": 0.5, "normal": 1.0, "rough": 2.0}
    laps = make_laps(scales, noise=0.4)
    pattern = fit_pattern(laps)
    for circuit, scale in scales.items():
        fit = fit_circuit(laps[laps["circuit"] == circuit], pattern)
        for compound, wear in WEAR.items():
            found = fit.wear_scale * pattern.wear[compound]
            assert found == pytest.approx(scale * wear, abs=0.015), (circuit, compound)


def test_pattern_is_shared_by_circuits_that_lack_a_compound():
    # Fails if a circuit without SOFT laps has no SOFT wear.
    laps = make_laps({"a": 1.0, "b": 1.0})
    no_soft = laps[(laps["circuit"] == "a") | (laps["compound"] != "SOFT")]
    fit = fit_circuit(no_soft[no_soft["circuit"] == "b"], fit_pattern(no_soft))
    assert fit.wear_scale == pytest.approx(1.0, abs=1e-8)


def test_young_tyre_medians_would_be_biased():
    # Fails if the synthetic data stops showing why the old estimator was replaced (E3).
    laps = make_laps({"a": 1.0}, trend=-0.06)
    young = laps[laps["age"] <= 5].groupby("compound")["pace"].median()
    old_estimate = young["HARD"] - young["MEDIUM"]
    assert abs(old_estimate - OFFSET["HARD"]) > 0.2
    assert fit_pattern(laps).offset["HARD"] == pytest.approx(OFFSET["HARD"], abs=1e-8)


def test_base_pace_is_the_typical_car_on_a_fresh_medium():
    # Fails if tyre wear or a compound offset is left in the base pace.
    fit = fit_circuit(make_laps({"a": 2.0}, trend=0.0), TRUE)
    assert fit.base_pace == pytest.approx(TRUE_PACE, abs=1e-8)


def test_one_slow_car_does_not_move_the_base_pace():
    # Fails if the base pace is a mean over cars.
    laps = make_laps({"a": 1.0}, trend=0.0)
    laps.loc[laps["car"] == laps["car"].iloc[-1], "pace"] += 50.0
    assert fit_circuit(laps, TRUE).base_pace == pytest.approx(TRUE_PACE, abs=0.2)


def test_noise_is_measured_and_resists_outliers():
    # Fails if the noise is a default, or a plain standard deviation.
    laps = make_laps({"a": 1.0}, noise=0.4)
    laps.loc[laps.index[::50], "pace"] += 3.0
    assert fit_circuit(laps, TRUE).noise_std == pytest.approx(0.4, abs=0.04)


def test_standard_errors_match_the_spread_of_repeated_fits():
    # Fails if errors ignore that the laps of one stint move together.
    laps = make_laps({"a": 1.0})
    rng = np.random.default_rng(3)
    stints = laps["stint"].unique()
    scales, errors = [], []
    for _ in range(150):
        tilt = dict(zip(stints, rng.normal(0, 0.03, len(stints))))
        noisy = laps.assign(pace=laps["pace"] + laps["stint"].map(tilt) * laps["age"])
        fit = fit_circuit(noisy, TRUE)
        scales.append(fit.wear_scale)
        errors.append(fit.wear_scale_error)
    assert np.mean(errors) == pytest.approx(np.std(scales), rel=0.35)


def test_tyres_that_get_faster_are_refused():
    # Fails if an impossible circuit is calibrated silently.
    with pytest.raises(CalibrationError, match="faster with age"):
        fit_circuit(make_laps({"a": -0.5}), TRUE)


def test_missing_compound_is_refused():
    # Fails if an unidentified offset is filled with a made-up number.
    laps = make_laps({"a": 1.0})
    with pytest.raises(CalibrationError, match="do not determine"):
        fit_pattern(laps[laps["compound"] != "SOFT"])


def test_lap_order_does_not_matter():
    # Fails if the fit depends on the row order or on duplicate row labels.
    laps = make_laps({"a": 1.0, "b": 2.0}, noise=0.3)
    shuffled = laps.sample(frac=1.0, random_state=1)
    shuffled.index = pd.Index([0] * len(shuffled))
    assert fit_pattern(shuffled).wear == pytest.approx(fit_pattern(laps).wear, abs=1e-9)
    assert fit_pattern(laps) == fit_pattern(laps)
