# Phase 0: Configuration

**Files:** [`configs/circuits.yaml`](../../configs/circuits.yaml), [`configs/races.yaml`](../../configs/races.yaml),
[`configs/ingest.yaml`](../../configs/ingest.yaml), [`configs/defaults.yaml`](../../configs/defaults.yaml),
loaded by [`src/common/config.py`](../../src/common/config.py) and [`src/data/spec/races.py`](../../src/data/spec/races.py)

---

## Purpose

Every choice that is not code lives in these four files: which circuits are calibrated, which races exist and what
each may be used for, how ingest judges a race, and every modelling constant, prior and check threshold. Changing a
number never means editing Python.

---

## The Strict Loader

`load_config(file)` returns a read-only `ConfigSection`:

- A missing key raises `ConfigError` naming the file, the full key and the keys that do exist. An empty key raises too.
- There is **no `get` method**, on purpose: a fallback like `config.get("min_lap", 4)` would hide a default in the code.
- Repeated keys in the YAML are refused (plain YAML keeps the last one silently).
- Lists come back as tuples, mappings as nested `ConfigSection`s. Each file is read once per process.

---

## `circuits.yaml`: What Is Calibrated

```yaml
circuits:
  - name: silverstone
    total_laps: 52
  ...
```

| Key | Meaning |
|---|---|
| `name` | Circuit id, matching the `circuit` of its races in `races.yaml` and the folder in `data/processed/` |
| `total_laps` | Race distance the simulator runs, and the length of every trace |

Five circuits: silverstone 52, monza 53, spa 44, budapest 70, barcelona 66. The models use every race of every
circuit; this file only says which circuits get a `calibration.json`.

---

## `races.yaml`: Every Race and Its Role

113 races, one per line:

```yaml
- {id: 2022_spa, circuit: spa, year: 2022, source: fastf1, event: Belgian Grand Prix, role: fit}
- {id: 2024_spa, circuit: spa, year: 2024, source: openf1, session_key: 9574, role: fit}
- {id: 2025_spa, circuit: spa, year: 2025, source: openf1, session_key: 9939, role: holdout, repairs: [opening_compound]}
```

| Key | Meaning |
|---|---|
| `id` | `<year>_<circuit>`, plus a suffix when a circuit had two races in a year (`2021_spielberg_styria`) |
| `source` | `fastf1` (cache, needs `event`) or `openf1` (JSON, needs `session_key`) |
| `role` | What the race may be used for (below) |
| `repairs` | Named data repairs for one race. Only `opening_compound` exists (see [03](./03-data-ingestion.md)) |

| Role | Races | Used for |
|---|---|---|
| `fit` | 88 (2021-2024) | Everything: tyres, pit stops, chains, flag laps, rain slowdown |
| `conditions_only` | 1 (2021 Budapest) | Weather and track status only; its lap times are not fitted |
| `frequency_only` | 1 (2021 Spa) | Counts as a wet race; it has no usable laps (a few laps behind the safety car) |
| `holdout` | 23 (2025) | Ingested and replayed as traces, never fitted, pooled or used to tune (D25) |

The loader enforces the rules: `holdout_years: [2025]` must match `role: holdout` exactly, any year past
`last_allowed_year: 2025` is refused (2026 is kept for a transfer test, D23), ids are unique, and sources, roles and
repairs must be known names.

Two more lists: `cross_checks` holds three 2023 races also read from OpenF1, so the two readers can be compared on
the same race; `excluded` records races left out and why (2025 Miami: OpenF1 has about half the laps).

---

## `ingest.yaml`: Judging a Race

| Key | Value | Meaning |
|---|---|---|
| `version` | 2 | Raise it when the frozen format changes; every race is then rebuilt |
| `paths.raw`, `paths.interim` | `data/raw`, `data/interim` | Input and output of ingest |
| `sector_sum_tolerance_s` | 0.01 | A lap is accurate when its three sectors add up to its lap time |
| `checks.min_cars` | 15 | Fewer cars: the race is refused |
| `checks.min_known_compound_share` | 0.75 | Share of laps with a known tyre |
| `checks.max_missing_lap_time_share` | 0.20 | Share of laps without a time |
| `checks.max_suspect_label_share` | 0.25 | Share of laps whose tyre label cannot be trusted |

---

## `defaults.yaml`: Modelling Constants and Checks

Everything under `calibration:`. Each block is explained where it is used; this table says where.

| Block | Content | Kind | Explained in |
|---|---|---|---|
| `paths.processed` | Output folder | - | [05](./05-runner.md) |
| `conditions` | Weather label shares (0.5 known, 0.3 / 0.7 damp, 0.5 wet), median filter, max padded laps | rules | [04](./04-calibration.md#1-lap-conditions) |
| `fuel` | 1.9 kg per lap, 0.033 s per kg | prior | [04](./04-calibration.md#what-is-not-fitted) |
| `tyres` | Fit seasons 2022-2024, clean-lap filters, cliff priors per compound, cliff cap 4 s, rain tyre wear | rules and priors | [04](./04-calibration.md#2-dry-tyres) |
| `pit_stops` | From lap 4, at least 4 cars that stayed out | rules | [04](./04-calibration.md#3-pit-stops) |
| `flag_laps` | From lap 4; flag lap noise 1.0 s | rule, prior | [04](./04-calibration.md#4-safety-cars) |
| `weather` | From lap 4 | rule | [04](./04-calibration.md#5-weather) |
| `warmup_second_lap_share`, `warmup_defaults` | 0.3; warm-up 0 for every tyre | prior | [04](./04-calibration.md#what-is-not-fitted) |
| `weather_penalty_defaults` | Time per lap for each tyre in each weather, before the measured rain slowdown | prior | [04](./04-calibration.md#5-weather) |
| `checks` | Thresholds of K1-K9 and the landscape search | rules | [05](./05-runner.md#checks-k1-k9) |

> [!NOTE]
> The `checks` thresholds are **provisional**: chosen while building, not yet confirmed and frozen. Changing one needs
> a decisions entry, because a threshold tuned to make a circuit pass is no longer a check.
