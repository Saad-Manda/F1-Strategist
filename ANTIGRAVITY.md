# ANTIGRAVITY Constitution & Project Guidelines

This file is the single source of truth for Stratex's architecture, stack, conventions, and rules.

## Project Overview

**Stratex** is an F1 Pit & Tire Strategy Reinforcement Learning Agent. The system calibrates tire degradation models (including the cliff effect), fuel sensitivity, and safety car probabilities from real historical F1 data (via FastF1), simulates races using a custom Gymnasium MDP environment with action masking and normalized observations, trains RL agents (tabular Q-learning/SARSA, Dueling Double DQN with Prioritized Experience Replay, MaskablePPO) to optimize tire strategies, and visualizes the races and agent decision-making (Q-values, action masks) through a FastAPI + React dashboard.

## Tech Stack

- **Languages**: Python (>= 3.10), JavaScript/HTML/CSS
- **Frameworks**: FastAPI (Backend), React (Frontend), Gymnasium (Simulation Env)
- **Libraries**:
  - RL & Math: PyTorch, Stable-Baselines3 + sb3-contrib (MaskablePPO), NumPy
  - Data & Calibration: FastF1, pandas, scipy (curve fitting), PyYAML
  - Visualization: matplotlib, seaborn, TensorBoard
  - Testing: pytest, httpx (FastAPI test client)
- **Deployment**: Local execution (runs on laptop CPU; RTX 4050 optional bonus)

## Commands

- **Install Dependencies**: `pip install -r requirements.txt` (backend) & `npm install` (frontend)
- **Run Backend**: `uvicorn backend.main:app --reload`
- **Run Frontend**: `npm run dev` (inside `frontend/`)
- **Run Tests**: `pytest`
- **Run Tests (verbose)**: `pytest -v`
- **Launch TensorBoard**: `tensorboard --logdir=runs/`
- **Run Notebooks**: `jupyter lab` (from project root)

## Project Structure

```
stratex/ (Workspace Root)
├── .antigravity/             # Antigravity automation, reference docs, templates
│   └── reference/            # API, architecture, database, testing specs
├── configs/                  # Circuit configs, agent hyperparams (YAML)
├── data/
│   ├── raw/                 # FastF1 cache (gitignored)
│   ├── processed/           # Calibration params, scenario templates
│   └── checkpoints/         # Trained agent model files
├── docs/
│   └── idea.md              # Master project plan and learning roadmap
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_calibration.ipynb
│   └── 03_agent_comparison.ipynb
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── fetch.py         # FastF1 wrappers + caching
│   │   └── calibrate.py     # Tyre-deg cliff fitting, SC-rate estimation
│   ├── env/
│   │   ├── f1_strategy_env.py  # Gymnasium MDP with action masking
│   │   └── dynamics.py      # Lap-time model (cliff, fuel, warmup, weather×compound)
│   ├── agents/
│   │   ├── baseline_agent.py
│   │   ├── q_learning_agent.py  # + SARSA
│   │   ├── dqn_agent.py     # Dueling Double DQN + PER
│   │   └── ppo_agent.py     # stretch (via SB3 MaskablePPO)
│   └── evaluation/
│       └── evaluate.py      # Paired-seed evaluation framework
├── backend/
│   └── main.py              # FastAPI application
├── frontend/                 # React dashboard
├── tests/
│   ├── test_env.py          # Environment + action masking tests
│   ├── test_dynamics.py     # Tire cliff, fuel, weather×compound tests
│   └── test_agents.py       # Agent integration + regression tests
├── runs/                    # TensorBoard log directory
├── PRD.md                   # Product Requirements Document
├── requirements.txt
└── README.md
```

## Architecture

The system has 5 layers. See `.antigravity/reference/architecture.md` for full details.

- **Data Layer (FastF1)**: Ingests lap telemetry, tire compound histories, weather data, and race control messages for safety cars and VSC events.
- **Calibration Layer**: Fits transition model parameters from real data:
  - **Tire degradation with cliff**: Piecewise model — linear phase (`base_deg × age`) + quadratic cliff (`cliff_sev × (age - cliff_age)²`). The cliff is what *creates* the pit stop decision.
  - **Fuel effect**: Linear model (~0.033 s/kg, ~1.9 kg/lap consumption).
  - **Out-lap warmup penalty**: Compound-dependent (SOFT ~1s, HARD ~2.5s).
  - **Weather×compound penalty matrix**: Cross-tabulated interaction (slicks in wet = massive penalty; wets in dry = overheating).
  - **Scenario templates**: Real historical races as exogenous backdrops (weather + SC traces).
