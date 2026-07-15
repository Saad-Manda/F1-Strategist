# Phase 0: Calibration Pipeline

**File:** [`src/data/calibrate.py`](../../src/data/calibrate.py)

---

## Purpose

`calibrate.py` is the mathematical core of Phase 0. It takes the raw lap data extracted by `fetch.py` and runs a multi-step statistical fitting pipeline to estimate the key numerical parameters that the RL simulator depends on:

- Tyre degradation model per compound (base rate + cliff)
- Fuel consumption model
- Pit lane time loss
- Safety car deployment probability
- Weather-to-compound penalty

---

## The Problem: Why Raw Data Can't Be Fit Directly

A naive approach would be to plot all raw lap times against tyre age and fit a curve. This fails because raw F1 lap times are **contaminated by two major confounds**:

1. **Car/Driver Performance Spread**: A Red Bull running on MEDIUM tyres is 3-4 seconds per lap faster than a Haas on the same compound. Fitting a single curve across all drivers would produce a meaningless result biased toward whichever team ran the most laps.

2. **Fuel Weight Effect**: Cars start the race carrying up to ~110 kg of fuel. As it burns off at ~1.9 kg/lap, the car gets lighter and therefore faster — by approximately 3 seconds over a full race distance. This creates a strong downward trend in lap times that has nothing to do with tyre wear.

Phase 0 removes both effects through a two-stage normalization before fitting.

---

## Step 1: Fuel Correction

**Function:** `correct_for_fuel(laps, total_laps, consumption_kg_per_lap=1.9, sensitivity_s_per_kg=0.033)`

Subtracts the lap-time improvement due to fuel burn-off from every lap time:

$$T_{\text{corrected}} = T_{\text{raw}} - (\text{Laps Remaining} \times 1.9 \, \text{kg/lap} \times 0.033 \, \text{s/kg})$$

**Parameters used (from F1 domain knowledge):**

| Parameter | Value | Meaning |
|---|---|---|
| `consumption_kg_per_lap` | 1.9 kg/lap | Approximate fuel burn rate per racing lap |
| `sensitivity_s_per_kg` | 0.033 s/kg | Lap time improvement per kg of fuel burned |

After this correction, faster lap times at the end of the race due to lighter fuel loads are removed, leaving only tyre wear and car performance as sources of pace variation.

---

## Step 2: Driver-Stint Pace Normalization

Within `fit_degradation_curve()`, each driver's stint is individually normalized:

$$\text{deg}_{d,s}(t) = T_{\text{corrected},d,s}(t) - \text{Baseline}_{d,s}$$

Where $\text{Baseline}_{d,s}$ is the **5th percentile** of the fuel-corrected lap times within that driver's stint (rather than the minimum, to be robust against occasional fast laps due to traffic gaps or tactical pushes).

This operation converts absolute lap times into **degradation penalties relative to each driver's own best pace on that compound**, which completely removes car performance offsets. Now a Hamilton on MEDIUM and a Zhou on MEDIUM are measuring the same underlying tyre wear rate.

Only laps with `TrackStatus == "1"` (clean green-flag racing) and `IsAccurate == True` are included.

---

## Step 3: Piecewise Degradation Curve Fitting

**Function:** `piecewise_degradation(tyre_age, base_deg, cliff_age, cliff_sev)`

The normalized degradation data is aggregated by taking the **median degradation per tyre age** (further reducing noise), and a piecewise mathematical model is fitted:

$$\text{deg}(t) = \underbrace{\text{base\_deg} \cdot t}_{\text{linear wear}} + \underbrace{\text{cliff\_sev} \cdot \max(0, \, t - \text{cliff\_age})^2}_{\text{quadratic cliff}}$$

**Parameters fitted by `scipy.optimize.curve_fit`:**

| Parameter | Description | Physical Meaning |
|---|---|---|
| `base_deg` | Linear wear rate (s/lap) | Gradual pace loss from normal tyre wear on each additional lap |
| `cliff_age` | Cliff threshold (laps) | The tyre age at which the tyre compound exceeds its designed working temperature/load range and begins to degrade exponentially |
| `cliff_sev` | Cliff severity coefficient | Controls how rapidly the lap time penalty grows beyond the cliff — a higher value means a steeper drop-off |

**Fitting constraints (bounds):**

| Parameter | Lower Bound | Upper Bound |
|---|---|---|
| `base_deg` | 0.0 s/lap | 0.5 s/lap |
| `cliff_age` | 5 laps | 45 laps |
| `cliff_sev` | 0.0 | 2.0 |

These bounds prevent non-physical fits (e.g., negative wear, or cliff ages outside realistic stint lengths).

