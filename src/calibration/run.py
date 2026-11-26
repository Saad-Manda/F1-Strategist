"""Calibrate every circuit, check it (K1-K9), and write it only if every circuit passes.

Run from the repo root:  python -m src.calibration.run [--dry-run] [--out DIR]
Writes data/processed/<circuit>/calibration.json and scenarios.parquet.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from src.calibration.build import build_calibrations
from src.calibration.checks.validate import calibration_failures
from src.calibration.conditions.table import race_conditions
from src.calibration.conditions.traces import build_trace
from src.calibration.fitting_races import load_fitting_races
from src.common.config import ConfigSection, load_config
from src.common.errors import CalibrationError
from src.common.schema import write_calibration
from src.data.spec.races import Race, load_races
from src.data.storage.frozen import load_race

# Real races to replay: a trace needs only weather and status. The holdout may be replayed, never fitted (D25).
TRACE_ROLES = ("fit", "conditions_only", "holdout")


def main(arguments: list[str] | None = None) -> int:
    """Calibrate, report, and return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="check, but write nothing")
    parser.add_argument("--out", help="write here instead of calibration.paths.processed")
    options = parser.parse_args(arguments)

    config = load_config("configs/defaults.yaml")["calibration"]
    interim = Path(load_config("configs/ingest.yaml")["paths"]["interim"])
    total_laps = {c["name"]: c["total_laps"] for c in load_config("configs/circuits.yaml")["circuits"]}
    races = load_races()

    calibrations = build_calibrations(load_fitting_races(races, interim, config), total_laps, config)
    traces = {c: circuit_traces(c, laps, races, interim, config) for c, laps in total_laps.items()}
    failures = {c: calibration_failures(p, config) for c, p in calibrations.items()}

    for circuit, params in calibrations.items():
        print(summary(params, traces[circuit][1]))
        for failure in failures[circuit]:
            print(f"  FAILED {failure}")
    failed = [c for c, found in failures.items() if found]
    if failed:
        print(f"Nothing written: {', '.join(failed)} failed.")
        return 1
    if options.dry_run:
        print("Every circuit passes; nothing written (--dry-run).")
        return 0
    out = Path(options.out or config["paths"]["processed"])
    for circuit, params in calibrations.items():
        write_calibration(params, out / circuit / "calibration.json")
        traces[circuit][0].to_parquet(out / circuit / "scenarios.parquet", index=False)
    print(f"Written to {out}/ for {len(calibrations)} circuits.")
    return 0


def circuit_traces(
    circuit: str, total_laps: int, races: list[Race], interim: Path, config: ConfigSection
) -> tuple[pd.DataFrame, list[str]]:
    """Every replayable race of `circuit`, and why the others were left out."""
    kept, rejected = [], []
    for race in races:
        if race.circuit != circuit or race.role not in TRACE_ROLES:
            continue
        conditions = race_conditions(race, load_race(race.id, interim), config["conditions"])
        try:
            kept.append(build_trace(conditions, total_laps, config["conditions"]["max_padded_laps"]))
        except CalibrationError as error:
            rejected.append(str(error))
    if not kept:
        raise CalibrationError(f"{circuit}: no race can be replayed")
    return pd.concat(kept, ignore_index=True), rejected


def summary(params: dict[str, Any], rejected: list[str]) -> str:
    """Where the numbers of one circuit come from (D10), and its best dry plan."""
    sources = params["provenance"]
    count = Counter(sources.values())
    best = params["diagnostics"]["landscape"]["best"]
    stints = " / ".join(best["compounds"])
    lines = [
        f"{params['circuit']}: {count['fitted']} fitted, {count['pooled']} pooled, {count['prior']} prior",
        f"  fitted: {', '.join(k for k, v in sources.items() if v == 'fitted')}",
        f"  pooled: {', '.join(k for k, v in sources.items() if v == 'pooled')}",
        f"  best dry plan: {stints}, stop on lap {', '.join(map(str, best['stops']))}",
    ]
    lines += [f"  trace left out: {reason}" for reason in rejected]
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
