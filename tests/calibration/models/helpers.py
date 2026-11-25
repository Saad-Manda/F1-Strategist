"""Synthetic clean laps with known tyre parameters."""

import numpy as np
import pandas as pd

OFFSET = {"SOFT": -0.4, "MEDIUM": 0.0, "HARD": 0.3}
WEAR = {"SOFT": 0.08, "MEDIUM": 0.05, "HARD": 0.03}
PLANS = [
    (("SOFT", 12), ("HARD", 28)),
    (("MEDIUM", 18), ("HARD", 22)),
    (("MEDIUM", 22), ("SOFT", 18)),
    (("HARD", 25), ("MEDIUM", 15)),
    (("SOFT", 10), ("MEDIUM", 14), ("HARD", 16)),
]
TRUE_PACE = 90.0


def make_race(race: str, circuit: str, scale: float, trend: float, noise: float, rng) -> pd.DataFrame:
    """Ten cars on five plans; every car has its own pace, every race its own trend."""
    rows = []
    for number in range(10):
        car = f"{race} {number}"
        car_pace = TRUE_PACE + 0.3 * (number - 4.5)
        lap = 0
        for stint, (compound, length) in enumerate(PLANS[number % len(PLANS)]):
            for age in range(1, length + 1):
                lap += 1
                rows.append(
                    {
                        "race": race,
                        "circuit": circuit,
                        "car": car,
                        "stint": f"{car} {stint}",
                        "lap": float(lap),
                        "compound": compound,
                        "age": float(age),
                        "pace": car_pace
                        + trend * lap
                        + OFFSET[compound]
                        + scale * WEAR[compound] * age
                        + noise * rng.standard_normal(),
                    }
                )
    return pd.DataFrame(rows)


def make_laps(scales: dict[str, float], noise: float = 0.0, trend: float = -0.04) -> pd.DataFrame:
    """Three races per circuit, with different trends."""
    rng = np.random.default_rng(7)
    races = [
        make_race(f"{year}_{circuit}", circuit, scale, trend * (i + 1) / 2, noise, rng)
        for circuit, scale in scales.items()
        for i, year in enumerate((2022, 2023, 2024))
    ]
    return pd.concat(races, ignore_index=True)
