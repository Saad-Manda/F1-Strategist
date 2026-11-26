import json

import numpy as np
import pytest

from src.common.errors import CalibrationError
from src.common.schema import (
    COMPOUNDS,
    STATUSES,
    WEATHERS,
    calibrated_fields,
    read_calibration,
    schema_problems,
    write_calibration,
)
from src.env.dynamics import Compound, TrackStatus, Weather
from tests.calibration.checks.helpers import valid_calibration


def test_names_match_the_race_model():
    # Fails if the file and the race model disagree on a name or its order.
    assert COMPOUNDS == tuple(c.name for c in Compound)
    assert WEATHERS == tuple(w.name for w in Weather)
    assert STATUSES == tuple(s.name for s in TrackStatus)


def test_calibrated_fields():
    # Fails if a number is left out of provenance, or a name such as the circuit is asked for one.
    fields = calibrated_fields()
    assert len(fields) == len(set(fields)) == 80
    assert "compounds.SOFT.cliff_age" in fields and "status_transition.SC.GREEN" in fields
    assert not {"circuit", "total_laps", "schema_version", "provenance", "diagnostics"} & set(fields)


def test_toy_params_meet_the_schema(toy_params):
    # Fails if the shared test circuit drifts from the file format.
    toy_params |= {"provenance": {}, "diagnostics": {}}
    assert schema_problems(toy_params) == []


def test_round_trip(tmp_path):
    # Fails if writing and reading change a value, or numpy numbers cannot be written.
    params, expected = valid_calibration(), valid_calibration()
    params["diagnostics"]["tyres"]["clean_laps"] = np.int64(1000)
    params["diagnostics"]["counts"] = np.array([1, 2])
    expected["diagnostics"]["counts"] = [1, 2]
    write_calibration(params, tmp_path / "monza" / "calibration.json")
    assert read_calibration(tmp_path / "monza" / "calibration.json") == expected


def test_a_malformed_calibration_is_never_written(tmp_path):
    # Fails if a broken file reaches disk, where the environment would load it.
    params = valid_calibration()
    params["pit_loss"] = float("nan")
    with pytest.raises(CalibrationError, match="pit_loss is not finite"):
        write_calibration(params, tmp_path / "calibration.json")
    assert not (tmp_path / "calibration.json").exists()


def test_a_malformed_file_is_refused(tmp_path):
    # Fails if a file with an unknown field or a NaN is read as valid.
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps(valid_calibration() | {"pit_window": 3}).replace("22.0", "NaN"))
    with pytest.raises(CalibrationError, match="pit_window is unknown.*pit_loss is not finite"):
        read_calibration(path)
    with pytest.raises(CalibrationError, match="no calibration file"):
        read_calibration(tmp_path / "missing.json")


def test_diagnostics_cannot_hold_nan(tmp_path):
    # Fails if a NaN in the free-form diagnostics is written, which strict JSON readers refuse.
    params = valid_calibration()
    params["diagnostics"]["gap"] = float("nan")
    with pytest.raises(ValueError):
        write_calibration(params, tmp_path / "calibration.json")
