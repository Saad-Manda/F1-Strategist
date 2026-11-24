"""Small synthetic races for the data tests."""

import numpy as np
import pandas as pd

from src.data.cleaning.assemble import build_frames
from src.data.spec.frames import RaceFrames


def make_laps(cars: int, laps: int) -> pd.DataFrame:
    """Every car drives 90 s laps on HARD, starting at time 0."""
    rows = [
        {
            "driver": f"D{car:02d}",
            "driver_number": car,
            "lap": lap,
            "lap_time_s": 90.0,
            "lap_start_s": 90.0 * (lap - 1),
            "lap_end_s": 90.0 * lap,
            "sector1_s": 30.0,
            "sector2_s": 30.0,
            "sector3_s": 30.0,
            "stint": 1,
            "compound": "HARD",
            "tyre_age": lap,
            "label": "raw",
            "is_in_lap": False,
            "is_out_lap": False,
        }
        for car in range(1, cars + 1)
        for lap in range(1, laps + 1)
    ]
    return pd.DataFrame(rows)


def make_weather() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time_s": [0.0, 60.0],
            "air_temp_c": [20.0, 20.5],
            "track_temp_c": [30.0, np.nan],
            "humidity_pct": [50.0, 51.0],
            "wind_speed_ms": [1.0, 1.5],
            "rainfall": [False, True],
        }
    )


def make_status(*changes: tuple[float, str]) -> pd.DataFrame:
    return pd.DataFrame(changes, columns=["time_s", "code"])


def make_frames(cars: int = 20, laps: int = 5, **lap_columns) -> RaceFrames:
    """A complete race; keyword arguments overwrite lap columns."""
    return build_frames(
        laps=make_laps(cars, laps).assign(**lap_columns),
        weather=make_weather(),
        track_status=make_status((0.0, "1"), (100.0, "4"), (300.0, "1")),
        race_laps=laps,
        sector_sum_tolerance_s=0.01,
    )
