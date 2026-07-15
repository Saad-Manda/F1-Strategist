# Phase 0: Exploratory Notebooks

Two Jupyter notebooks are provided as part of Phase 0 to visualize the raw data, validate the calibration pipeline, and build intuition for the mathematical models.

---

## Notebook 1: Data Exploration & Ingestion

**File:** [`notebooks/01_data_exploration.ipynb`](../../notebooks/01_data_exploration.ipynb)

This notebook demonstrates the full ingestion and normalization pipeline visually using Silverstone 2022 as the example race. It walks through the problem that Phase 0 solves (why raw data is noisy) and how the cleaning pipeline makes the underlying tyre physics legible.

---

### Plot 1: Raw Lap Times vs Tyre Age

**What it shows:** A scatter plot of all drivers' raw lap times (seconds, y-axis) against tyre age in laps (x-axis), color-coded by compound:
- SOFT → Red
- MEDIUM → Yellow
- HARD → Black
- INTERMEDIATE → Green
- WET → Blue

**Technical Details:**

This plot renders the unmodified `LapTime_s` directly from the FastF1 session laps dataframe, filtered only by FastF1's built-in `IsAccurate` flag (which removes obvious pit stop laps). It represents the raw signal that a naive model would try to fit.

**Strategic Insights:**

The scatter cloud is very wide vertically — often 5-8 seconds of spread at any given tyre age. This spread is caused by two overlapping effects:

1. **Car/Driver Performance Gap**: A Mercedes or Red Bull runs 3-4 seconds per lap faster than a Williams or Haas on identical tyres. These cars all appear in the same scatter, creating multiple overlapping horizontal bands.
2. **Fuel Weight Effect**: A car burns ~1.9 kg of fuel per lap. Since a heavier car is slower, a car at lap 1 (full fuel load, ~110 kg) is ~3 seconds slower per lap than the same car at lap 52 (near empty). This creates a strong downward trend in lap times across the race — but it's caused by fuel, not tyres.

The conclusion: fitting a tyre degradation curve directly on this raw data is impossible. The confounds completely mask the tyre wear signal.

---

### Plot 2: Fuel-Corrected Lap Times vs Tyre Age

**What it shows:** The same scatter plot as Plot 1, but after subtracting the fuel weight penalty from each lap time.

**Technical Details:**

The fuel correction formula is applied to each lap:

$$T_{\text{corrected}} = T_{\text{raw}} - (\text{Laps Remaining} \times 1.9 \, \text{kg/lap} \times 0.033 \, \text{s/kg})$$

This shifts each data point up by an amount proportional to how early in the race it occurred. A lap-1 time is shifted upward by ~$52 \times 1.9 \times 0.033 = 3.26$ seconds; a lap-52 time is shifted by 0.

**Strategic Insights:**

The scatter cloud narrows. The strong downward trend caused by fuel burn disappears. You can now see that all data points are clustered around a tighter range of corrected lap times — the tyre degradation trend is starting to become visible as a shallow upward slope.

However, the multiple horizontal bands (one per car performance tier) still exist. A further normalization step (Plot 3) is required to remove them.

---

### Plot 3: MEDIUM Tire Degradation Piecewise Fit

**What it shows:** A scatter plot of driver-stint-normalized median degradation penalties (seconds, y-axis) vs tyre age (x-axis), overlaid with:
- The fitted piecewise regression curve (orange line)
- A vertical red dashed line at the calibrated `cliff_age`

**Technical Details:**

**Stage 1 — Driver-Stint Normalization:**
For each `(Driver, Stint)` pair in the clean lap data:
1. The 5th percentile of the fuel-corrected lap times in that stint is computed as the `baseline`.
2. The degradation penalty for each lap is: $\text{deg} = T_{\text{corrected}} - \text{baseline}$

This converts absolute lap times into relative degradation within each driver's own stint, removing all car performance offsets. Now a Hamilton stint on MEDIUM and a Zhou stint on MEDIUM measure the same underlying tyre physics.

**Stage 2 — Median Aggregation:**
The normalized degradation values are grouped by `TyreLife` and the median is taken. This reduces stochastic noise (random lap-to-lap variation) further.

**Stage 3 — Piecewise Curve Fit:**
`scipy.optimize.curve_fit` fits the following function to the median data:

$$\text{deg}(t) = \text{base\_deg} \cdot t + \text{cliff\_severity} \cdot \max(0, t - \text{cliff\_age})^2$$

with the bounds `base_deg ∈ [0, 0.5]`, `cliff_age ∈ [5, 45]`, `cliff_sev ∈ [0, 2.0]`.

**Strategic Insights:**

The plot reveals two distinct physical phases of tyre wear:

1. **Linear Phase (before the cliff):** A steady, gradual increase in degradation penalty with each lap — approximately 0.03–0.08 seconds of additional lap time per lap.
2. **Cliff Phase (after the cliff age):** Once the tyre crosses its designed working range (the `cliff_age`), the rubber begins to grain, blister, or overheat and the lap time penalty rises steeply in a near-quadratic curve.

The `cliff_age` is the single most strategically important parameter: it defines the latest a driver can stay on a given compound before pace collapses. A strategist wants to pit **just before** the cliff.

