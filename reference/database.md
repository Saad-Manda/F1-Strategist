# Database & Storage Reference

PitGenius is designed to run locally without a heavy SQL/NoSQL database engine. Instead, it relies on static file storage in structured formats (JSON and Parquet) for calibrated coefficients and scenario libraries.

## Storage Hierarchy

```
data/
├── raw/                 # FastF1 cache files
└── processed/           # Processed datasets and configuration exports
    ├── silverstone/
    │   ├── calibration.json
    │   └── scenarios.parquet
    └── monza/
        ├── calibration.json
        └── scenarios.parquet
```

## Schema Definitions

### 1. Calibration Configuration (`calibration.json`)
Stores the fitted coefficients for the lap-time transition model:
```json
{
  "circuit": "silverstone",
  "base_pace": 90.5,
  "pit_loss": 22.5,
  "compounds": {
    "SOFT": {
      "base_deg": 0.15,
      "exponent": 1.2
    },
    "MEDIUM": {
      "base_deg": 0.08,
      "exponent": 1.1
    },
    "HARD": {
      "base_deg": 0.04,
      "exponent": 1.05
    }
  },
  "safety_car_probability_per_lap": 0.015
}
```

### 2. Scenario Database (`scenarios.parquet`)
A table containing real historical race events (such as lap-by-lap weather changes and safety car deployments).
Columns:
- `race_id` (string)
- `lap_number` (int)
- `weather_regime` (string: DRY, DAMP, WET)
- `safety_car_active` (boolean)
- `track_temp` (float)
