# API Reference

The PitGenius backend exposes REST endpoints via FastAPI to serve simulation data and agent trajectories to the frontend dashboard.

## Endpoints

### 1. Run Simulation / Replay
* **Endpoint**: `GET /race/{circuit}/{seed}`
* **Description**: Runs a simulated race on the specified circuit under the given random seed using a chosen strategist agent/policy.
* **Parameters**:
  - `circuit` (string): Circuit name (e.g., `'silverstone'`, `'monza'`).
  - `seed` (int): Random seed to control safety car and weather events.
  - `agent_type` (query string): `'baseline'`, `'q_learning'`, `'dqn'`, or `'ppo'`.
* **Response**:
  ```json
  {
    "circuit": "silverstone",
    "seed": 42,
    "agent_type": "dqn",
    "total_race_time": 5420.5,
    "laps": [
      {
        "lap_number": 1,
        "compound": "MEDIUM",
        "tyre_age": 1,
        "lap_time": 93.4,
        "action_taken": "STAY_OUT",
        "safety_car": false,
        "weather": "DRY",
        "q_values": {
          "STAY_OUT": -93.4,
          "PIT_SOFT": -118.2,
          "PIT_MEDIUM": -118.5,
          "PIT_HARD": -119.0
        }
      }
      // ... subsequent laps
    ]
  }
  ```

### 2. Get Available Circuits
* **Endpoint**: `GET /circuits`
* **Description**: Returns the list of calibrated circuits and available scenario templates.
* **Response**:
  ```json
  {
    "circuits": ["silverstone", "monza", "spa"]
  }
  ```
