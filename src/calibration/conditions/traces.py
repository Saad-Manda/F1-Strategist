"""Real races as replayable traces of exactly the circuit's race distance."""

import pandas as pd

from src.calibration.conditions.table import RaceConditions
from src.common.errors import CalibrationError

TRACE_DTYPES = {
    "race_id": "string",
    "role": "string",
    "lap": "int64",
    "weather_regime": "string",
    "track_status": "string",
    "red_flag": "bool",
    "rainfall": "bool",
    "inter_share": "float64",
    "wet_share": "float64",
    "air_temp_c": "float64",
    "track_temp_c": "float64",
    "padded": "bool",
}


def build_trace(conditions: RaceConditions, total_laps: int, max_padded_laps: int) -> pd.DataFrame:
    """One race cut or padded to `total_laps`, or an error saying why it cannot be used."""
    race, table = conditions.race, conditions.table
    if conditions.weather_rejection:
        raise CalibrationError(f"{race.id}: trace rejected, {conditions.weather_rejection}")
    missing = total_laps - len(table)
    if missing > max_padded_laps:
        raise CalibrationError(
            f"{race.id}: trace rejected, {len(table)} of {total_laps} laps were run"
        )
    laps = pd.RangeIndex(1, total_laps + 1, name="lap")
    trace = table.reindex(laps, method="ffill")
    trace["padded"] = laps > len(table)
    # Padding repeats the last lap's conditions, but never extends a safety car.
    trace["status"] = trace["status"].mask(trace["padded"], "GREEN")
    trace = trace.reset_index()
    trace["red_flag"] = trace["status"] == "RED"
    # Red flags are not modelled (D21); the simulator sees those laps as neutralised.
    trace["status"] = trace["status"].mask(trace["red_flag"], "SC")
    trace = trace.rename(columns={"regime": "weather_regime", "status": "track_status"})
    trace = trace.assign(race_id=race.id, role=race.role)
    return trace[list(TRACE_DTYPES)].astype(TRACE_DTYPES)
