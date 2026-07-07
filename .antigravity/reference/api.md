# API Reference

The Stratex backend exposes REST endpoints via FastAPI to serve simulation data and agent trajectories to the frontend dashboard.

## Base URL

```
http://localhost:8000
```

## Endpoints

### 1. Run Simulation / Replay

* **Endpoint**: `GET /race/{circuit}/{seed}`
* **Description**: Runs a simulated race on the specified circuit under the given random seed using a chosen strategist agent. Returns the complete lap-by-lap trajectory including agent decision data.
* **Path Parameters**:
  - `circuit` (string): Circuit name (e.g., `"silverstone"`, `"monza"`, `"spa"`).
  - `seed` (int): Random seed controlling scenario template selection (safety car timing, weather events).
* **Query Parameters**:
  - `agent_type` (string, required): One of `"baseline"`, `"q_learning"`, `"sarsa"`, `"dqn"`, or `"ppo"`.
  - `baseline_strategy` (string, optional): For baseline agent only — `"one_stop"`, `"two_stop"`, or `"threshold"`. Default: `"one_stop"`.
* **Response**:
  ```json
  {
    "circuit": "silverstone",
    "seed": 42,
    "agent_type": "dqn",
    "total_race_time": 5420.5,
    "total_laps": 52,
    "pit_stops": 1,
    "compounds_used": ["MEDIUM", "HARD"],
    "two_compound_rule_satisfied": true,
    "laps": [
      {
        "lap_number": 1,
        "compound": "MEDIUM",
        "tyre_age": 1,
        "lap_time": 93.4,
        "fuel_effect": 3.18,
        "tyre_deg": 0.07,
        "weather": "DRY",
        "safety_car": false,
        "action_taken": "STAY_OUT",
        "action_mask": [true, true, true, true, false, false],
        "q_values": {
          "STAY_OUT": -93.4,
          "PIT_SOFT": -118.2,
          "PIT_MEDIUM": -118.5,
          "PIT_HARD": -117.0,
          "PIT_INTER": null,
          "PIT_WET": null
        }
      }
    ]
  }
  ```
  - `q_values`: Per-action Q-value estimates. `null` for masked (invalid) actions.
  - `action_mask`: Boolean array — `true` = valid action, `false` = masked out.

### 2. Compare Agents on Paired Seeds

* **Endpoint**: `GET /race/{circuit}/compare`
* **Description**: Runs multiple agents on the **same** sequence of scenario seeds for statistically fair comparison. Returns summary statistics (mean, std, min, max race time) per agent.
* **Query Parameters**:
  - `agents` (string, comma-separated): e.g., `"baseline,q_learning,dqn"`.
  - `n_seeds` (int, default 50): Number of paired seeds to evaluate.
* **Response**:
  ```json
  {
    "circuit": "silverstone",
    "n_seeds": 50,
    "results": {
      "baseline": {
        "mean_race_time": 5480.2,
        "std_race_time": 45.3,
        "min_race_time": 5390.1,
        "max_race_time": 5620.4
      },
      "dqn": {
        "mean_race_time": 5425.8,
        "std_race_time": 38.1,
        "min_race_time": 5370.5,
        "max_race_time": 5540.2
      }
    }
  }
  ```

### 3. Historical Counterfactual Replay

* **Endpoint**: `GET /race/{circuit}/{race_id}/historical`
* **Description**: Loads a real historical Grand Prix's scenario template and runs the specified agent against it. Returns the agent's strategy alongside the actual historical strategy for comparison.
* **Path Parameters**:
  - `circuit` (string): Circuit name.
  - `race_id` (string): Historical race identifier (e.g., `"2023_silverstone"`).
* **Query Parameters**:
  - `agent_type` (string, required): Agent to use for the counterfactual.
  - `driver` (string, optional): Historical driver to compare against (default: race winner).
* **Response**: Same structure as endpoint 1, plus an additional `historical` field containing the real driver's lap-by-lap data.

### 4. Get Available Circuits

* **Endpoint**: `GET /circuits`
* **Description**: Returns the list of calibrated circuits, their parameters, and available scenario template counts.
* **Response**:
  ```json
  {
    "circuits": [
      {
        "name": "silverstone",
        "total_laps": 52,
        "pit_loss": 22.5,
        "scenario_count": 12,
        "compounds_available": ["SOFT", "MEDIUM", "HARD"]
      }
    ]
  }
  ```

### 5. Get Available Agents

* **Endpoint**: `GET /agents`
* **Description**: Returns the list of available trained agent checkpoints and their metadata.
* **Response**:
  ```json
  {
    "agents": [
      {
        "type": "dqn",
        "circuit": "silverstone",
        "version": "v1",
        "training_episodes": 5000,
        "mean_race_time": 5425.8,
        "checkpoint_path": "data/checkpoints/dqn/silverstone_v1.pt"
      }
    ]
  }
  ```
