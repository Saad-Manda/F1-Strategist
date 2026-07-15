# Phase 0: Master Runner

**File:** [`src/data/run_calibration.py`](../../src/data/run_calibration.py)

---

## Purpose

`run_calibration.py` is the **entry point** for the entire Phase 0 pipeline. It ties together the configuration loader (`circuits.yaml`), the FastF1 cache initializer, and the per-circuit calibration function into a single runnable script.

---

## How to Run

From the project root, with your virtual environment activated:

```bash
python -m src.data.run_calibration
```

> [!NOTE]
> The first run will take significant time (potentially 10-30 minutes per circuit) because FastF1 must download and parse raw session data from the F1 timing servers. Subsequent runs are served from the disk cache and complete in seconds.

---

## What It Does — Step by Step

1. **Loads `configs/circuits.yaml`**: Reads the list of circuits, their FastF1 event names, total race laps, and seasons to process.

2. **Initializes the FastF1 Cache**: Creates the `data/raw/` directory if it doesn't exist and enables FastF1's disk caching. This ensures all downloaded session data is stored locally for fast re-use.

3. **Iterates Over Each Circuit**: For each circuit defined in the YAML, prints a status header and calls `calibrate_circuit()` from `calibrate.py`.

4. **Error Handling**: Each circuit is wrapped in a `try/except` block. If a circuit-level failure occurs (e.g., an unexpected crash), the error is printed with `[ERROR]` and the runner continues to the next circuit instead of crashing the entire pipeline.

---

## Example Console Output

When run successfully, the output looks like:

```
Loaded 3 circuits for ingestion and calibration.

==========================================
Processing Circuit: SILVERSTONE (British Grand Prix)
Seasons to Ingest: [2021, 2022, 2023]
Total Laps: 52
==========================================

--- Starting Calibration: SILVERSTONE ---
Loading 2021 British Grand Prix...
Loading 2022 British Grand Prix...
Loading 2023 British Grand Prix...
[SUCCESS] Calibrated SILVERSTONE successfully!
   Base Pace: 90.34s, Pit Loss: 18.3s, SC Prob: 0.0897
   Saved calibration.json and scenarios.parquet (3 templates) to data/processed/silverstone

==========================================
Processing Circuit: MONZA (Italian Grand Prix)
...
```

---

## Re-running the Pipeline

The pipeline is **idempotent** — re-running it will overwrite the previous `calibration.json` and `scenarios.parquet` outputs. This is useful if:
- You add a new season to an existing circuit's config
- You add a completely new circuit
- You modify the calibration math in `calibrate.py` and need to regenerate outputs

---

## Dependencies

This script pulls together all the Phase 0 components. Ensure all packages in `requirements.txt` are installed before running:

```bash
pip install -r requirements.txt
```

**Key packages used:**

| Package | Version | Purpose |
|---|---|---|
| `fastf1` | ≥ 3.0.0 | F1 race session data API and disk caching |
| `pandas` | ≥ 2.0.0 | Lap data manipulation and aggregation |
| `numpy` | ≥ 1.24.0 | Numerical array operations |
| `scipy` | ≥ 1.10.0 | `curve_fit` for tyre degradation fitting |
| `pyarrow` | ≥ 12.0.0 | Writing and reading Parquet files |
| `pyyaml` | ≥ 6.0 | Loading `circuits.yaml` |
