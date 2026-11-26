# Phase 0: Calibration Models

**Files:** [`src/calibration/conditions/`](../../src/calibration/conditions/) (`timeline.py`, `status.py`, `regimes.py`,
`table.py`), [`fitting_races.py`](../../src/calibration/fitting_races.py),
[`models/`](../../src/calibration/models/) (`clean_laps.py`, `tyre_fit.py`, `tyres.py`, `pit_stops.py`,
`track_status.py`, `chains.py`, `weather.py`, `fields.py`)

---

## Purpose

These modules turn frozen races into the parameters of the race model. First each race gets a per-lap table of
conditions (when the leader ran each lap, the track status, the weather). Then four models each return a `Fields`:
the values, where each comes from (`fitted`, `pooled`, `prior`), and diagnostics that show the data behind them.

**Which races.** `load_fitting_races` loads only roles `fit` and `conditions_only`: 89 races of 2021-2024. The 2025
holdout is never loaded here. Each model then narrows the set further, as stated below.

The race model these numbers feed, as computed by [`src/env/dynamics.py`](../../src/env/dynamics.py):

$$
t_{\text{green}} = b + o_c + d_c\,a + \min\!\big(s_c\,(a - A_c)_+^2,\; K\big) + w_c(a) + f\,(N - \ell) + P_{W,c} + \varepsilon
$$

$$
t_{\text{SC}} = t^{\text{SC}} + \varepsilon, \qquad t_{\text{VSC}} = t^{\text{VSC}} + \varepsilon
$$

| Term | Field | Meaning |
|---|---|---|
| $b$ | `base_pace` | Lap of a new MEDIUM with no fuel |
| $o_c$ | `compound_pace_offset` | How much faster (negative) tyre $c$ is than MEDIUM when new |
| $d_c\,a$ | `compounds.c.base_deg` | Linear wear, $a$ = tyre age (1 on the first lap) |
| $s_c, A_c, K$ | `cliff_severity`, `cliff_age`, `cliff_cap` | The cliff: quadratic after age $A_c$, capped at $K$ |
| $w_c(a)$ | `warmup_penalty`, `warmup_second_lap_share` | Warm-up on ages 1 and 2 |
| $f\,(N-\ell)$ | `fuel` | Fuel still on board for the laps after lap $\ell$, $f$ = 1.9 kg x 0.033 s/kg = 0.0627 s per lap |
| $P_{W,c}$ | `weather_compound_penalty` | Time lost on tyre $c$ in weather $W$ |
| $\varepsilon$ | `noise_std`, `flag_noise_std` | Lap-to-lap noise |

A stop adds `pit_loss` (times `pit_loss_sc_multiplier` or `pit_loss_vsc_multiplier` under a flag) to the lap it is
made on; that lap runs on the old tyre.

---

## 1. Lap Conditions

`race_conditions(race, frames, rules)` builds one row per lap of the leader: `start_s`, `end_s`, `status`, `regime`,
the tyre shares, rainfall and temperatures.

### Leader timeline

The leader of lap $\ell$ is the first car to finish it: $\text{end}_\ell = \min_{\text{cars}} \text{lap\_end}$. Each
lap starts when the previous one ended, so the laps cover the race without gaps. Lap 1 starts at the earliest lap-1
start. Missing end times or times that go backwards fail the race.

> [!NOTE]
> The first Phase 0 took the first row of each lap as the leader. That is whichever car comes first in the table, and
> it put weather and status up to 33 s off on average.

### Track status

Status is read **when the leader finishes the lap**, because that is when a car decides to stop (D31):

| Status | When |
|---|---|
| `RED` | A red flag was active at any time during the lap, or the lap before (the restart lap is not racing) |
| `SC` | Code 4 at the end of the lap |
| `VSC` | Code 6 or 7 at the end of the lap |
| `GREEN` | Otherwise |

Red flags are not modelled (D21): they break the status chain, and traces show them as `SC` with `red_flag` set.

### Weather regime

