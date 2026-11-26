# Phase 0: Output Data Formats

`python -m src.calibration.run` writes two files per circuit to `data/processed/{circuit_name}/`
([05. Runner and Checks](./05-runner.md)). This page describes the current format, schema version 2. How each number
is measured is in [04. Calibration Models](./04-calibration.md).

---

## 1. `calibration.json`

All parameters of one circuit's race model. The exact fields and types are defined in `src/common/schema.py`: a file
with a missing, unknown, wrongly typed or non-finite field is never written and never read. Times are in seconds.

### Fields

| Field | Content | Source |
|---|---|---|
| `schema_version` | `2` | - |
| `circuit`, `total_laps` | Name and race distance, from `configs/circuits.yaml` | - |
| `base_pace_reference_compound` | `"MEDIUM"`: pace offsets are measured from it | - |
| `fuel` | `consumption_kg_per_lap`, `sensitivity_s_per_kg` | prior |
| `warmup_second_lap_share` | Share of the warm-up penalty paid on a tyre's second lap | prior |
| `base_pace` | Lap time of a new MEDIUM with no fuel | fitted |
| `noise_std` | Spread of lap times the model does not explain (robust sd of the fit's residuals) | fitted |
| `compound_pace_offset` | Per compound: how much faster (negative) than MEDIUM when new. 0 for INTERMEDIATE and WET, whose pace is in the weather penalty | pooled (dry) / prior |
| `compounds` | Per compound: `base_deg` (s lost per lap of age), `cliff_age`, `cliff_severity`, `cliff_cap`, `warmup_penalty` | `base_deg` pooled (dry); the rest prior |
| `pit_loss` | Time a green stop adds, warm-up included | fitted |
| `pit_loss_sc_multiplier`, `pit_loss_vsc_multiplier` | Share of `pit_loss` a stop costs on the first lap of an SC / VSC | pooled |
| `status_start`, `status_transition` | Chance of GREEN / SC / VSC on lap 1, and from one lap to the next | pooled |
| `safety_car`, `virtual_safety_car` | `lap_time` of a flag lap | pooled |
| `flag_noise_std` | Spread of flag lap times | prior |
| `weather_start`, `weather_transition` | Chance of DRY / DAMP / WET on lap 1, and from one lap to the next | pooled |
| `weather_compound_penalty` | Per weather and compound: time added to the lap. DAMP and WET include the measured rain slowdown on every tyre | rain tyre pooled; gaps prior |
| `provenance` | Where each number comes from: `fitted`, `pooled` or `prior` | - |
| `diagnostics` | The numbers behind the fit, one section per model (below) | - |

Lap time, as computed by `src/env/dynamics.py`:

```
green lap = base_pace + compound_pace_offset + base_deg x age + min(cliff_severity x (age - cliff_age)^2, cliff_cap)
          + warm-up (ages 1 and 2) + fuel x laps still to run + weather_compound_penalty + noise
flag lap  = safety_car or virtual_safety_car lap_time + noise
```

### `provenance`

Keys are dotted paths (`compounds.SOFT.base_deg`); one key may cover a whole table (`status_transition`). Check K8
requires every number to have exactly one source, and a `fitted` number to have enough data behind it.

### `diagnostics`

| Section | Content |
|---|---|
| `tyres` | Races and clean laps used, stints per compound, 95th percentile stint age (`long_stint_age`), wear scale and its standard error, the pattern's standard errors |
| `pit_stops` | Number of green, SC and VSC stops, and their quartiles |
| `track_status` | Races, step counts of the chain, flag lap ratios, flag periods, the circuit's green lap |
| `weather` | Labelled and rejected races, step counts, rain slowdown and the races behind it |
| `landscape` | The best dry plan, gaps to it by number of stops and by tyre choice, the cost of moving a stop 5 laps, the 1 s window, and what the cliff costs the best plan ([05](./05-runner.md#the-strategy-landscape)) |

---

## 2. `scenarios.parquet`

Real races as replayable traces, one row per lap, each exactly `total_laps` long. The environment samples weather and
safety cars from the chains above for training and headline results; these real traces serve the dashboard, the
historical comparison and a generalisation test.

### Schema

| Column | Type | Content |
|---|---|---|
| `race_id` | string | For example `2024_silverstone` |
| `role` | string | `fit`, `conditions_only` (2021-2024) or `holdout` (2025, never fitted, D25) |
| `lap` | int | 1 to `total_laps` |
| `weather_regime` | string | `DRY`, `DAMP` or `WET`, from the tyres the field is on |
| `track_status` | string | `GREEN`, `SC` or `VSC` when the leader finished the lap. Red-flag laps read `SC` |
| `red_flag` | bool | The lap was red-flagged (not modelled, D21) |
| `rainfall` | bool | The rain sensor was on during the lap |
| `inter_share`, `wet_share` | float | Share of cars with a known tyre on INTERMEDIATE / WET |
| `air_temp_c`, `track_temp_c` | float | Mean during the lap |
| `padded` | bool | The race was up to 3 laps short and this lap repeats the last one (under green) |

### Races

Every fit, conditions-only and holdout race of the circuit whose weather could be labelled, 2021-2025: 5 per circuit,
except Spa with 4 (2021 Spa has no usable laps). 2021 Hungary is `conditions_only`: its weather and status are replayed,
but its lap times are not fitted. A race more than 3 laps short is left out, and `run.py` prints why.
