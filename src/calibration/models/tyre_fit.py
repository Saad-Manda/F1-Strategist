"""Dry tyre fit (D32): a compound pattern shared by all circuits, one wear scale per circuit."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.calibration.models.clean_laps import DRY_COMPOUNDS
from src.common.errors import CalibrationError

MAD_TO_SD = 1.4826


@dataclass(frozen=True)
class TyrePattern:
    """Pace offsets relative to MEDIUM (s) and wear (s per lap), over all circuits."""

    offset: dict[str, float]
    wear: dict[str, float]
    standard_error: dict[str, float]


@dataclass(frozen=True)
class CircuitFit:
    """One circuit: how hard it is on tyres relative to the pattern, its pace and its noise."""

    wear_scale: float
    wear_scale_error: float
    base_pace: float
    noise_std: float


def fit_pattern(laps: pd.DataFrame) -> TyrePattern:
    """Offsets and wear per compound, from the laps of all circuits together."""
    columns = {}
    for compound in DRY_COMPOUNDS:
        is_fitted = (laps["compound"] == compound).astype(float)
        if compound != "MEDIUM":
            columns[f"offset {compound}"] = is_fitted
        columns[f"wear {compound}"] = is_fitted * laps["age"]
    coef, error, _ = _least_squares(pd.DataFrame(columns), laps["pace"], laps)
    return TyrePattern(
        offset={c: 0.0 if c == "MEDIUM" else coef[f"offset {c}"] for c in DRY_COMPOUNDS},
        wear={c: coef[f"wear {c}"] for c in DRY_COMPOUNDS},
        standard_error=error,
    )


def fit_circuit(laps: pd.DataFrame, pattern: TyrePattern) -> CircuitFit:
    """The wear scale of one circuit, with the pattern fixed."""
    wear = laps["compound"].map(pattern.wear).astype(float) * laps["age"]
    pace = laps["pace"] - laps["compound"].map(pattern.offset).astype(float)
    coef, error, residual = _least_squares(pd.DataFrame({"scale": wear}), pace, laps)
    scale = coef["scale"]
    if scale <= 0:
        raise CalibrationError(f"tyres get faster with age (wear scale {scale:.3f})")
    car_pace = (pace - scale * wear).groupby(laps["car"]).mean()
    return CircuitFit(
        wear_scale=scale,
        wear_scale_error=error["scale"],
        base_pace=float(car_pace.median()),
        noise_std=float(MAD_TO_SD * np.median(np.abs(residual))),
    )


def _least_squares(
    columns: pd.DataFrame, target: pd.Series, laps: pd.DataFrame
) -> tuple[dict[str, float], dict[str, float], np.ndarray]:
    """Coefficients, standard errors and residuals, with one effect per car and trend per race.

    Laps of a stint are not independent, so the errors treat each stint as one observation.
    """
    trends = pd.get_dummies(laps["race"], dtype=float).mul(laps["lap"], axis=0)
    x = _within_car(pd.concat([columns, trends], axis=1), laps["car"]).to_numpy()
    y = _within_car(target, laps["car"]).to_numpy()
    solution, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    if rank < x.shape[1]:
        raise CalibrationError("the laps do not determine the tyre fit")
    residual = y - x @ solution
    scores = pd.DataFrame(x * residual[:, None]).groupby(laps["stint"].to_numpy()).sum().to_numpy()
    inverse = np.linalg.inv(x.T @ x)
    variance = np.diag(inverse @ (scores.T @ scores) @ inverse)
    coef = dict(zip(columns, solution.tolist()))
    error = dict(zip(columns, np.sqrt(variance).tolist()))
    return coef, error, residual


def _within_car(values: pd.DataFrame | pd.Series, car: pd.Series) -> pd.DataFrame | pd.Series:
    """Remove each car's mean, so cars are only compared with themselves."""
    return values - values.groupby(car).transform("mean")