---

### Plot 4: Safety Car Active Probability by Lap Number

**What it shows:** A bar chart of the safety car deployment rate (y-axis, fraction of drivers experiencing SC on that lap) per lap number (x-axis).

**Technical Details:**

For each lap, the fraction of drivers whose `TrackStatus` string contained `'4'` (Safety Car) is calculated and plotted as a bar. Pooling across all 3 seasons and all 20 drivers per race gives a relatively stable empirical probability distribution.

**Strategic Insights:**

The chart reveals structural patterns in safety car risk:

- **Lap 1** typically has the highest SC probability — start-line incidents (collisions, first-corner pile-ups) are far more common than any other lap.
- **Mid-race spikes** correspond to laps where tyre wear tends to peak, leading to spins or off-track excursions.

This distribution is compressed into a single scalar (`safety_car_probability_per_lap`) in `calibration.json`, but the full per-lap distribution is used in the Gym environment for more realistic SC injection during training.

---

## Notebook 2: Calibration Validation

**File:** [`notebooks/02_calibration.ipynb`](../../notebooks/02_calibration.ipynb)

This notebook loads the **output** of Phase 0 (`calibration.json` and `scenarios.parquet`) and simulates the transition dynamics forward in time to validate that the calibrated parameters produce physically plausible and strategically coherent lap-time profiles.

---

### Plot 1: Simulated Tyre Degradation Penalty Curves (Soft vs Medium vs Hard)

**What it shows:** Three lines (one per dry compound) plotting the simulated tyre degradation penalty (seconds, y-axis) against tyre age in laps (x-axis):
- SOFT → Red
- MEDIUM → Yellow
- HARD → Black

The degradation function used is exactly the fitted piecewise model from `calibration.json`.

**Technical Details:**

For each compound, the degradation penalty at age $t$ is computed using the fitted coefficients:

$$\text{deg}(t) = \text{base\_deg} \cdot t + \text{cliff\_severity} \cdot \max(0, t - \text{cliff\_age})^2$$

The x-axis runs from tyre age 1 to 45, covering the full range of possible stint lengths.

**Strategic Insights:**

This plot visualizes the fundamental tyre compound trade-offs that drive F1 strategy:

- **SOFT (Red):** The fastest compound early (lowest initial lap time penalty), but hits its cliff the earliest (~27 laps). Best for short, aggressive stints or qualifying-style speed.
- **MEDIUM (Yellow):** A balanced middle ground, hitting the cliff at ~33 laps. The most commonly prescribed first compound in modern F1.
- **HARD (Black):** The most durable compound — slow to warm up (high warmup penalty) and has a higher base degradation rate per lap in some circuits, but the cliff is very late (~32-38 laps) and relatively mild, making it ideal for long final stints.

From a strategy perspective, this plot answers: *"If I pit for a given compound, how long can I run it before pace collapses?"*

---

### Plot 2: Simulated Lap Times — 42-Lap MEDIUM Stint (Silverstone)

**What it shows:** A single line (yellow) plotting the simulated absolute lap times (seconds, y-axis) across 42 consecutive laps on MEDIUM tyres, starting from lap 1 of the race. A vertical red dashed line marks the `cliff_age` (~33.1 laps).

**Technical Details:**

For each lap $L$ (tyre age $t = L$, starting from stint beginning = race start):

$$\text{LapTime}(L) = \text{base\_pace} + \text{deg}(t) + (\text{Laps Remaining} \times 1.9 \times 0.033)$$

The lap time is the sum of:
- `base_pace`: The reference pace (5th percentile of historical MEDIUM corrected laps)
- Tyre degradation penalty $\text{deg}(t)$ from the fitted model
- Fuel weight penalty: $(52 - L) \times 1.9 \times 0.033$ seconds (car is heavier at the start, so this term decreases over time, making the car faster)

The stint is intentionally extended to 42 laps (beyond the 30-lap default) to ensure the cliff at 33.1 laps is clearly crossed and visible in the output.

**Strategic Insights:**

This chart is the clearest visualization of the two competing physical dynamics in an F1 race stint:

1. **Fuel Burn-off (makes the car faster):** As the car burns fuel (~$0.063$ s/lap pace improvement), lap times naturally decrease.
2. **Tyre Degradation (makes the car slower):** As the tyres age, the degradation penalty increases.

The resulting stint profile has **three distinct phases:**

| Phase | Laps | Description |
|---|---|---|
| **Fuel Dominant** | ~1–25 | Lap times steadily *decrease* as fuel burn-off improvement outweighs gradual tyre wear. The car is getting faster with each lap. |
| **Balanced** | ~26–33 | The fuel improvement and tyre wear effects roughly cancel out. Lap times plateau. |
| **Cliff Dominant** | ~34–42 | Past the cliff age, the quadratic degradation term explodes, causing lap times to increase rapidly. Each lap is now slower than the last — and the gap widens. |

This profile is why the `cliff_age` parameter is the key strategic decision variable: a strategist must pit **before** the cliff to avoid donating seconds per lap to the competition. The chart makes viscerally clear why staying out too long is catastrophically expensive in race time.
