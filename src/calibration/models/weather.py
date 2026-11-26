"""Rain: how often it comes and goes, and how much slower it makes every car (D35)."""

import pandas as pd

from src.calibration.fitting_races import FittingRace
from src.calibration.models.fields import Fields
from src.calibration.models.chains import count_steps, shares
from src.common.config import ConfigSection
from src.common.errors import CalibrationError

WEATHERS = ("DRY", "DAMP", "WET")
DRY_COMPOUNDS = ("SOFT", "MEDIUM", "HARD")
CLEAR_TRACK = "1"


def weather_fields(
    races: list[FittingRace], base_pace: float, config: ConfigSection
) -> Fields:
    """Weather chain and penalties of a circuit with this `base_pace`.

    The chain and the slowdown of rain are pooled over circuits. Penalties between tyres stay priors.
    """
    labelled = [r for r in races if not r.conditions.weather_rejection]
    start, counts = count_steps([r.conditions.table["regime"] for r in labelled], WEATHERS)
    priors = config["weather_penalty_defaults"]
    penalty = {w: {c: float(priors[w][c]) for c in priors[w]} for w in WEATHERS}
    provenance = {"weather_start": "pooled", "weather_transition": "pooled"}
    slowdown, support = {}, {}
    for weather in WEATHERS:
        best = _rain_tyre(weather, priors) if weather != "DRY" else ""
        if best:
            slowdown[weather], support[weather] = rain_slowdown(labelled, weather, best, config)
            for compound in penalty[weather]:
                penalty[weather][compound] += slowdown[weather] * base_pace
        # The rain tyre's penalty is all measured; the others add a prior gap to it.
        for compound in penalty[weather]:
            source = "pooled" if compound == best else "prior"
            provenance[f"weather_compound_penalty.{weather}.{compound}"] = source
    return Fields(
        values={
            "weather_start": shares(start),
            "weather_transition": {w: shares(counts.loc[w]) for w in WEATHERS},
            "weather_compound_penalty": penalty,
        },
        provenance=provenance,
        diagnostics={
            "races": len(labelled),
            "rejected": sorted(r.race.id for r in races if r.conditions.weather_rejection),
            "start_counts": start.to_dict(),
            "transition_counts": counts.T.to_dict(),
            "slowdown": slowdown,
            "slowdown_races": support,
        },
    )


def rain_slowdown(
    races: list[FittingRace], weather: str, compound: str, config: ConfigSection
) -> tuple[float, int]:
    """Share by which `compound` in `weather` is slower than the same car on dry slicks.

    Each race gives the median over cars that ran both; the result is the median over races.
    """
    found = [r for r in (_race_slowdown(r, weather, compound, config) for r in races) if r]
    if not found:
        raise CalibrationError(f"no race with {compound} running in {weather} and dry laps")
    return float(pd.Series(found).median()), len(found)


def _race_slowdown(
    race: FittingRace, weather: str, compound: str, config: ConfigSection
) -> float | None:
    laps = race.frames.laps
    table = race.conditions.table
    fuel = config["fuel"]
    pace = laps["lap_time_s"] - fuel["consumption_kg_per_lap"] * fuel["sensitivity_s_per_kg"] * (
        race.frames.race_laps - laps["lap"]
    )
    usable = (
        laps["is_accurate"]
        & (laps["track_status"] == CLEAR_TRACK)
        & (laps["lap"].map(table["status"]) == "GREEN")
        & (laps["lap"] >= config["weather"]["min_lap"])
    )
    regime = laps["lap"].map(table["regime"])
    on_dry = usable & (regime == "DRY") & laps["compound"].isin(DRY_COMPOUNDS)
    in_rain = usable & (regime == weather) & (laps["compound"] == compound)
    dry = pace[on_dry].groupby(laps["driver"]).median()
    rain = pace[in_rain].groupby(laps["driver"]).median()
    both = dry.index.intersection(rain.index)
    if both.empty:
        return None
    return float((rain[both] / dry[both]).median() - 1)


def _rain_tyre(weather: str, priors: ConfigSection) -> str:
    """The tyre made for this weather: the one without a penalty."""
    best = [c for c in priors[weather] if priors[weather][c] == 0]
    if len(best) != 1:
        raise CalibrationError(f"weather penalties for {weather} need one tyre without a penalty")
    return best[0]
