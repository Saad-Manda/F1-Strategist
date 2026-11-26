# Phase 0: Remediation (Phase 0.5)

The first Phase 0 pipeline (`fetch.py`, `calibrate.py`, `run_calibration.py`, since deleted) ran, but its
`calibration.json` files could not support a meaningful strategy problem. Phase 0.5 replaced it with the pipeline the
other pages describe. This page keeps the history: what was wrong, why the first planned fix would also have failed,
and what replaced each part.

---

## What Was Wrong

| Defect in the Phase 0 output | Effect |
|---|---|
| No pace offset between compounds | A new SOFT was no faster than a new HARD, so the only reason to choose a tyre was wear |
| Degradation fitted per circuit and compound, unordered | At Monza HARD wore faster than MEDIUM (0.060 against 0.055 s per lap) |
| Quadratic cliff with no cap | Up to 39 s lost on a single lap: any plan that reached it was absurd |
| Weather labelled from the rain sensor (`Rainfall`), with `INTER` keys that matched no compound | Every scenario lap came out DRY; laps where the field stayed on slicks could be charged as damp |
| Scenarios cut short | `2021_spa` had 3 rows, `2023_monza` 51 of 53 |
| Safety car lap time hardcoded at 160 s | The same at Monza (84 s laps) and Spa (110 s laps) |
| "Leader" taken as the first row per lap (`groupby(...).first()`) | Weather and status joined at the wrong time, by up to 33 s on average |
| Any car's flag counted as a safety car | Spells lengthened by lapped cars |
| `noise_std` a default of 0.20 s | Real residuals are 0.33-0.67 s |
| Broad `except` with fallbacks; the runner exited 0 after errors | A failed fit silently wrote default numbers |

## Why the First Fix Would Also Have Failed

The first Phase 0.5 plan fixed the obvious defects, but was checked against the data before it was built:

- **Young-tyre medians for the compound offset** made HARD faster than MEDIUM on 3 of 5 circuits: HARD is run later
  in the race, so a faster track and fuel error leak into it.
- **A joint fit per circuit** was better, but still unordered in places. Ordering needs many circuits pooled.
- **The cliff is not in the data.** Teams stop before it: adding a cliff to the fit lowers the error by 0-7%, with
  severities at least ten times smaller than the defaults. A gate of "no fallback for dry compounds" could never pass.
- **Its own checks rejected its own example**: "no lap above 5 s of degradation" fails on the plan's example schema
  (7.3 s at age 52), and "1-stop and 2-stop must differ by more than 2 s" fails exactly the circuits where the choice
  is interesting.
- **The weather rule** `DAMP if Rainfall or ...` would charge slicks 3-6 s a lap at 2023 Spa, where everyone stayed on
  slicks, and calls a field on full wets DRY when the sensor is off.
- **The nine cached races had no wet phase at all**, so a weather chain could not be measured. The data set had to grow
  to every race of 2021-2025 (OpenF1 for 2023-2025), with 2025 held out of all fitting.
- **The safety car stop discount of 0.4** was not in the data at lap level; it had to be measured another way.

## What Was Built

```
data/raw  ->  python -m src.data.ingest  ->  data/interim/<race>/*.parquet   (frozen, offline)
          ->  python -m src.calibration.run  ->  data/processed/<circuit>/calibration.json, scenarios.parquet
```

| Step | Method |
|---|---|
| Conditions per lap | The leader is the car with the smallest time at each lap; status is the one active when the leader finishes the lap. Weather is labelled from **tyres**: DAMP from 30% of known tyres on INTER/WET until the phase's last lap at 70%, WET at 50% on WET. A race whose known tyres fall under 50% gets no weather label |
| Dry tyres | Clean laps of 58 fully dry 2022-2024 races. One compound pattern (offsets and wear) for all circuits, then one wear scale per circuit. Each car is compared only with itself; each race has its own lap trend |
| Pit loss | In-lap plus out-lap against the same two laps of cars that stayed out. Under SC and VSC: stops on the first lap of a period, as a share of a green stop (0.68 and 0.62) |
| Safety cars | A chain GREEN / SC / VSC counted over 89 races, lap 1 counted on its own. Flag lap time from the time lost over each period, as a share of a green lap |
| Weather | A chain DRY / DAMP / WET counted over 88 labelled races. Rain slows every tyre by the measured share (11.1% damp, 21.1% wet) of the circuit's pace |
| Checks K1-K9 | Schema, tyre order, plausible ranges, cliff cap, chains, timing and tyre choice matter, provenance, noise. All failures are reported at once and nothing is written if any circuit fails |

Details: ingestion in [03](./03-data-ingestion.md), the models in [04](./04-calibration.md), the checks in
[05](./05-runner.md). Every number is recomputed step by step in `notebooks/02_calibration.ipynb` ([07](./07-notebooks.md)).

## What Is Assumed

Every number in `calibration.json` has a `provenance` entry: `fitted` (this circuit's own data), `pooled` (many
circuits) or `prior` (assumed). Per circuit: 3 fitted, 16 pooled, 40 prior entries.

| Assumed | Why |
|---|---|
| Cliff severity and cap (4 s); cliff age where no stint ran that long | Teams stop before the cliff. The data only says it comes no earlier than the 95th percentile stint |
| Gaps between tyres in the rain, rain tyre wear | Selection mixes them up: cars stay out too long or switch late |
| Full-wet slowdown | Measured, but from one race (2022 Monaco) |
| Fuel effect, flag lap noise, warm-up share | Not identifiable from this data. Warm-up is 0: the measured pit loss already contains it |

**Five circuits** are calibrated: Silverstone, Monza and Spa (1-stop races) and Hungaroring and Barcelona (2-stop races).
A dry run of all 28 circuits in the data showed which ones the data supports.

**Silverstone's strategy comes from assumptions.** Its measured wear is 0.013-0.020 s per lap, so its best plan runs
each tyre to just before the prior cliff. At the other four the cliff never touches the best plan. Development uses Monza.

## Gate

`pytest tests/test_calibration.py` reads each `calibration.json` and runs K1-K9. Phase 1 does not start until it passes.
