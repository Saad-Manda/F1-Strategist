# ANTIGRAVITY Constitution & Project Guidelines

This file is the single source of truth for PitGenius's architecture, stack, conventions, and rules.

## Project Overview
**PitGenius** is an F1 Pit & Tire Strategy Reinforcement Learning Agent. The system calibrates tire degradation and safety car models from real historical F1 data (via FastF1), simulates races using a custom Gymnasium environment, trains RL agents (tabular Q-learning/SARSA, DQN, PPO) to optimize tire strategies, and visualizes the races and agent decision-making processes through a FastAPI + React dashboard.

## Tech Stack
- **Languages**: Python (>= 3.10), JavaScript/HTML/CSS
- **Frameworks**: FastAPI (Backend), React (Frontend), Gymnasium (Simulation Env)
- **Libraries**:
  - RL & Math: PyTorch, Stable-Baselines3 (optional), NumPy
  - F1 Data: FastF1
- **Deployment**: Local execution (runs on laptop CPU)

## Commands
- **Install Dependencies**: `pip install -r requirements.txt` (backend) & `npm install` (frontend)
- **Run Backend**: `uvicorn backend.main:app --reload`
- **Run Frontend**: `npm run dev` (inside frontend directory)
- **Run Tests**: `pytest`

## Project Structure
```
pitgenius/ (Workspace Root)
├── .antigravity/             # Antigravity automation settings
├── configs/                  # circuit configs, agent hyperparams (YAML)
├── data/
│   ├── raw/                 # FastF1 cache
│   └── processed/           # calibration params, scenario templates (JSON/parquet)
├── docs/
│   └── idea.md              # Project plan and roadmap
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_calibration.ipynb
│   └── 03_agent_comparison.ipynb
├── src/
│   ├── data/fetch.py         # FastF1 wrappers + caching
│   ├── data/calibrate.py     # tyre-deg curve fitting, SC-rate estimation
│   ├── env/f1_strategy_env.py
│   ├── env/dynamics.py       # lap-time model
│   ├── agents/baseline_agent.py
│   ├── agents/q_learning_agent.py
│   ├── agents/dqn_agent.py
│   ├── agents/ppo_agent.py   # stretch
│   └── evaluation/evaluate.py
├── backend/main.py            # FastAPI backend
├── frontend/                  # React frontend
├── tests/
│   ├── test_env.py
│   └── test_agents.py
├── reference/                # Spec documents
│   ├── api.md
│   ├── architecture.md
│   ├── database.md
│   └── testing.md
├── PRD.md                    # Product Requirements Document
├── requirements.txt
└── README.md
```

## Architecture
- **Data Layer (FastF1)**: Ingests lap telemetry, tire compound histories, and race control messages.
- **Calibration Layer**: Fits tire degradation curves per compound, calculates empirical safety car probabilities, and extracts real weather traces as static templates.
- **Simulator (Gymnasium)**: Models a race lap-by-lap as an MDP. State space tracks laps remaining, compound, tire age, weather, track temp, safety car status, and compounds used (compulsory two dry compound rule). Action space allows staying out or pitting for any compound.
- **Agent Layer**: Baselines (rule-based) and RL agents (tabular Q-learning/SARSA, DQN, PPO).
- **Presentation Layer**: FastAPI serves race replays and Q-value / agent decision traces to a React dashboard.

## Code Patterns
- **Config-Driven**: Keep all circuit calibrations and agent hyperparameters in YAML files under `configs/`.
- **Typing & Docs**: Use Python type hints and detailed docstrings throughout `src/`.
- **Seed Everything**: Always seed `numpy`, `torch`, and the Gym environments to ensure reproducibility.
- **Evaluation**: Run head-to-head agent comparisons using paired seeds to isolate performance from random scenario differences.

## Testing
- Framework: `pytest`
- Run tests in the `tests/` directory.
- Test coverage must include:
  - Simulator environment sanity checks (tyre-age resets on pits, reward sign correctness, race termination).
  - Agent regression tests.

## Validation
- Run `pytest` before commits.
- Perform visual verification of simulated trajectories on the React dashboard.

## Key Files
- `src/env/f1_strategy_env.py`: Custom Gym Environment modeling the MDP.
- `src/env/dynamics.py`: The lap-time transition model.
- `docs/idea.md`: Project roadmap and learning plan.
