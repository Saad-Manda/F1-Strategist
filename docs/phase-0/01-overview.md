# Phase 0: Overview & Goals

## What Is Phase 0?

Phase 0 is the **Data Foundation** layer of the Stratex F1 Strategy Agent. It is a prerequisite for all subsequent phases (Gym Environment, RL Agent, Dashboard, etc.).

Its primary purpose is to transform raw, historical Formula 1 race timing data into a clean set of **physics-informed numerical models** that can drive a deterministic lap-time simulator. These models encode the key strategic variables that govern race outcomes: tyre degradation, fuel consumption, pit lane time loss, weather conditions, and safety car probability.

---

## Why Does It Exist?

A reinforcement learning agent cannot train in a vacuum. It needs a **simulation environment** (the Gym, built in Phase 1) that faithfully models how lap times evolve during a Grand Prix under different conditions. That simulator needs concrete numerical parameters to work — and Phase 0 is what derives those parameters from real-world data.

The quality and physical accuracy of the Phase 0 outputs directly determines how realistic the simulator will be, and therefore how transferable any strategy learned by the RL agent will be to real-world race conditions.

---

## What Does Phase 0 Produce?

For each configured circuit, Phase 0 produces two output files inside `data/processed/{circuit}/`:

1. **`calibration.json`** — A complete set of calibrated model parameters for the circuit:
   - Base race pace
   - Tyre compound degradation curves (per-compound `base_deg`, `cliff_age`, `cliff_severity`, `warmup_penalty`)
   - Fuel consumption and sensitivity
   - Pit lane time loss
   - Safety car deployment probability
   - Weather-to-compound penalty table

2. **`scenarios.parquet`** — A Parquet table of lap-by-lap scenario templates derived from real historical races, encoding weather regime, track temperature, rainfall, and safety car status per lap. These scenarios are replayed during RL training to initialize the simulator from realistic race conditions.

---

## Circuits Calibrated in Phase 0

| Circuit | FastF1 Event Name | Total Laps | Seasons |
|---|---|---|---|
| Silverstone | British Grand Prix | 52 | 2021, 2022, 2023 |
| Monza | Italian Grand Prix | 53 | 2021, 2022, 2023 |
| Spa | Belgian Grand Prix | 44 | 2021, 2022, 2023 |

---

## Data Flow

```
FastF1 API
    │
    ▼
data/raw/              ← FastF1 disk cache (raw session files)
    │
    ▼ (fetch.py)
Lap Data + Weather Data + SC Trace
    │
    ▼ (calibrate.py)
Fuel Correction → Driver-Stint Normalization → Piecewise Curve Fit
    │
    ▼
data/processed/{circuit}/
    ├── calibration.json
    └── scenarios.parquet
```

---

## Key Design Principles

- **Data-driven, not hand-tuned**: All numerical model parameters (degradation rates, cliff ages, pit loss) are fitted statistically from real race data, not guessed or hard-coded (unless data is insufficient, in which case sensible compound-specific defaults are used as a fallback).

- **Multi-season aggregation**: Each circuit is calibrated by pooling lap data from 3 seasons (2021, 2022, 2023), averaging out year-to-year performance outliers (e.g., one team's dominant car) and producing a more generalizable model.

- **Separation of concerns**: The pipeline is split into three distinct modules — `fetch.py` (ingest), `calibrate.py` (math), and `run_calibration.py` (orchestration) — so that each step can be understood, modified, and tested independently.
