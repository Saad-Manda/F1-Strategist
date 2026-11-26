# Phase 0: Data Foundation

Phase 0 turns real Formula 1 races into the numbers the race simulator runs on. It freezes every race of 2021-2025
from two data sources into one format, works out the conditions of each lap (leader timing, track status, weather),
fits the tyre, pit stop, safety car and weather models, checks the result against nine rules (K1-K9), and writes one
`calibration.json` and one `scenarios.parquet` per circuit. Every number says whether it was fitted on the circuit,
pooled over many circuits, or assumed.

The pipeline was built once, found wrong, and rebuilt in Phase 0.5. These pages describe the rebuilt pipeline;
[08. Remediation](./08-remediation.md) keeps the history.

---

## Table of Contents

| Document | Description |
|---|---|
| [01. Overview](./01-overview.md) | What Phase 0 produces, the data flow, and the rules it follows |
| [02. Configuration](./02-circuit-config.md) | The four config files: circuits, races, ingest, modelling constants and checks |
| [03. Data Ingestion](./03-data-ingestion.md) | Reading FastF1 and OpenF1, tyre labels, quality checks, the frozen race format |
| [04. Calibration Models](./04-calibration.md) | Lap conditions, then the tyre, pit stop, safety car and weather models |
| [05. Runner and Checks](./05-runner.md) | `run.py`, the strategy landscape, checks K1-K9, the gate and the tests |
| [06. Output Data Formats](./06-output-formats.md) | `calibration.json` (schema v2) and `scenarios.parquet` |
| [07. Notebooks](./07-notebooks.md) | What each notebook shows, plot by plot |
| [08. Remediation](./08-remediation.md) | What was wrong with the first pipeline, why the first fix would also have failed, what is still assumed |

---

## Quick Start

From the repo root:

```powershell
& "venv\Scripts\Activate.ps1"
pip install -r requirements.txt

python -m src.data.ingest          # data/raw -> data/interim/<race>/  (offline; skips races that are up to date)
python -m src.calibration.run      # data/interim -> data/processed/<circuit>/  (writes nothing if a check fails)
pytest tests/test_calibration.py   # the gate: every calibration.json passes K1-K9
```

`python -m src.calibration.run --dry-run` runs every check and writes nothing. `pytest` runs the fast tests and
`pytest -m slow` the ones that load every frozen race.

> [!IMPORTANT]
> `data/raw/` cannot be downloaded again: F1's archive now needs a login, and the FastF1 cache is tied to its version.
> Keep the backup in `data/backup/` and never upgrade FastF1 without one.
