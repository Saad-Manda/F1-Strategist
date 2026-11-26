"""What a pit stop costs: per circuit under green, and its share of that under SC and VSC (D33)."""

import pandas as pd

from src.calibration.fitting_races import FittingRace
from src.calibration.models.clean_laps import CLEAR_TRACK
from src.calibration.models.fields import Fields
from src.common.config import ConfigSection
from src.common.errors import CalibrationError

MULTIPLIER_FIELDS = {"SC": "pit_loss_sc_multiplier", "VSC": "pit_loss_vsc_multiplier"}


def collect_stops(races: list[FittingRace], config: ConfigSection) -> pd.DataFrame:
    """Every usable stop of the fully dry races."""
    stops = [race_stops(r, config) for r in races if r.race.role == "fit" and r.fully_dry]
    if not stops:
        raise CalibrationError("no dry race to take pit stops from")
    return pd.concat(stops, ignore_index=True)


def race_stops(race: FittingRace, config: ConfigSection) -> pd.DataFrame:
    """Stops of one race and what each cost, compared with cars that stayed out.

    The in-lap and out-lap are compared with the same two laps of the other cars, corrected
    for how fast each car usually is.
    """
    rules = config["pit_stops"]
    laps = race.frames.laps
    end, times, entering, leaving, flags = (
        laps.pivot(index="lap", columns="driver", values=column)
        for column in ("lap_end_s", "lap_time_s", "is_in_lap", "is_out_lap", "track_status")
    )
    entering, leaving = entering.eq(True), leaving.eq(True)
    in_pits = entering | leaving
    status = race.conditions.table["status"]
    usual = times.mask(in_pits)[times.index.map(status) == "GREEN"].median()
    two_laps = end.shift(-1) - end.shift(1) - 2 * usual

    rows = []
    for lap in range(rules["min_lap"], race.frames.race_laps):
        stopped = end.columns[entering.loc[lap] & leaving.loc[lap + 1]]
        if stopped.empty:
            continue
        stayed_out = two_laps.loc[lap][~in_pits.loc[lap : lap + 1].any()].dropna()
        if len(stayed_out) < rules["min_peers"]:
            continue
        for car in stopped:
            clear = (flags.loc[lap : lap + 1, car] == CLEAR_TRACK).all()
            kind = "GREEN" if clear else _first_flag_lap(status, lap)
            loss = two_laps.at[lap, car] - stayed_out.median()
            if kind and pd.notna(loss):
                rows.append((race.race.id, race.race.circuit, car, lap, kind, float(loss)))
    return pd.DataFrame(rows, columns=["race", "circuit", "car", "lap", "kind", "loss"])


def _first_flag_lap(status: pd.Series, lap: int) -> str:
    """SC or VSC when `lap` is the first of the period; later stops meet a bunched field."""
    starts = status[lap - 1] == "GREEN" and status[lap + 1] != "RED"
    return status[lap] if starts and status[lap] in MULTIPLIER_FIELDS else ""


def pit_fields(circuit: str, stops: pd.DataFrame) -> Fields:
    """Pit loss of `circuit`, and the SC and VSC multipliers pooled over circuits."""
    green = stops[stops["kind"] == "GREEN"].groupby("circuit")["loss"]
    if circuit not in green.groups:
        raise CalibrationError(f"{circuit}: no green pit stop")
    typical = green.median()
    values = {"pit_loss": float(typical[circuit])}
    diagnostics = {
        "green_stops": int(green.size()[circuit]),
        "green_quartiles": green.get_group(circuit).quantile([0.25, 0.75]).tolist(),
    }
    for kind, field in MULTIPLIER_FIELDS.items():
        flagged = stops[stops["kind"] == kind]
        share = (flagged["loss"] / flagged["circuit"].map(typical)).dropna()
        if share.empty:
            raise CalibrationError(f"no {kind} pit stop")
        values[field] = float(share.median())
        diagnostics[f"{kind}_stops"] = len(share)
        diagnostics[f"{kind}_races"] = int(flagged.loc[share.index, "race"].nunique())
        diagnostics[f"{kind}_quartiles"] = share.quantile([0.25, 0.75]).tolist()
    provenance = {"pit_loss": "fitted"} | dict.fromkeys(MULTIPLIER_FIELDS.values(), "pooled")
    return Fields(values, provenance, diagnostics)
