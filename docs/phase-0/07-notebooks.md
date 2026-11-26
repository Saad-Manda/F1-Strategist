# Phase 0: Notebooks

**Files:** [`notebooks/01_data_exploration.ipynb`](../../notebooks/01_data_exploration.ipynb),
[`notebooks/02_calibration.ipynb`](../../notebooks/02_calibration.ipynb)

| Notebook | What it is |
|---|---|
| 01 Data exploration | An early look at one race (2022 Silverstone) straight from FastF1: why raw lap times cannot be fitted directly. It predates the pipeline |
| 02 Calibration | Where every number in `calibration.json` comes from, recomputed step by step and checked against the files |

---

## Notebook 1: Data Exploration

Loads 2022 Silverstone from the FastF1 cache (`data/raw/`) without any project code and makes four plots.

| Plot | Shows | What it teaches |
|---|---|---|
| Raw lap times against tyre age | Every lap, coloured by compound | The cloud is 5-8 s wide: car speed and fuel load hide the tyre effect |
| Fuel-corrected lap times | The same, minus $1.9 \times 0.033 \times$ laps remaining | Fuel burn makes laps faster over the race; removing it takes out the downward trend |
| MEDIUM degradation, piecewise fit | Each stint against its own 5th percentile, median by age, with a linear-plus-quadratic curve | Comparing a car only with itself removes car speed |
| Safety car share by lap | Share of cars with status `4` on each lap | Where in one race the safety car was out |

> [!NOTE]
> This notebook shows the problem, not the method in use. Its per-stint baseline and piecewise cliff fit on one race
> were replaced by the pooled fit of [04](./04-calibration.md#2-dry-tyres); the cliff cannot be fitted at all, because
> teams stop before it. Its safety car plot is a single race; the model counts a chain over 89 races.

---

## Notebook 2: Calibration

The notebook only **loads** with project code: the frozen races, their per-lap conditions (leader timeline, status,
weather label) and the config. Every step after that is written out in cells, and each section ends with an `assert`
against the `calibration.json` files that `python -m src.calibration.run` wrote. If the pipeline and the notebook ever
disagree, a cell fails. It runs on 2021-2024 races only and on every circuit in `circuits.yaml`.

### 1 Weather

**Table: weather per race.** For each of the 88 labelled races with rain, the number of DRY, DAMP and WET laps, and the
one race left out (2022 Spielberg, known tyres fall to 39%).

**Plot: 2024 Silverstone.**
- *Shows*: lap on x; the share of the field on INTER or WET (green line) and on WET (blue line); laps labelled DAMP
  shaded green; black ticks at the top where the rain sensor was on.
- *Computation*: the shares and labels of [04, Weather regime](./04-calibration.md#weather-regime).
- *Insight*: the rain sensor and the tyres do not always agree, and the label follows the tyres. A DAMP phase ends at
  its last lap with 70% of the field on rain tyres, as cars start going back to slicks, not when the last car changes.

**Tables: the chain and the slowdown.** Step counts and the transition matrix, the lap-1 shares, and the mean length of
a spell in each weather ($1 / (1 - p_{\text{stay}})$: 969 laps DRY, 37 DAMP, 12 WET). Then the rain slowdown per race:
DAMP 11.1% (median of 9 races, 6.9-21.5%), WET 21.1% (one race).

### 2 Dry tyres

**Table: clean laps per step**: 63,333 laps of 58 fully dry races down to 49,902.

**Table: the pattern**: offsets and wear with stint-clustered standard errors (SOFT -0.257 s, HARD +0.074 s; wear
0.065 / 0.047 / 0.041 s per lap).

**Table: per circuit**: clean laps, wear scale and its error, `base_pace`, `noise_std`.

**Table: raw against used.** Each circuit fitted on its own, with its own offsets and wear, next to the pooled values
the file uses. The own-circuit numbers are noisy and in places out of order (fitted alone, Silverstone's HARD comes out 0.11 s faster than its MEDIUM); this is why the
pattern is pooled.

**Plot: degradation and cliffs**, one panel per circuit.
- *Shows*: tyre age on x, time lost to wear on y. Solid line: the degradation used (`base_deg` × age plus the capped
  cliff). Dashed: the circuit's own raw wear fit. A dot at the 95th percentile tyre age seen at the circuit.
- *Computation*: `cliff_age` = max(prior, ⌈95th percentile⌉), asserted against the files.
- *Insight*: to the right of the dot the data says almost nothing, and the shape there is the prior. The cliff's
  start is pushed later where teams ran long stints; its steepness is never measured.

### 3 Pit stops

**Table: green pit loss per circuit**: count, mean, quartiles of every green stop's measured loss.

**Plot: histogram of green stop losses**, one colour per circuit, with each median in the legend.
- *Insight*: the losses are tight around the median (quartiles within about 3 s), with a long right tail of slow
  stops; the median ignores that tail.

**SC and VSC shares**: 0.68 of a green stop from 118 stops in 20 races; 0.62 from 55 stops in 15 races.

### 4 Safety cars

**Status chain**: transition matrix and lap-1 shares, and the expected SC laps per race at each circuit (1.9-2.8).

**Flag laps**: periods and laps used (29 SC periods, 98 laps; 22 VSC periods, 33 laps), the ratios (1.746 and 1.356
green laps), and each circuit's green, SC and VSC lap time.

### 5 Does strategy matter?

**Plot: every 1-stop plan**, one panel per circuit.
- *Shows*: stop lap on x, seconds behind the best 1-stop plan on y. One solid line per pair of tyres (MEDIUM then SOFT,
  HARD then SOFT, HARD then MEDIUM); the dashed line of the same colour is the same plan **without any cliff**. A thin
  line at 1 s.
- *Computation*: a race time written out lap by lap with the formula of [04](./04-calibration.md), asserted against
  the landscape's best 1-stop time.
- *Insight*: where the solid and dashed lines agree near their minimum (Monza, Spa, Budapest, Barcelona), the best stop
  lap comes from the measured wear. At Silverstone the dashed lines are almost flat and the solid ones drop sharply at
  the cliff: its timing comes from the prior.

**Table: the full landscape** from `diagnostics.landscape` for every circuit: best plan, shift cost, window, gaps by
number of stops and by tyre choice, no-stop margin, cliff value ([05](./05-runner.md#the-strategy-landscape)).

### 6 What is measured and what is assumed

The provenance of every field, the same at every circuit (asserted): 3 fitted (`base_pace`, `noise_std`, `pit_loss`),
16 pooled, 40 prior, each listed by name.
