"""Tyre parameters of one circuit: the dry fit, plus priors for what the data cannot show."""

from math import ceil
from typing import Any

import pandas as pd

from src.calibration.models.clean_laps import DRY_COMPOUNDS
from src.calibration.models.fields import Fields
from src.calibration.models.tyre_fit import TyrePattern, fit_circuit
from src.common.config import ConfigSection
from src.common.errors import CalibrationError

RAIN_COMPOUNDS = ("INTERMEDIATE", "WET")


def tyre_fields(
    circuit: str, laps: pd.DataFrame, pattern: TyrePattern, config: ConfigSection
) -> Fields:
    """Tyre fields of `circuit`. `laps` may hold other circuits too."""
    laps = laps[laps["circuit"] == circuit]
    if laps.empty:
        raise CalibrationError(f"{circuit}: no clean dry laps")
    try:
        fit = fit_circuit(laps, pattern)
    except CalibrationError as error:
        raise CalibrationError(f"{circuit}: {error}") from error

    rules = config["tyres"]
    wear = {c: fit.wear_scale * pattern.wear[c] for c in DRY_COMPOUNDS}
    wear |= {c: rules["rain_tyre_wear"][c] for c in RAIN_COMPOUNDS}
    by_compound = laps.groupby("compound")
    longest = by_compound["age"].quantile(rules["long_stint_quantile"]).to_dict()

    values = {
        "base_pace": fit.base_pace,
        "noise_std": fit.noise_std,
        # Rain tyre pace is in the weather penalties.
        "compound_pace_offset": pattern.offset | dict.fromkeys(RAIN_COMPOUNDS, 0.0),
        "compounds": {
            c: {
                "base_deg": wear[c],
                "cliff_age": _cliff_age(rules["cliff"][c]["age"], longest.get(c)),
                "cliff_severity": rules["cliff"][c]["severity"],
                "cliff_cap": rules["cliff_cap"],
                "warmup_penalty": config["warmup_defaults"][c],
            }
            for c in wear
        },
    }
    diagnostics = {
        "races": sorted(laps["race"].unique()),
        "clean_laps": len(laps),
        "stints": by_compound["stint"].nunique().to_dict(),
        "long_stint_age": longest,
        "wear_scale": fit.wear_scale,
        "wear_scale_error": fit.wear_scale_error,
        "pattern_error": pattern.standard_error,
    }
    return Fields(values, _provenance(values), diagnostics)


def _cliff_age(prior: int, longest_stint: float | None) -> int:
    """Cars reach `longest_stint` without a visible cliff, so it comes no earlier (D10)."""
    return prior if longest_stint is None else max(prior, ceil(longest_stint))


def _provenance(values: dict[str, Any]) -> dict[str, str]:
    provenance = {"base_pace": "fitted", "noise_std": "fitted"}
    for compound, tyre in values["compounds"].items():
        source = "pooled" if compound in DRY_COMPOUNDS else "prior"
        provenance[f"compound_pace_offset.{compound}"] = source
        for field in tyre:
            provenance[f"compounds.{compound}.{field}"] = source if field == "base_deg" else "prior"
    return provenance
