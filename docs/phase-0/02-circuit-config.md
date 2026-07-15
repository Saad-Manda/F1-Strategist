# Phase 0: Circuit Configuration

**File:** [`configs/circuits.yaml`](../../configs/circuits.yaml)

---

## Purpose

The `circuits.yaml` configuration file is the **single source of truth** for which Grand Prix events are ingested and calibrated in Phase 0. By changing this file, you can add, remove, or modify circuits without touching any Python code.

---

## File Structure

```yaml
circuits:
  - name: silverstone
    fastf1_name: "British Grand Prix"
    total_laps: 52
    seasons: [2021, 2022, 2023]

  - name: monza
    fastf1_name: "Italian Grand Prix"
    total_laps: 53
    seasons: [2021, 2022, 2023]

  - name: spa
    fastf1_name: "Belgian Grand Prix"
    total_laps: 44
    seasons: [2021, 2022, 2023]

fastf1:
  cache_dir: "data/raw"
```

---

## Field Definitions

| Field | Type | Description |
|---|---|---|
| `name` | string | A short, filesystem-safe identifier for the circuit (e.g., `silverstone`). Used as the output directory name under `data/processed/`. |
| `fastf1_name` | string | The exact Grand Prix event name as recognized by the FastF1 API. Must match FastF1's internal event naming precisely. |
| `total_laps` | integer | The scheduled race distance in laps. Used in fuel consumption calculations across the calibration pipeline. |
| `seasons` | list[int] | The list of race seasons (years) to download and aggregate for this circuit. Multiple seasons are pooled to produce a more robust, season-agnostic calibration. |
| `fastf1.cache_dir` | string | The directory where FastF1 will store its downloaded session cache files. Defaults to `data/raw/`. This directory is excluded from version control via `.gitignore`. |

---

## How It Is Used

The master runner script (`run_calibration.py`) reads this YAML file at startup and iterates over every circuit entry, calling `calibrate_circuit()` for each one with the configured parameters.

### Adding a New Circuit

To add a new circuit, simply append a new entry to the `circuits` list. Example:

```yaml
  - name: monaco
    fastf1_name: "Monaco Grand Prix"
    total_laps: 78
    seasons: [2021, 2022, 2023]
```

Then re-run `python -m src.data.run_calibration`. The new circuit will be automatically downloaded, calibrated, and its outputs saved to `data/processed/monaco/`.

> [!NOTE]
> The `fastf1_name` value must match FastF1's internal Grand Prix name. You can verify the correct name by checking the [FastF1 documentation](https://docs.fastf1.dev/) or by calling `fastf1.get_event_schedule(year)` in a Python session.
