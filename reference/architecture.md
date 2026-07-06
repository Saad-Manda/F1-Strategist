# System Architecture

This document describes the high-level architecture, module design, and flow of data in the PitGenius platform.

## Architecture Diagram
```
┌──────────────────┐
│   FastF1 Ingest  │  Downloads telemetry, tyre logs, weather, safety cars.
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│Calibration Layer │  Fits lap-time & degradation curves; exports parameters.
└────────┬─────────┘
         │ (parameters.json, scenarios)
         ▼
┌──────────────────┐
│ Gymnasium Sim    │  Simulates laps, computes deg, fuel weight, safety car delays.
└────────┬─────────┘
         │ (MDP actions / observations)
         ▼
┌──────────────────┐
│  RL Agents (RL)  │  Q-learning, SARSA, DQN, PPO decide when to pit.
└────────┬─────────┘
         │ (simulated trajectories)
         ▼
┌──────────────────┐
│ FastAPI Backend  │  Exposes REST endpoints to trigger & fetch simulations.
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ React Dashboard  │  Plots degradation, lap times, and shows agent logic.
└──────────────────┘
```

## Component Details

### 1. Ingestion & Calibration (`src/data/`)
- **`fetch.py`**: Interacts with the FastF1 API. Fetches session-level data and caches raw results locally.
- **`calibrate.py`**: Performs regression analysis on clean lap times (filtering out safety car and in/out laps) to estimate base pace, degradation coefficients per compound, pit lane time loss, and safety car probability distribution.

### 2. Simulator (`src/env/`)
- **`dynamics.py`**: Implements the deterministic and stochastic transition dynamics formulas (lap time as a function of tyre age, compound, fuel burn-off, weather penalty, and safety car status).
- **`f1_strategy_env.py`**: Implements the Gymnasium Env interface. Manages episodes representing full races, tracks tyre age/compounds used, and enforces F1 rules (like using two dry compounds).

### 3. Reinforcement Learning Agents (`src/agents/`)
- **Baselines**: Fixed-stop (e.g. 1-stop or 2-stop) and threshold-based heuristic strategists.
- **Tabular Q-Learning/SARSA**: Bins continuous variables (laps remaining, tyre age) and maintains a discrete Q-table.
- **DQN**: A PyTorch MLP predicting Q-values from raw observation inputs, trained using an experience replay buffer and target networks.

### 4. Application Tier (`backend/` & `frontend/`)
- FastAPI acts as the orchestrator, initializing environments and executing policy evaluation on request.
- React frontend presents comparative charts (DQN vs. Tabular vs. Heuristic) and a visual replay board.