- **Simulator (Gymnasium MDP)**:
  - **State** (16 normalized features): `laps_remaining`, `tire_compound` (one-hot, 5d), `tire_age`, `weather_regime` (one-hot, 3d), `track_temp`, `safety_car_active`, `compounds_used` (bitmask, 3d), `mandatory_pit_needed`. All in [0, 1].
  - **Action** (6 discrete, masked): `STAY_OUT`, `PIT_SOFT`, `PIT_MEDIUM`, `PIT_HARD`, `PIT_INTER`, `PIT_WET`. Invalid actions masked per state.
  - **Reward**: `-lap_time` per step (dense, aligned with true objective). Zero during SC laps. Terminal penalty for two-compound rule violation.
  - **Discount**: γ = 1.0 for single-car phases (fixed-length episodes make this safe; γ < 1.0 biases against late-race pace).
- **Agent Layer**: Baselines (rule-based), Tabular Q-learning/SARSA (aggressively binned, ~518K entries), Dueling Double DQN with PER, MaskablePPO (stretch, via SB3).
- **Presentation Layer**: FastAPI serves race replays with Q-values + action masks to a React dashboard. Supports paired-seed agent comparison and historical counterfactual replays.

## Code Patterns

- **Config-Driven**: All circuit calibrations and agent hyperparameters in YAML files under `configs/`. No hardcoded constants in source.
- **Typing & Docs**: Use Python type hints and detailed docstrings throughout `src/`.
- **Seed Everything**: Always seed `numpy`, `torch`, `gymnasium`, and `random` for reproducibility.
- **Paired-Seed Evaluation**: Run head-to-head agent comparisons on identical scenario sequences. Report mean ± std over 50+ seeds, never a single run.
- **Action Masking**: All agents must respect `action_masks()`. Tabular agents explore only among valid actions. DQN masks Q-values of invalid actions to `-inf`.
- **Normalized Observations**: All env features in [0, 1]; categoricals one-hot encoded; bitmask for compounds used.

## Testing

- Framework: `pytest`
- Test files in `tests/`: `test_env.py`, `test_dynamics.py`, `test_agents.py`
- Test coverage must include:
  - Tire cliff behavior (sharp increase past cliff threshold).
  - Out-lap warmup penalty application.
  - Fuel effect (lap times decrease as fuel burns off).
  - Action masking correctness (no INTER/WET in DRY; forced pit for two-compound rule).
  - Reward = 0 during safety car laps.
  - Observation bounds in [0, 1].
  - Agent regression: trained agent beats random policy.
- See `.antigravity/reference/testing.md` for the full evaluation methodology including paired-seed protocol and reward hacking checks.

## Validation

- Run `pytest` before every commit.
- Manually inspect full episode traces before trusting learning curves (check for reward hacking).
- Verify pit count distribution, compound usage, and two-compound rule compliance.
- Visual verification of simulated trajectories on the React dashboard.

## Key Files

- `src/env/f1_strategy_env.py`: Custom Gym Environment with action masking and normalized observations.
- `src/env/dynamics.py`: Lap-time transition model (cliff + fuel + warmup + weather×compound).
- `src/data/calibrate.py`: Curve fitting for tire degradation cliff parameters from FastF1 data.
- `docs/idea.md`: Master project roadmap and RL learning plan.
- `.antigravity/reference/architecture.md`: Full architecture with design decision rationale.
- `.antigravity/reference/database.md`: Calibration schema with all parameter definitions.

## On-Demand Context

- **FastF1 Data**: `src/data/fetch.py` wraps FastF1; cache stored in `data/raw/`. Filter with `pick_quicklaps()` + `TrackStatus` for SC laps.
- **Agent Training**: Run training scripts from `src/agents/`. Logs go to `runs/` for TensorBoard. Checkpoints saved to `data/checkpoints/`.
- **Prior Art**: TUMFTM/race-simulation (GitHub), arXiv:2501.04068 (Explainable RL for F1), arXiv:2602.23056 (Multi-Agent F1 Strategy).

## Notes

- **FastF1 Disclaimer**: FastF1 is an unofficial, community-built library, not an official FIA/F1 data product. Standard practice in this space.
- **RL Reproducibility**: RL is notoriously run-to-run variable. Never trust a single seed's result. Always report mean ± std over 50+ paired seeds.
- **This project is designed for portfolio/interview demonstration**. The MDP design, real-data calibration, paired-seed evaluation, and Q-value explainability are the defensible signals, not just "I used DQN."
- **2018 FastF1 data** can be spotty. Start with 2019+ for reliable coverage.
