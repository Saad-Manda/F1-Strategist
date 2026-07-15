# Phase 0: Data Foundation — Documentation Index

This documentation covers the complete **Phase 0 — Data Foundation** implementation of the Stratex F1 Strategy Agent project. Phase 0 is the bedrock layer of the entire system: it ingests raw historical F1 race data from the FastF1 API, cleans and normalizes it, and fits a set of physics-informed mathematical models that the RL simulator and agent (Phases 1+) depend on.

---

## Table of Contents

| Document | Description |
|---|---|
| [01. Overview & Goals](./01-overview.md) | What Phase 0 does and why it exists |
| [02. Circuit Configuration](./02-circuit-config.md) | How circuits and seasons are defined (`circuits.yaml`) |
| [03. Data Ingestion](./03-data-ingestion.md) | How raw race data is downloaded and extracted (`fetch.py`) |
| [04. Calibration Pipeline](./04-calibration.md) | How models are fitted and the output format (`calibrate.py`) |
| [05. Master Runner](./05-runner.md) | How to run the full pipeline (`run_calibration.py`) |
| [06. Output Data Formats](./06-output-formats.md) | Structure of `calibration.json` and `scenarios.parquet` |
| [07. Exploratory Notebooks](./07-notebooks.md) | What each notebook demonstrates and its plots |

---

## Quick Start

To reproduce the full Phase 0 ingestion and calibration pipeline from scratch:

```bash
# 1. Activate your Python virtual environment
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& "venv\Scripts\Activate.ps1"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the master calibration runner
python -m src.data.run_calibration
```

The pipeline will automatically download and cache the race sessions via FastF1, run the calibration math, and write the output files to `data/processed/{circuit}/`.
