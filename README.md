# PitGenius — F1 Pit & Tire Strategy RL Agent

PitGenius is a reinforcement learning platform designed to solve the F1 pit stop and tire compound optimization problem. By calibrating pace models and tire degradation curves against real-world telemetry (via FastF1), PitGenius simulates races inside a custom Gym MDP environment and trains intelligent strategist agents.

A FastAPI backend serves race simulations and agent decision trails (Q-values) to an interactive React dashboard.

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│   FastF1 data    │────▶│  Calibration      │────▶│  Simulator (Gym    │
│  (real races)    │     │  layer            │     │  environment)      │
│  laps, tyres,    │     │  tyre-deg curves, │     │  MDP: state/action/│
│  weather, SC     │     │  SC rates, pit    │     │  reward/transition │
│  events          │     │  loss, scenario   │     │                    │
│                  │     │  templates        │     │                    │
└─────────────────┘     └────────┬─────────┘     └─────────┬──────────┘
                                 │                         │
                                 ▼                         ▼
                        ┌──────────────────┐     ┌───────────────────┐
                        │ FastAPI backend  │◀───▶│  React dashboard  │
                        │ race replays     │     │  race replay,     │
                        │ agent decisions  │     │  agent logic      │
                        └──────────────────┘     └───────────────────┘
```

## Features

- **Real-Data Calibration**: Model tire degradation and safety car rates from actual F1 session data.
- **Gymnasium MDP Simulator**: Accurate lap-time updates based on tire age, fuel burn, track temp, weather, and safety cars, enforcing the official F1 two-compound tire rule.
- **Explainable Decisions**: Inspect agent evaluation parameters (Q-values) for each lap decision.
- **Counterfactual Replay**: Compare the RL agent's decisions side-by-side with historical race decisions.

## Repo Structure

```
pitgenius/
├── configs/                  # Circuit & agent configuration files
├── data/
│   ├── raw/                 # FastF1 cache
│   └── processed/           # Calibration params, scenario templates
├── src/
│   ├── data/fetch.py         # FastF1 ingestion
│   ├── data/calibrate.py     # Tire degradation curve fitting
│   ├── env/f1_strategy_env.py# Gymnasium MDP environment
│   ├── env/dynamics.py       # Lap-time physics and weather models
│   ├── agents/               # Rule-based, Q-learning, DQN & PPO agents
│   └── evaluation/           # Performance comparisons & analytics
├── backend/                  # FastAPI backend
├── frontend/                 # React dashboard UI
├── tests/                    # Pytest suite
└── reference/                # Architectural & API reference guides
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js (for React frontend)

### Installation
1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

### Running the App
1. Start the backend:
   ```bash
   uvicorn backend.main:app --reload
   ```
2. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

### Running Tests
Execute:
```bash
pytest
```
