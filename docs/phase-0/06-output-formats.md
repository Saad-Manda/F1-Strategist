# Phase 0: Output Data Formats

Phase 0 generates two output files per circuit, written to `data/processed/{circuit_name}/`:

---

## 1. `calibration.json`

A JSON document containing all calibrated parameters for the circuit's lap-time simulation model.

### Full Schema

```json
{
  "circuit": "silverstone",
  "total_laps": 52,
  "base_pace": 90.34,
  "pit_loss": 18.3,
  "noise_std": 0.20,
  "fuel": {
    "consumption_kg_per_lap": 1.9,
    "sensitivity_s_per_kg": 0.033
  },
  "compounds": {
    "SOFT": {
      "base_deg": 0.0363,
      "cliff_age": 27.2,
      "cliff_severity": 0.0329,
      "warmup_penalty": 1.0
    },
    "MEDIUM": {
      "base_deg": 0.0326,
      "cliff_age": 33.1,
      "cliff_severity": 0.2681,
      "warmup_penalty": 1.5
    },
    "HARD": {
      "base_deg": 0.0341,
      "cliff_age": 32.0,
      "cliff_severity": 0.4439,
      "warmup_penalty": 2.5
    },
    "INTERMEDIATE": {
      "base_deg": 0.05,
      "cliff_age": 28.0,
      "cliff_severity": 0.30,
      "warmup_penalty": 1.0
    },
    "WET": {
      "base_deg": 0.03,
      "cliff_age": 38.0,
      "cliff_severity": 0.25,
      "warmup_penalty": 0.5
    }
  },
  "weather_compound_penalty": {
    "DRY":  { "SOFT": 0.0, "MEDIUM": 0.0, "HARD": 0.0, "INTER": 4.0, "WET": 10.0 },
    "DAMP": { "SOFT": 6.0, "MEDIUM": 4.0, "HARD": 3.0, "INTER": 0.0, "WET": 2.5  },
    "WET":  { "SOFT": 15.0, "MEDIUM": 12.0, "HARD": 10.0, "INTER": 3.0, "WET": 0.0 }
  },
  "safety_car_probability_per_lap": 0.0897,
  "safety_car_lap_time": 160.0
}
```

### Field Reference

#### Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `circuit` | string | Circuit identifier (matches the config `name`) |
| `total_laps` | int | Scheduled race distance in laps |
| `base_pace` | float (seconds) | The reference lap time — 5th percentile of all fuel-corrected MEDIUM laps. All penalties are added on top of this. |
| `pit_loss` | float (seconds) | The empirically estimated median total time lost per pit stop (pit-lane traversal + stop time, net of warmup penalty) |
| `noise_std` | float (seconds) | Standard deviation of Gaussian lap-time noise to be injected in the simulator. Fixed at 0.20 s (domain knowledge). |

#### `fuel` Object

| Field | Type | Description |
|---|---|---|
| `consumption_kg_per_lap` | float | Fuel burn rate per lap (1.9 kg/lap) |
| `sensitivity_s_per_kg` | float | Lap time improvement per kg of fuel burned (0.033 s/kg) |

#### `compounds` Object

For each compound (`SOFT`, `MEDIUM`, `HARD`, `INTERMEDIATE`, `WET`):

| Field | Type | Description |
|---|---|---|
| `base_deg` | float (s/lap) | Linear degradation rate per lap — how many seconds slower the car gets with each additional lap on this compound under normal wear |
| `cliff_age` | float (laps) | The tyre age at which exponential degradation begins — the "cliff" |
| `cliff_severity` | float | Quadratic coefficient controlling how steeply lap times rise beyond the cliff age |
| `warmup_penalty` | float (seconds) | Fixed lap-time penalty on the first lap of a stint (tyre warm-up) |

**Using these to compute lap time penalty for a given tyre age $t$:**

$$\text{deg}(t) = \text{base\_deg} \cdot t + \text{cliff\_severity} \cdot \max(0, t - \text{cliff\_age})^2$$

#### `weather_compound_penalty` Object

A nested lookup table: `weather_compound_penalty[weather_regime][compound]` gives the additional lap time penalty (in seconds) for running that compound in that weather condition. Zero means it is the optimal compound for those conditions.

#### Safety Car Fields

| Field | Type | Description |
|---|---|---|
| `safety_car_probability_per_lap` | float | Empirical fraction of driver-laps during which a Safety Car was active |
| `safety_car_lap_time` | float (seconds) | Fixed lap time under Safety Car conditions — approximately 160s, regardless of circuit |

---

## 2. `scenarios.parquet`

A Parquet table encoding lap-by-lap race scenario templates derived from real historical races.

**Purpose:** The RL training environment samples from these templates to initialize races from realistic conditions rather than always starting from a fixed clean-weather, no-SC baseline.

### Schema

| Column | Type | Description |
|---|---|---|
| `LapNumber` | int | Lap number in the race (1 to `total_laps`) |
| `weather_regime` | string | `"DRY"`, `"DAMP"`, or `"WET"` — the classified weather condition on this lap |
| `TrackTemp` | float | Track surface temperature (°C) |
| `AirTemp` | float | Ambient air temperature (°C) |
| `Rainfall` | bool | True if rain was recorded on this lap |
| `sc_active` | bool | True if Safety Car was active on this lap |
| `vsc_active` | bool | True if Virtual Safety Car was active on this lap |
| `race_id` | string | Identifies the source race (e.g., `"2022_silverstone"`, `"2021_monza"`) |

### Row Count

Each race contributes `total_laps` rows. For 3 seasons, the file contains `3 × total_laps` rows per circuit (e.g., `3 × 52 = 156` rows for Silverstone).

### How It Is Used by the Simulator

During RL training, the Gym environment (`Phase 1`) selects one `race_id` at random to replay. It uses the lap-by-lap `weather_regime`, `sc_active`, and `vsc_active` columns from that scenario to drive the environment's state transitions, ensuring the agent is exposed to a realistic mix of dry races, damp conditions, safety cars, and VSC periods.