A lap is DRY, DAMP or WET by **what tyres the field is on**, not by the rain sensor. The sensor can show rain while
everyone stays on slicks (2023 Spa), or nothing while the field is on full wets.

Per lap, among cars with a trusted tyre label: $r$ = share on INTERMEDIATE or WET, $r_W$ = share on WET.

1. **DAMP** phases start when $r \ge 0.3$. A phase ends at its last lap with $r \ge 0.7$: teams stay on rain tyres
   too long as the track dries, so the tail is cut (D28). A phase that never reaches 0.7 is DAMP throughout.
2. **WET** wherever $r_W \ge 0.5$.
3. A 3-lap median filter removes one-lap flicker.

A race in which any lap has under 50% trusted tyre labels gets **no** weather label (D29): its `regime` is empty and
it is left out of everything that needs weather. One race is left out this way (2022 Spielberg). Of the 88 labelled
races, 13 have rain.

Rainfall and temperatures are averaged over the samples inside the lap, or taken from the last sample before it.

---

## 2. Dry Tyres

### Clean laps

The tyre model is fitted on fully dry `fit` races of 2022-2024 (the 18-inch tyres; D11, D32): **58 races**. A race
with any damp lap is left out entirely, because a drying track looks like tyre wear. A lap is kept when, in order:

| Step | Rule | Laps left |
|---|---|---|
| all | | 63,333 |
| known dry tyre | SOFT, MEDIUM or HARD with a trusted label | 63,186 |
| green | Clear track for the car (code `1`) and `GREEN` for the leader | 56,889 |
| accurate | `is_accurate` (drops pit laps and broken timing) | 53,176 |
| settled | Lap 4 or later, tyre age 3 or more | 50,493 |
| near median | Within 3 s of the car's median clean lap (drops traffic and mistakes) | 49,902 |

Fuel is removed from each lap: $\text{pace} = t - f\,(N - \ell)$.

### The fit (D32)

One equation for every clean lap $i$ of car $k$ in race $r$:

$$
\text{pace}_i = \alpha_k + \beta_r\,\ell_i + o_{c_i} + w_{c_i}\,a_i + e_i, \qquad o_{\text{MEDIUM}} = 0
$$

- $\alpha_k$: each car in each race has its own level, removed by subtracting the car's mean from every column. Cars
  are only compared with themselves, so a fast team on SOFT does not make SOFT look fast.
- $\beta_r\,\ell$: each race has its own lap trend, because the track rubbers in and gets faster.
- $o_c$, $w_c$: the pace offset and wear per lap of each compound.

It is solved by least squares. Laps of one stint are not independent, so standard errors are clustered by stint
(sandwich estimator). The pooled pattern over all circuits:

| | SOFT | MEDIUM | HARD |
|---|---|---|---|
| Offset (s) | -0.257 ± 0.048 | 0 | +0.074 ± 0.030 |
| Wear (s per lap) | 0.0652 ± 0.0034 | 0.0466 ± 0.0019 | 0.0414 ± 0.0013 |

A circuit's 3-5 races are too few to order three tyres: fitted on its own, a circuit can make HARD faster than MEDIUM
or wear faster. So the pattern is pooled, and each circuit only gets a **wear scale** $\lambda$, with the pattern fixed:

$$
\text{pace}_i - o_{c_i} = \alpha_k + \beta_r\,\ell_i + \lambda\,(w_{c_i}\,a_i) + e_i
$$

| Value | From | Kind |
|---|---|---|
| `compounds.c.base_deg` | $\lambda\,w_c$ | pooled |
| `compound_pace_offset.c` | $o_c$ | pooled |
| `base_pace` | Median over cars of each car's mean of $\text{pace} - o_c - \lambda w_c a$ | fitted |
| `noise_std` | $1.4826 \times \operatorname{median}\lvert e_i\rvert$ (a robust standard deviation) | fitted |

A circuit with $\lambda \le 0$ (tyres getting faster with age) is refused. Results:

| Circuit | Clean laps | $\lambda$ | `base_pace` | `noise_std` | `base_deg` SOFT / MEDIUM / HARD |
|---|---|---|---|---|---|
| silverstone | 1,374 | 0.31 | 91.61 | 0.33 | 0.020 / 0.014 / 0.013 |
| monza | 2,382 | 1.12 | 84.20 | 0.39 | 0.073 / 0.052 / 0.046 |
| spa | 1,838 | 2.21 | 110.49 | 0.54 | 0.144 / 0.103 / 0.091 |
| budapest | 3,313 | 1.44 | 81.51 | 0.52 | 0.094 / 0.067 / 0.060 |
| barcelona | 3,238 | 1.50 | 77.95 | 0.48 | 0.098 / 0.070 / 0.062 |

### The cliff

Teams stop **before** a tyre falls off, so the laps show almost no cliff: adding one to the fit improves it by 0-7%
(E4). The data only says the cliff comes no earlier than the stints people actually ran:

$$
A_c = \max\big(A_c^{\text{prior}},\ \lceil q_{0.95}(\text{age of clean laps on } c \text{ at the circuit})\rceil\big)
$$

with priors 18 / 28 / 38 laps for SOFT / MEDIUM / HARD. Severity (0.35 / 0.30 / 0.25 s per lap²) and the cap
$K$ = 4 s are priors. The 95th percentile ages are stored as `diagnostics.tyres.long_stint_age`.

> [!IMPORTANT]
> Where the measured wear is low, the best stop lap is set by this assumed cliff. That is the case at Silverstone,
> whose strategy therefore rests on a prior; at the other four circuits the cliff never touches the best plan
> (`diagnostics.landscape.cliff_value` = 0).

### Rain tyres

INTERMEDIATE and WET have no dry pace offset (their pace is in the weather penalty, below), wear 0.05 s per lap and the
same cliff priors: all priors.

---

## 3. Pit Stops

`race_stops` measures every stop of the fully dry `fit` races (2021-2024).

A stop costs the in-lap and the out-lap. They are compared with **the same two laps** of cars that stayed out, each
corrected for how fast that car usually is ($u_k$, its median green lap without pit laps):

$$
L_k = \big(\text{end}_{k,\ell+1} - \text{end}_{k,\ell-1} - 2u_k\big) - \operatorname{median}_{j\ \text{stayed out}} \big(\text{end}_{j,\ell+1} - \text{end}_{j,\ell-1} - 2u_j\big)
$$

for a car that enters the pits on lap $\ell$ and leaves on $\ell+1$, from lap 4, with at least 4 cars that stayed out.

| Kind | Which stops | Value | Kind |
|---|---|---|---|
| Green | Clear track (code `1`) for the car on both laps | `pit_loss` = median of the circuit's green $L_k$ | fitted |
| SC / VSC | The stop lap is the **first** lap of the period (green before, not red after) | `pit_loss_sc_multiplier`, `pit_loss_vsc_multiplier` = median over all circuits of $L_k / \text{pit\_loss}_{\text{circuit}}$ | pooled |

Only the first lap of a period is used: later, the field is bunched behind the safety car and the comparison with
cars that stayed out no longer measures the stop. Results: SC 0.68 (118 stops, 20 races), VSC 0.62 (55 stops, 15
races) (D33). Green pit loss: silverstone 20.5 s (49 stops), monza 25.5 (80), spa 18.4 (105), budapest 21.7 (106),
barcelona 23.0 (169).

The measured green loss already contains the new tyre's warm-up, so `warmup_penalty` is 0 for every tyre (D33);
otherwise it would be counted twice.

---

## 4. Safety Cars

### The status chain (pooled)

`count_steps` counts, over all 89 races, the status of lap 1 and every step from one lap to the next. Lap 1 is
counted on its own because races can start behind the safety car. A `RED` lap breaks the chain: steps into or out of
it are not counted. Each row of counts divided by its sum is a probability row:

