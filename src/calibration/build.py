"""One calibration (schema v2) per circuit, from the models of WP4-WP6."""

from typing import Any

from src.calibration.checks.landscape import landscape
from src.calibration.fitting_races import FittingRace
from src.calibration.models.clean_laps import collect_clean_laps
from src.calibration.models.pit_stops import collect_stops, pit_fields
from src.calibration.models.track_status import status_fields
from src.calibration.models.tyre_fit import fit_pattern
from src.calibration.models.tyres import tyre_fields
from src.calibration.models.weather import weather_fields
from src.common.config import ConfigSection
from src.common.schema import SCHEMA_VERSION


def build_calibrations(
    races: list[FittingRace], total_laps: dict[str, int], config: ConfigSection
) -> dict[str, dict[str, Any]]:
    """Calibrations of the circuits in `total_laps`. What is pooled is fitted once, over all races."""
    laps, _ = collect_clean_laps(races, config)
    pattern = fit_pattern(laps)
    stops = collect_stops(races, config)
    built = {}
    for circuit, race_laps in total_laps.items():
        tyres = tyre_fields(circuit, laps, pattern, config)
        models = {
            "tyres": tyres,
            "pit_stops": pit_fields(circuit, stops),
            "track_status": status_fields(circuit, races, config),
            "weather": weather_fields(races, tyres.values["base_pace"], config),
        }
        params = {
            "schema_version": SCHEMA_VERSION,
            "circuit": circuit,
            "total_laps": race_laps,
            "base_pace_reference_compound": "MEDIUM",
            "fuel": {k: config["fuel"][k] for k in config["fuel"]},
            "warmup_second_lap_share": config["warmup_second_lap_share"],
            "provenance": {"fuel": "prior", "warmup_second_lap_share": "prior"},
            "diagnostics": {},
        }
        for name, fields in models.items():
            params |= fields.values
            params["provenance"] |= fields.provenance
            params["diagnostics"][name] = fields.diagnostics
        params["diagnostics"]["landscape"] = landscape(params, config["checks"]["landscape"])
        # The numbers first, then where they come from, so the file reads top to bottom.
        built[circuit] = {k: v for k, v in params.items() if k not in ("provenance", "diagnostics")} | {
            "provenance": params["provenance"],
            "diagnostics": params["diagnostics"],
        }
    return built
