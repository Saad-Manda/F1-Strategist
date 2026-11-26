# Phase 0: Runner and Checks

**Files:** [`src/calibration/run.py`](../../src/calibration/run.py), [`build.py`](../../src/calibration/build.py),
[`checks/landscape.py`](../../src/calibration/checks/landscape.py), [`checks/validate.py`](../../src/calibration/checks/validate.py),
[`src/common/schema.py`](../../src/common/schema.py), [`tests/test_calibration.py`](../../tests/test_calibration.py)

---

## Purpose

`run.py` builds one calibration per circuit, checks every circuit, and writes the files only if all of them pass. The
checks ask two questions: is each number plausible, and does the result make a strategy problem worth learning?

---

## How to Run

```powershell
python -m src.calibration.run              # build, check, write data/processed/<circuit>/
python -m src.calibration.run --dry-run    # build and check, write nothing
python -m src.calibration.run --out DIR    # write somewhere else
```

It needs the frozen races in `data/interim/` (run `python -m src.data.ingest` first). It exits 0 when every circuit
passes, 1 otherwise.

---

## What It Does

1. **Load** the configs, the race list, and the 89 fitting races with their conditions ([04](./04-calibration.md)).
2. **Build** (`build_calibrations`). What is pooled is fitted once: the clean laps, the tyre pattern, the pit stops.
   Then for each circuit in `circuits.yaml`: tyres, pit stops, track status and weather (which needs the circuit's
   `base_pace`). Fuel and warm-up share come from config as priors. The `provenance` and `diagnostics` of the four
   models are merged, and the strategy landscape (below) is added to `diagnostics.landscape`.
3. **Traces** (`circuit_traces`). Every `fit`, `conditions_only` and `holdout` race of the circuit becomes a trace of
   exactly `total_laps` laps. The holdout may be replayed, because replaying is not fitting (D25, D30). A race is left
   out, with the reason printed, if its weather could not be labelled or it is more than 3 laps short. A race up to 3
   laps short is padded by repeating its last lap's conditions, under green.
4. **Check** every circuit with K1-K9 and print a summary.
5. **Write** `calibration.json` and `scenarios.parquet` per circuit, only if no circuit failed.

### Example output (abridged)

```
monza: 3 fitted, 16 pooled, 40 prior
  fitted: base_pace, noise_std, pit_loss
  pooled: compound_pace_offset.SOFT, compounds.SOFT.base_deg, ...
  best dry plan: MEDIUM / HARD, stop on lap 26
budapest: 3 fitted, 16 pooled, 40 prior
  ...
  best dry plan: HARD / HARD / MEDIUM, stop on lap 24, 48
Written to data\processed/ for 5 circuits.
```

A circuit with a race that could not be replayed also prints `trace left out: <race>: <reason>`.

On a failure each circuit lists `FAILED K<n>: ...` lines, and the run ends with `Nothing written: <circuits> failed.`

---

## The Strategy Landscape

`landscape(params, config)` prices **every dry plan** of a green race with the race model (`compute_lap_time`,
`compute_pit_loss` in `src/env/dynamics.py`):

- 1 and 2 stops on every lap, 3 stops on every third lap (`three_stop_grid_laps`), never on the final lap;
- every tyre order that uses at least two dry compounds (the two-compound rule).

Pitting on lap $L$ runs lap $L$ on the old tyre and adds the pit loss; the new tyre is age 1 on lap $L+1$. To make
the search fast, `Prices` first sums the lap times of every possible stint (compound, first lap, last lap) once; a
plan is then the sum of its stints plus one pit loss per stop.

> [!NOTE]
> In this model the order of stints never changes the race time: tyre terms depend only on tyre age, fuel only on the
> lap. "MEDIUM then HARD, stop lap 27" and "HARD then MEDIUM, stop lap 26" can tie, and the file may name either.

| Result | Meaning |
|---|---|
| `best` | Fastest plan: tyres, stop laps, race time |
| `best_by_stops` | Best 1-, 2- and 3-stop plan, as seconds behind `best` |
| `tyre_choices` | For each set of dry tyres used (`SOFT+MEDIUM`, `MEDIUM+HARD`, `SOFT+HARD`, all three), its best plan over 1-3 stops, behind `best` (D37) |
| `stop_shift_cost` | Cheapest cost of moving one stop of `best` 5 laps earlier or later |
| `window_laps` | Most stop laps one stop can take while staying within 1 s of `best` |
| `no_stop_margin` | How much slower than `best` the fastest no-stop race would be (illegal; reported only) |
| `cliff_value` | `best` minus the best time with every cliff removed: how much the best plan rests on the assumed cliff |

