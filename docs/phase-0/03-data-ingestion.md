# Phase 0: Data Ingestion

**File:** [`src/data/fetch.py`](../../src/data/fetch.py)

---

## Purpose

`fetch.py` is responsible for all direct interaction with the **FastF1 API**. It downloads, caches, and parses raw Formula 1 race session data into three structured extracts that the calibration pipeline consumes:

1. **Lap Data** — Per-driver, per-lap timing and tyre information
2. **Weather Trace** — Lap-by-lap weather conditions and regime classification
3. **Safety Car Trace** — Lap-by-lap SC and VSC deployment status

---

## Functions

### `init_fastf1_cache(cache_dir)`

Initializes the FastF1 disk cache at the specified directory.

FastF1 downloads large binary session data files on first access, which can take several minutes per race weekend. Once cached, subsequent calls to `load_race_session()` for the same session are served from disk in seconds. This function ensures the cache directory exists before any session is loaded.

- **Default cache location:** `data/raw/` (excluded from git via `.gitignore`)

---

### `load_race_session(year, event_name)`

Downloads and returns a FastF1 `Session` object for a specific Race session.

- Loads **lap timing data** and **weather data** (telemetry is deliberately excluded — it's very large and not needed for strategy calibration).
- FastF1 returns the raw session exactly as broadcast by the F1 timing system, before any cleaning.

---

### `extract_lap_data(session)`

Extracts and cleans the per-lap timing dataframe from a loaded session.

**Steps performed:**
1. Converts `LapTime` (a `timedelta`) to float seconds as `LapTime_s`.
2. Drops rows with missing values for `Compound`, `TyreLife`, or `LapTime_s`.
3. Standardizes compound names to uppercase (FastF1 sometimes returns mixed-case strings).
4. Filters to valid compound codes only: `{"SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"}`.

**Output columns:**

| Column | Type | Description |
|---|---|---|
| `LapNumber` | float | Lap number in the race |
| `Driver` | string | Three-letter driver code (e.g., `"HAM"`, `"VER"`) |
| `Compound` | string | Tyre compound (`"SOFT"`, `"MEDIUM"`, `"HARD"`, etc.) |
| `TyreLife` | float | Number of laps the current tyre set has run |
| `LapTime_s` | float | Lap time in seconds |
| `Stint` | float | Stint index — increments at each pit stop |
| `TrackStatus` | string | Track status flag string (see below) |
| `IsAccurate` | bool | FastF1's flag for a representative racing lap |

#### Track Status Flags

FastF1 encodes track status as a concatenated string of numeric codes. Relevant codes:

| Code | Meaning |
|---|---|
| `'1'` | Green flag (normal racing) |
| `'2'` | Yellow flag |
| `'4'` | Safety Car active |
| `'6'` | Virtual Safety Car (VSC) active |

A lap may have multiple codes concatenated (e.g., `'124'` means both green and yellow flags and SC were active at different points during that lap).

---

### `extract_weather_trace(session)`

Extracts a lap-by-lap weather snapshot from the session's raw weather telemetry.

FastF1 provides weather data sampled at approximately 1-minute intervals during the race. This function aligns that irregular time-series to each completed lap by merging on the nearest session timestamp, producing one weather row per lap.

**Weather Regime Classification:**

The weather regime (`DRY`, `DAMP`, or `WET`) is derived from the **majority compound in use across all drivers on that lap**, not from a simple temperature threshold. This is a deliberate design choice: the compound actually selected by teams is the strongest real-world signal for whether the track is dry enough for slicks or requires wet-weather tyres.

| Majority Compound on Lap | Classified Weather Regime |
|---|---|
| `SOFT`, `MEDIUM`, or `HARD` | `DRY` |
| `INTERMEDIATE` | `DAMP` |
| `WET` | `WET` |

**Output columns:**

| Column | Type | Description |
|---|---|---|
| `LapNumber` | int | Lap number |
| `weather_regime` | string | `"DRY"`, `"DAMP"`, or `"WET"` |
| `TrackTemp` | float | Track surface temperature (°C) |
| `AirTemp` | float | Ambient air temperature (°C) |
| `Rainfall` | bool | True if rain was recorded during this lap |

If a session has no weather data at all (rare), a fallback DRY trace is generated using default temperatures.

---

### `extract_safety_car_trace(session)`

Extracts a lap-by-lap boolean record of Safety Car and Virtual Safety Car deployments.

**How it works:**

For each lap number in the session, the function checks whether **any driver** had a `TrackStatus` flag containing `'4'` (SC) or `'6'` (VSC) on that lap. Using an OR across all drivers ensures that even partial-lap SC deployments (e.g., deployed on lap 12 but only some drivers completed the lap under SC) are captured.

**Output columns:**

| Column | Type | Description |
|---|---|---|
| `LapNumber` | int | Lap number |
| `sc_active` | bool | True if Safety Car was active for any driver on this lap |
| `vsc_active` | bool | True if Virtual Safety Car was active for any driver on this lap |

---

## Important Implementation Notes

- **No telemetry downloaded:** `session.load(laps=True, telemetry=False, weather=True)` — Telemetry (GPS, throttle, brake traces) is excluded because it is very large and not required for race strategy calibration.
- **FastF1 cache is essential:** Without the disk cache, re-running the pipeline for the same 9 races (3 circuits × 3 seasons) would require downloading ~500MB+ from the F1 data servers every time.
- **`IsAccurate` flag vs. manual filtering:** FastF1's `IsAccurate` flag marks laps that were affected by pit stops, red flags, or safety cars. The calibration pipeline uses this flag in addition to `TrackStatus == "1"` filtering to isolate clean racing laps for curve fitting.