**Fallback defaults:** If fewer than 15 clean laps are available for a compound (e.g., a wet race where no one ran SOFT), or if `curve_fit` fails to converge, compound-specific defaults are used:

| Compound | Default `base_deg` | Default `cliff_age` | Default `cliff_sev` |
|---|---|---|---|
| SOFT | 0.08 s/lap | 18 laps | 0.35 |
| MEDIUM | 0.05 s/lap | 28 laps | 0.30 |
| HARD | 0.03 s/lap | 38 laps | 0.25 |

---

## Step 4: Warmup Penalty

New tyres require 1-2 laps to reach their optimal operating temperature. FastF1's `pick_quicklaps()` removes out-laps and in-laps, meaning `TyreLife == 1` data is unavailable. The warmup penalty is therefore a fixed domain-knowledge default applied on the first lap of each stint:

| Compound | Warmup Penalty |
|---|---|
| SOFT | 1.0 s |
| MEDIUM | 1.5 s |
| HARD | 2.5 s |
| INTERMEDIATE | 1.0 s |
| WET | 0.5 s |

---

## Step 5: Pit Lane Time Loss Estimation

**Function:** `estimate_pit_loss(session_laps)`

The pit lane time loss (the total time penalty incurred by driving through the pit lane, including the pit stop itself) is estimated empirically from consecutive stint transitions:

$$\text{pit\_loss} = (T_{\text{in-lap}} + T_{\text{out-lap}}) - (T_{\text{ref-in}} + T_{\text{ref-out}}) - \text{warmup\_penalty}$$

Where:
- $T_{\text{ref-in}}$ is the median of clean laps from the stint preceding the pit stop (excluding the final few laps to avoid cliff-degraded laps)
- $T_{\text{ref-out}}$ is the median of the first 2-4 clean laps of the next stint (laps 2-4, skipping the out-lap itself)
- The warmup penalty is subtracted to isolate the pure pit-lane infrastructure loss (drive-through time) from the known tyre warmup cost

**Quality filter:** Observations where the total loss is outside the range `[10s, 40s]` are discarded as likely erroneous or affected by special events (e.g., a driver serving a time penalty during a pit stop, such as Hamilton's 10-second time penalty at Silverstone 2021).

The final `pit_loss` is the **median** across all valid observations across all drivers and all seasons for the circuit.

---

## Step 6: Safety Car Probability

The per-lap safety car deployment probability is calculated directly from the empirical rate across all sessions:

$$P(\text{SC on lap}) = \frac{\text{Total SC-active laps across all drivers and sessions}}{\text{Total laps across all drivers and sessions}}$$

---

## Step 7: Baseline Pace

The circuit's `base_pace` (the reference lap time from which all degradation and fuel corrections are added) is set to the **5th percentile of all fuel-corrected MEDIUM compound laps** across all seasons. MEDIUM is used as the reference because it is the most commonly used compound in F1 races, providing the most data.

---

## Weather Compound Penalty Defaults

When a car is running the "wrong" compound for the weather condition, a lap-time penalty is applied. These penalties are encoded as a fixed lookup table of domain-knowledge defaults:

| Weather | SOFT | MEDIUM | HARD | INTER | WET |
|---|---|---|---|---|---|
| DRY | 0.0 s | 0.0 s | 0.0 s | 4.0 s | 10.0 s |
| DAMP | 6.0 s | 4.0 s | 3.0 s | 0.0 s | 2.5 s |
| WET | 15.0 s | 12.0 s | 10.0 s | 3.0 s | 0.0 s |

These represent the approximate lap time penalty for running an inappropriate compound — e.g., running SOFT tyres in a wet race incurs a ~15 second per lap penalty, while running INTER in DRY conditions costs ~4 seconds.

---

## Master Calibration Orchestrator

**Function:** `calibrate_circuit(circuit_name, circuit_fastf1_name, seasons, total_laps, ...)`

This is the top-level function that runs all the steps above in sequence for a single circuit:

1. Loop over each season in `seasons`:
   - Load the race session via `load_race_session()`
   - Extract and fuel-correct lap data
   - Extract safety car trace
   - Extract weather trace and merge with SC trace into a scenario template
   - Collect pit loss observations
2. Pool all laps from all seasons into a single dataframe
3. Fit degradation curves for each compound
4. Compute baseline pace, pit loss median, and SC probability
5. Write `calibration.json` and `scenarios.parquet` to `data/processed/{circuit_name}/`

If a season fails to load (e.g., API error, network issue), it is skipped with a warning and calibration continues on remaining seasons.