| From \ to | GREEN | SC | VSC |
|---|---|---|---|
| GREEN | 0.9840 | 0.0094 | 0.0066 |
| SC | 0.2898 | 0.7102 | 0 |
| VSC | 0.6739 | 0.0435 | 0.2826 |

Lap 1: GREEN 0.802, SC 0.174, VSC 0.023. Over a race this gives 1.9-2.8 expected SC laps depending on race length.
Every circuit gets the same chain: one circuit's 4-5 races are too few to count it.

### Flag lap time (pooled ratio, circuit's own green lap)

Because status is read at the end of the lap, the lap **after** a period is still slow, and its lost time belongs to
the period. For every dry SC or VSC period from lap 4 that has green laps on both sides, with $n$ labelled laps and
the race's median dry green leader lap $g$:

$$
\text{extra} = \frac{\sum_{\ell=\text{first}}^{\text{last}+1} \text{duration}_\ell}{g} - (n + 1)
$$

The flag lap, in green laps, is chosen so that the labelled laps lose as much time as the real ones:

$$
\rho = 1 + \frac{\sum \text{extra}}{\sum n}
$$

SC $\rho$ = 1.746 (29 periods, 98 laps), VSC $\rho$ = 1.356 (22 periods, 33 laps). Each circuit's flag lap is $\rho$
times its own green lap (median over its fully dry races), for example Monza: 86.0 s green, 150.1 s SC, 116.6 s VSC.
`flag_noise_std` (1.0 s) is a prior.

---

## 5. Weather

### The weather chain (pooled, D35)

Counted like the status chain, over the 88 labelled races:

| From \ to | DRY | DAMP | WET |
|---|---|---|---|
| DRY | 0.9990 | 0.0010 | 0 |
| DAMP | 0.0242 | 0.9728 | 0.0030 |
| WET | 0 | 0.0870 | 0.9130 |

Lap 1: DRY 0.898, DAMP 0.091, WET 0.011. DRY to WET and WET to DRY never happen; check K5 makes sure they stay 0.

### Rain slowdown (pooled)

For each weather, the tyre made for it is the one whose prior penalty is 0 (INTERMEDIATE in DAMP, WET in WET). In
each race, each car's median fuel-corrected lap on that tyre in that weather is compared with **the same car's**
median dry lap on slicks (accurate, clear-track, green laps from lap 4):

$$
\text{slowdown}_W = \operatorname{median}_{\text{races}} \Big( \operatorname{median}_{\text{cars}} \frac{\text{rain pace}}{\text{dry pace}} \Big) - 1
$$

DAMP: 11.1% (9 races). WET: 21.1%, from **one race** (2022 Monaco, the only one with clean laps on WETs and slicks).

### Penalties

Each circuit's penalty adds the measured slowdown, as a share of its own `base_pace`, to every tyre:

$$
P_{W,c} = P_{W,c}^{\text{prior}} + \text{slowdown}_W \times b \qquad (W = \text{DAMP}, \text{WET})
$$

The rain tyre's penalty is then all measured (`pooled`); the other tyres carry a prior gap to it (`prior`). DRY
penalties are all priors (4 s on INTERMEDIATE, 10 s on WET, 0 on slicks). The gaps between tyres in the rain cannot be
measured: cars stay out too long or switch late, so tyre choice and driver choice are mixed up.

---

## What Is Not Fitted

| Prior | Value | Why |
|---|---|---|
| Fuel | 1.9 kg per lap, 0.033 s per kg | Fuel load and lap are the same thing in race data; it cannot be separated from the race trend |
| Cliff severity and cap; cliff age where no stint ran that long | See above | Teams stop before the cliff |
| Warm-up | 0, second-lap share 0.3 | Already inside the measured pit loss (D33) |
| Rain tyre wear, gaps between tyres in rain, DRY penalties of rain tyres | `defaults.yaml` | Selection effects |
| Flag lap noise | 1.0 s | Too few flag laps |

All of them are in `configs/defaults.yaml` and listed as `prior` in each file's `provenance`.
