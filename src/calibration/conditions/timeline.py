"""When the race leader started and finished each lap."""

import pandas as pd

from src.common.errors import CalibrationError


def leader_timeline(laps: pd.DataFrame, race_laps: int) -> pd.DataFrame:
    """Start and end of every lap of the leader, in seconds, indexed by lap.

    The leader of a lap is the first car to finish it (N13). Its lap starts when the previous
    leader finished, so the laps cover the race without gaps or overlaps.
    """
    ends = laps.groupby("lap")["lap_end_s"].min()
    expected = list(range(1, race_laps + 1))
    if ends.index.tolist() != expected or ends.isna().any():
        missing = sorted(set(expected) - set(ends.dropna().index))
        raise CalibrationError(f"no car has an end time for laps {missing}")
    first_start = laps.loc[laps["lap"] == 1, "lap_start_s"].min()
    if pd.isna(first_start):
        raise CalibrationError("no car has a start time for lap 1")
    starts = ends.shift(1, fill_value=first_start)
    if (ends <= starts).any():
        raise CalibrationError(f"leader times go backwards on laps {ends.index[ends <= starts].tolist()}")
    return pd.DataFrame({"start_s": starts, "end_s": ends})
