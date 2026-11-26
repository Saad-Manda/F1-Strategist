# Phase 0: Overview

## What Is Phase 0?

Phase 0 is the data foundation of Stratex. It reads real Formula 1 race data and produces, for each circuit, the
parameters of a lap-by-lap race model: how fast a car is on each tyre, how the tyres wear, what a pit stop costs, how
often safety cars and rain come and go, and how slow a lap is under them. The simulator of Phase 1 runs on these
numbers, and every agent of the later phases learns in that simulator.

---

## Why Does It Exist?

A strategy agent can only learn what the simulator rewards. If a new SOFT is no faster than a new HARD, or a tyre loses
39 s on one lap, the agent learns to exploit the model, not to race. Phase 0 therefore has two jobs:

1. **Measure** what the data can show, with methods that keep the comparison fair: the same car against itself, the
   same two laps of the cars that stayed out, the leader's own clock.
2. **Admit** what the data cannot show. Teams stop before a tyre falls off, so the cliff is never seen; rain mixes
   tyre choice with driver choice. Those numbers are priors, marked as such in the output.

Then it **checks** that the result is a strategy problem worth solving: the tyres are in order, the stop lap matters
but has a window, more than one tyre choice is sensible. A calibration that fails any check is not written.

---

## What Does Phase 0 Produce?

For each circuit in `configs/circuits.yaml`, two files in `data/processed/<circuit>/`:

| File | Content | Used by |
|---|---|---|
| `calibration.json` | Every parameter of the race model (schema v2), where each comes from (`provenance`), and the numbers behind it (`diagnostics`) | The environment, the baselines, the DP oracle |
| `scenarios.parquet` | Real races as lap-by-lap traces of weather and track status, exactly one race distance long | The dashboard, the historical comparison, a generalisation test |

Formats: [06. Output Data Formats](./06-output-formats.md).

## Circuits

| Circuit | Laps | Best dry plan | What makes it useful |
|---|---|---|---|
| Silverstone | 52 | 1 stop, MEDIUM and SOFT | Low wear: the stop lap is set by the assumed cliff |
| Monza | 53 | 1 stop, MEDIUM and HARD | Measured wear sets the stop; the development circuit |
| Spa | 44 | 1 stop, MEDIUM and HARD | Highest wear of the 1-stop races |
| Budapest (Hungaroring) | 70 | 2 stops, HARD, HARD, MEDIUM | A clear 2-stop race (1 stop is 7.9 s slower) |
| Barcelona | 66 | 2 stops, MEDIUM, HARD, HARD | 1 or 2 stops are close (1.8 s apart) |

A dry run over all 28 circuits in the data found 20 that pass every check; these five give 1-stop and 2-stop races
with the stop timing mostly measured. Adding a circuit is a line in `circuits.yaml` and a re-run.

---

## Data Flow

```
data/raw/                      FastF1 cache (2021-2023) and OpenF1 JSON (2023-2025)
    |
    |  python -m src.data.ingest          (03)
    v
data/interim/<race>/           laps, weather, track_status .parquet + manifest.json, one format for both sources
    |
    |  python -m src.calibration.run      (05)
    |    race conditions per lap          (04: leader timeline, status, weather regime)
    |    models                           (04: tyres, pit stops, safety cars, weather)
    |    build one calibration per circuit, price every dry plan (landscape)
    |    checks K1-K9; stop if any circuit fails
    v
data/processed/<circuit>/      calibration.json, scenarios.parquet
    |
    v
pytest tests/test_calibration.py   the gate before Phase 1
```

---

## Key Design Principles

- **Three kinds of number.** Each value is `fitted` (this circuit's own races), `pooled` (all circuits together) or
  `prior` (assumed). Per circuit: 3 fitted, 16 pooled, 40 prior entries. The split is on purpose: a circuit has 3-5
  races, too few to order three tyres, so the tyre pattern is pooled and each circuit only scales its wear.

- **Held-out data stays out.** 2025 races are ingested but never fitted, pooled or used to tune a threshold (D25).
  2026 is not even listed (D23): it is kept for a later transfer test. `races.yaml` refuses a list that breaks either rule.

- **Frozen inputs.** Ingest writes each race once to parquet with a manifest and content hashes. Calibration reads
  only the frozen files, so it runs offline and gives the same result every time.

- **Fail loudly.** Config keys have no defaults, the calibration file has a strict schema, and every failure is
  collected and reported at once. Nothing is written unless every circuit passes.

- **One race model.** Every lap time in Phase 0's checks comes from `src/env/dynamics.py`, the same function the
  simulator will use. The checks price the strategies the agent will face, not a copy of them.

- **No constants in code.** Every threshold, prior and filter lives in `configs/`. The checks' thresholds are
  provisional until confirmed.
