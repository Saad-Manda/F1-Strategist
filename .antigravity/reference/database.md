# Data & Storage Reference

Stratex uses static file storage (JSON and Parquet) for calibrated coefficients and scenario libraries. No SQL/NoSQL database is needed.

## Storage Hierarchy

```
data/
├── raw/                 # FastF1 cache files (gitignored)
└── processed/           # Processed datasets and configuration exports
    ├── silverstone/
    │   ├── calibration.json
    │   └── scenarios.parquet
    ├── monza/
    │   ├── calibration.json
    │   └── scenarios.parquet
    └── spa/
        ├── calibration.json
        └── scenarios.parquet
```

## Schema Definitions

### 1. Calibration Configuration (`calibration.json`)

Stores the fitted coefficients for the lap-time transition model. Each parameter is calibrated from real FastF1 data using `scipy.optimize.curve_fit`.

```json
{
  "circuit": "silverstone",
  "total_laps": 52,
  "base_pace": 90.5,
  "pit_loss": 22.5,
  "noise_std": 0.2,

  "fuel": {
    "consumption_kg_per_lap": 1.85,
    "sensitivity_s_per_kg": 0.033
  },

  "compounds": {
    "SOFT": {
      "base_deg": 0.12,
      "cliff_age": 18,
      "cliff_severity": 0.35,
      "warmup_penalty": 1.0
    },
    "MEDIUM": {
      "base_deg": 0.07,
      "cliff_age": 28,
      "cliff_severity": 0.30,
      "warmup_penalty": 1.5
    },
    "HARD": {
      "base_deg": 0.04,
      "cliff_age": 40,
      "cliff_severity": 0.25,
      "warmup_penalty": 2.5
    },
    "INTERMEDIATE": {
      "base_deg": 0.10,
      "cliff_age": 30,
      "cliff_severity": 0.20,
      "warmup_penalty": 1.0
    },
    "WET": {
      "base_deg": 0.06,
      "cliff_age": 40,
      "cliff_severity": 0.15,
      "warmup_penalty": 0.5
    }
  },

  "weather_compound_penalty": {
    "DRY":  { "SOFT": 0.0, "MEDIUM": 0.0, "HARD": 0.0, "INTER": 4.0,  "WET": 10.0 },
    "DAMP": { "SOFT": 6.0, "MEDIUM": 4.0, "HARD": 3.0, "INTER": 0.0,  "WET": 2.5  },
    "WET":  { "SOFT": 15.0,"MEDIUM": 12.0,"HARD": 10.0,"INTER": 3.0,  "WET": 0.0  }
  },

  "safety_car_probability_per_lap": 0.015,
  "safety_car_lap_time": 160.0
}
```

#### Field Descriptions

| Field | Description |
|-------|-------------|
| `base_pace` | Fastest achievable lap time on fresh tires, no fuel, dry conditions (seconds) |
| `pit_loss` | Total time lost entering + stationary + exiting pits vs staying on track (seconds) |
| `noise_std` | Standard deviation of per-lap Gaussian noise (seconds) |
| `fuel.consumption_kg_per_lap` | Fuel burn rate, typically 1.7–2.2 kg/lap |
| `fuel.sensitivity_s_per_kg` | Lap time cost per kg of fuel, typically 0.030–0.035 s/kg |
| `compounds.*.base_deg` | Linear degradation rate in the pre-cliff phase (seconds per tire-age lap) |
| `compounds.*.cliff_age` | Tire age (laps) at which the cliff begins — performance drops sharply after this |
| `compounds.*.cliff_severity` | Quadratic coefficient for post-cliff degradation: `cliff_sev × (age - cliff_age)²` |
| `compounds.*.warmup_penalty` | Out-lap penalty for cold tires (seconds). Softs warm fastest, hards slowest. |
| `weather_compound_penalty` | Matrix of lap-time penalties for running a given compound in a given weather condition. Slicks in WET = massive penalty (aquaplaning). Wets in DRY = overheating penalty. |
| `safety_car_probability_per_lap` | Empirical probability of a safety car deployment on any given lap |
| `safety_car_lap_time` | Fixed lap time during safety car (all cars circulate at ~160s, independent of tires) |

#### Tire Degradation Model

The degradation function uses a piecewise model, not a simple polynomial:

```python
def tyre_degradation(compound, tyre_age, params):
    base_deg = params[compound]["base_deg"]
    cliff_age = params[compound]["cliff_age"]
    cliff_sev = params[compound]["cliff_severity"]

    # Linear phase: gradual degradation
    gradual = base_deg * tyre_age

    # Cliff phase: quadratic blowup after threshold
    cliff = cliff_sev * max(0, tyre_age - cliff_age) ** 2

    return gradual + cliff
```

The cliff is the single most important strategic phenomenon — it's what *creates* the pit stop decision. Without it, staying out indefinitely is always cheaper than the ~22s pit loss.

### 2. Scenario Database (`scenarios.parquet`)

A table containing real historical race events extracted from FastF1. Each simulated episode samples one of these traces as the exogenous backdrop.

| Column | Type | Description |
|--------|------|-------------|
| `race_id` | string | Identifier for the source race (e.g., `"2023_silverstone"`) |
| `lap_number` | int | Lap number within the race |
| `weather_regime` | string | `DRY`, `DAMP`, or `WET` |
| `safety_car_active` | bool | Whether the safety car is deployed on this lap |
| `vsc_active` | bool | Whether the virtual safety car is active |
| `track_temp` | float | Track surface temperature in °C |
| `air_temp` | float | Air temperature in °C |
| `rainfall` | bool | Whether rain is currently falling |

### 3. Agent Checkpoints

Trained agent models are stored in `data/checkpoints/`:

```
data/checkpoints/
├── q_learning/
│   └── silverstone_dry_v1.pkl      # Pickled Q-table
├── dqn/
│   ├── silverstone_v1.pt           # PyTorch model weights
│   └── silverstone_v1_config.yaml  # Hyperparameters used
└── ppo/
    └── silverstone_v1.zip          # SB3 model bundle
```
