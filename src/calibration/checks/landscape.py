"""Every dry 1-, 2- and 3-stop plan of a green race, priced with the race model (C2)."""

import copy
import itertools
from dataclasses import dataclass
from typing import Any

import numpy as np

from src.common.config import ConfigSection
from src.env.dynamics import (
    DRY_COMPOUNDS,
    Compound,
    TrackStatus,
    Weather,
    compute_lap_time,
    compute_pit_loss,
)

DRY = sorted(DRY_COMPOUNDS)


@dataclass(frozen=True)
class Plan:
    """Tyres in the order fitted, and the laps on which the car pits (on the old tyre, C1)."""

    compounds: tuple[Compound, ...]
    stops: tuple[int, ...]


class Prices:
    """Race time of dry plans under green, from one table of stint times."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.laps = params["total_laps"]
        self.pit_loss = compute_pit_loss(TrackStatus.GREEN, params)
        # stint[compound, first, last]: laps first..last on a new tyre, laps numbered from 1.
        self.stint = np.full((len(Compound), self.laps + 1, self.laps + 1), np.nan)
        for compound in DRY:
            for first in range(1, self.laps + 1):
                times = [
                    compute_lap_time(
                        compound, lap - first + 1, self.laps - lap, Weather.DRY, TrackStatus.GREEN, params
                    )
                    for lap in range(first, self.laps + 1)
                ]
                self.stint[compound, first, first:] = np.cumsum(times)

    def times(self, compounds: tuple[Compound, ...], stops: np.ndarray) -> np.ndarray:
        """Race time for each row of `stops`, one stop lap per column, in order."""
        rows = len(stops)
        edges = np.column_stack([np.zeros(rows, int), stops, np.full(rows, self.laps)])
        total = self.pit_loss * (len(compounds) - 1)
        for i, compound in enumerate(compounds):
            total = total + self.stint[compound, edges[:, i] + 1, edges[:, i + 1]]
        return total

    def time(self, plan: Plan) -> float:
        return float(self.times(plan.compounds, np.array([plan.stops], int).reshape(1, -1))[0])


def stop_laps(laps: int, stops: int, step: int = 1) -> np.ndarray:
    """Every choice of stop laps, on every `step`-th lap. No stop on the final lap."""
    chosen = list(itertools.combinations(range(1, laps, step), stops))
    return np.array(chosen, int).reshape(len(chosen), stops)


def sequences(stops: int) -> list[tuple[Compound, ...]]:
    """Tyre orders that meet the two-compound rule."""
    return [c for c in itertools.product(DRY, repeat=stops + 1) if len(set(c)) > 1]


def landscape(params: dict[str, Any], config: ConfigSection) -> dict[str, Any]:
    """The best plans, and how much timing and tyre choice matter around them."""
    prices = Prices(params)
    by_stops = _best_by_stops(prices, config)
    best, best_time = min(by_stops.values(), key=lambda found: found[1])
    one_stop = {}
    for compounds in sequences(1):
        pair = "-".join(sorted(c.name for c in set(compounds)))
        fastest = float(prices.times(compounds, stop_laps(prices.laps, 1)).min())
        one_stop[pair] = min(one_stop.get(pair, np.inf), fastest)
    shift_cost, window = _timing(prices, best, best_time, config)
    flat = copy.deepcopy(params)
    for tyre in flat["compounds"].values():
        tyre["cliff_severity"] = 0.0
    without_cliff = min(t for _, t in _best_by_stops(Prices(flat), config).values())
    return {
        "best": {"compounds": [c.name for c in best.compounds], "stops": list(best.stops), "time": best_time},
        "best_by_stops": {str(n): t - best_time for n, (_, t) in by_stops.items()},
        "one_stop_pairs": {p: t - by_stops[1][1] for p, t in one_stop.items()},
        "stop_shift_cost": shift_cost,
        "window_laps": window,
        "no_stop_margin": min(prices.time(Plan((c,), ())) for c in DRY) - best_time,
        "cliff_value": best_time - without_cliff,
    }


def _best_by_stops(prices: Prices, config: ConfigSection) -> dict[int, tuple[Plan, float]]:
    best = {}
    for stops, step in ((1, 1), (2, 1), (3, config["three_stop_grid_laps"])):
        laps = stop_laps(prices.laps, stops, step)
        found = (np.inf, None)
        for compounds in sequences(stops):
            times = prices.times(compounds, laps)
            i = int(np.argmin(times))
            if times[i] < found[0]:
                found = (float(times[i]), Plan(compounds, tuple(int(x) for x in laps[i])))
        best[stops] = (found[1], found[0])
    return best


def _timing(prices: Prices, best: Plan, best_time: float, config: ConfigSection) -> tuple[float, int]:
    """Cheapest move of one stop by `stop_shift_laps`, and the most laps one stop can sit on within `window_s`."""
    shift = config["stop_shift_laps"]
    costs, window = [], 0
    for i, stop in enumerate(best.stops):
        low = best.stops[i - 1] + 1 if i else 1
        high = best.stops[i + 1] - 1 if i + 1 < len(best.stops) else prices.laps - 1
        moved = {}
        for lap in range(low, high + 1):
            plan = Plan(best.compounds, best.stops[:i] + (lap,) + best.stops[i + 1 :])
            moved[lap] = prices.time(plan) - best_time
        costs += [moved[lap] for lap in (stop - shift, stop + shift) if lap in moved]
        window = max(window, sum(cost <= config["window_s"] for cost in moved.values()))
    return min(costs, default=np.inf), window