| Circuit | Best plan | 1 / 2 / 3 stops behind | Shift cost | Window | Cliff value |
|---|---|---|---|---|---|
| silverstone | MEDIUM, SOFT; lap 29 | 0 / 13.6 / 30.8 | 13.3 s | 2 | 1.0 s |
| monza | MEDIUM, HARD; lap 26 | 0 / 11.1 / 28.5 | 1.1 s | 8 | 0 |
| spa | MEDIUM, HARD; lap 21 | 0 / 2.7 / 12.8 | 2.4 s | 7 | 0 |
| budapest | HARD, HARD, MEDIUM; laps 24, 48 | 7.9 / 0 / 8.2 | 1.5 s | 9 | 0 |
| barcelona | MEDIUM, HARD, HARD; laps 21, 44 | 1.8 / 0 / 10.1 | 1.2 s | 8 | 0 |

Silverstone's steep shift cost and 2-lap window come from the cliff: its wear is so low that the best plan runs each
tyre to just before the assumed cliff age, and any later stop falls off it.

---

## Checks K1-K9

`calibration_failures(params, config)` returns every failure as `"K<n>: what is wrong"`; `validate` raises one
`CalibrationError` listing them all. If the schema (K1) fails, nothing else is checked, because the other checks would
crash on a malformed file. Thresholds are in `defaults.yaml` under `calibration.checks` and are **provisional**.

| Check | Asks | Rule (threshold) |
|---|---|---|
| **K1** Schema | Is the file well formed? | Every field of schema v2 present, no unknown field, right types, all numbers finite, `schema_version` 2, provenance values known |
| **K2** Ordering | Are the tyres in order? | Pace measured from MEDIUM. SOFT faster new than MEDIUM, MEDIUM than HARD, by ≥ 0.05 s. Each wears ≥ 1.05x the next. Each reaches its cliff ≥ 1 lap earlier |
| **K3** Ranges | Is each number plausible? | `pit_loss` 12-30 s; `base_pace` 60-130 s; every `base_deg` 0.003-0.25; SC and VSC multipliers 0-1; SC and VSC lap 1.0-2.5x `base_pace` |
| **K4** Cliffs | Does the cliff stay bounded? | For every tyre and age, the cliff is 0 to `cliff_cap`. On each dry tyre, a stint 1.3x the 95th percentile stint loses < 8 s |
| **K5** Chains | Are the chains valid? | Every start and transition row is a probability row. DRY↔WET is 0. Expected SC laps per race 0.5-8 |
| **K6** Timing | Does the stop lap matter, with a window? | Moving a stop 5 laps costs ≥ 0.3 s; the 1 s window is ≤ 16 laps |
| **K7** Tyre choice | Does the choice of tyres matter, with more than one sensible? | Over `tyre_choices`: worst minus best ≥ 1 s, and ≥ 2 choices within 10 s of best |
| **K8** Provenance | Does every number say where it comes from? | Each calibrated field has exactly one source; no source names a non-field; a `fitted` number has enough data: `base_pace` and `noise_std` ≥ 300 clean laps, `pit_loss` ≥ 20 green stops |
| **K9** Noise | Is the fit not too good to be true? | `noise_std` > 0.2 s |

> [!IMPORTANT]
> K7 judges each set of tyres at **its own best number of stops** (D37). Judged on 1-stop plans only, it refused every
> circuit where a 2-stop is best, since a 1-stop on SOFT is far off there. A close 1-stop against 2-stop gap is not a
> defect, so it is reported (`best_by_stops`) but not checked.

---

## The Gate

```powershell
pytest tests/test_calibration.py
```

For each circuit in `circuits.yaml` it reads `data/processed/<circuit>/calibration.json` (which itself refuses a file
that does not match the schema), checks that `circuit` and `total_laps` match the config, and runs K1-K9. Phase 1 does
not start until it passes.

---

## Tests

`pytest` runs the fast tests; `pytest -m slow` the ones that load every frozen race. Tests mirror `src/`:

| Folder | Covers |
|---|---|
| `tests/common/` | Strict config loader; schema v2 (every way a file can be malformed) |
| `tests/data/` | Both readers (including track status from race control), tyre labelling (shifts, merges, the repair), lap flags, the race list rules, frozen storage |
| `tests/calibration/conditions/` | Leader timeline, status, weather regime, traces |
| `tests/calibration/models/` | Each model on small built races with known answers |
| `tests/calibration/checks/` | The landscape on races with a known best plan; one breakage per rule of K1-K9 |
| `tests/calibration/test_build.py`, `test_run.py` | The merged calibration, the runner's exit codes and writes, real traces (slow) |

The checks were themselves tested by breaking the source code on purpose, one change at a time, and confirming a test
fails for each.
