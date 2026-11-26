# Stratex — F1 Pit & Tire Strategy RL Agent

> **Disclaimer**: This project uses [FastF1](https://github.com/theOehrly/Fast-F1), an unofficial, community-built library for accessing Formula 1 timing data. It is not an official FIA or Formula 1 data product.

Stratex is a reinforcement learning platform that solves the F1 pit stop and tire compound optimization problem. It calibrates tyre pace and wear, pit loss, safety cars and rain from 2021-2024 race data via FastF1 (and says which numbers are measured and which are assumed, such as the tyre **cliff**), simulates races inside a custom Gymnasium MDP environment, and trains intelligent strategist agents that learn *when* to pit and *which* compound to choose.

A FastAPI backend serves race simulations and agent decision trails (Q-values, action masks) to an interactive React dashboard, enabling historical counterfactual analysis ("what if the agent had strategized this Grand Prix?").

## The Problem

In Formula 1, tire strategy is one of the few areas where teams can gain or lose significant time. A strategist must decide:
- **When** to pit (trading ~22 seconds of pit lane time loss for fresh tires)
- **Which compound** to switch to (softer = faster but degrades sooner; harder = slower but lasts longer)
- **How to react** to safety cars (which make a pit stop cheaper) and weather changes

This is hard because tires degrade non-linearly (the "cliff" — a sudden, dramatic grip loss), safety cars are unpredictable, and the optimal strategy depends on what rivals are doing. Stratex models this as a Markov Decision Process and trains RL agents to solve it.

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    FastF1 Data Ingest                      │
│  Laps, Compounds, TyreLife, Weather, Safety Cars          │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│                  Calibration Layer                         │
│  Tyre deg CLIFF model │ Fuel effect │ Scenario templates  │
│  Out-lap warmup       │ Pit loss    │ Weather×Compound    │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│              Gymnasium MDP Environment                    │
│  lap_time = base + deg + CLIFF + fuel + weather×compound │
│           + out_lap_warmup + noise                        │
│  Action masking · Normalized obs · SC reward handling     │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│  Agents: Baseline │ Q-Learning/SARSA │ Dueling DDQN+PER │
│                    │                  │ MaskablePPO (SB3) │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌────────────────────┐        ┌────────────────────────────┐
│ FastAPI Backend    │◀──────▶│  React Dashboard           │
│ Simulations        │        │  Lap traces, Q-values      │
│ Paired-seed evals  │        │  Agent comparison          │
│ Historical replay  │        │  Historical counterfactual │
└────────────────────┘        └────────────────────────────┘
```

## Key Features

- **Real-Data Calibration**: Tyre pace and wear, pit loss, safety car and weather chains measured from 2021-2024 races, with every number labelled fitted, pooled or prior (see below).
- **Rich Dynamics Model**: Fuel burn-off, compound-dependent out-lap warmup penalty, weather×compound interaction matrix (slicks in rain = massive penalty), safety car reward handling.
- **Action Masking**: Invalid actions (wet tires on dry track, violating two-compound rule) are filtered out — agents never waste time exploring nonsensical moves.
- **Explainable Decisions**: Dashboard shows Q-values and action masks at every lap — you can see *why* the agent chose to pit, not just that it did.
- **Statistical Evaluation**: Paired-seed comparisons over 50+ seeds. Mean ± std reporting, not cherry-picked single runs.
- **Counterfactual Replay**: Compare the agent's strategy side-by-side with what actually happened in a historical Grand Prix.

## What Is Measured and What Is Assumed

`python -m src.calibration.run` writes `data/processed/<circuit>/calibration.json` and refuses to write anything if a
check fails. Every number carries its source:

- **Fitted per circuit**: base pace, lap-time noise, green pit loss.
- **Pooled over 2021-2024 races of many circuits**: the dry tyre pattern (each circuit scales its wear), the pit loss
  share under SC and VSC, the safety car and weather chains, flag lap times, and how much slower the rain tyres are.
- **Assumed (prior)**: the tyre cliff (teams stop before it, so the data only shows it comes no earlier than the
  longest stints), gaps between tyres in the rain, rain tyre wear, fuel effect.

The 2025 season is held out of all fitting. See `notebooks/02_calibration.ipynb` and `docs/phase-0/08-remediation.md`.

## Repo Structure

```
stratex/
├── configs/                  # Circuit & agent configuration (YAML)
├── data/
│   ├── raw/                 # FastF1 cache
│   ├── processed/           # Calibration params, scenario templates
│   └── checkpoints/         # Trained model files
├── src/
│   ├── common/              # Strict config loader, errors, calibration file schema
│   ├── data/                # Raw FastF1/OpenF1 files -> frozen parquet races
│   ├── calibration/         # Race conditions, models, checks, the calibration run
│   ├── env/                 # Gymnasium MDP + dynamics model
│   ├── agents/              # Baseline, Q-learning, DQN, PPO
│   └── evaluation/          # Paired-seed evaluation framework
├── backend/                  # FastAPI backend
├── frontend/                 # React dashboard
├── notebooks/                # EDA, calibration, comparison notebooks
└── tests/                    # pytest suite
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js (for React frontend)

### Installation
```bash
# Clone the repository
git clone <repo-url>
cd stratex

# Install Python dependencies
pip install -r requirements.txt

# Set up frontend
cd frontend && npm install && cd ..
```

### Running
```bash
# Data and calibration
python -m src.data.ingest          # raw files -> data/interim/ (offline)
python -m src.calibration.run      # -> data/processed/<circuit>/; exits non-zero if a check fails

# Backend
uvicorn backend.main:app --reload

# Frontend (in a separate terminal)
cd frontend && npm run dev

# Tests
pytest

# TensorBoard (training logs)
tensorboard --logdir=runs/
```

## MDP Design

The intellectual heart of the project — designing this well matters more than any algorithm choice.

| Component | Design |
|-----------|--------|
| **State** | 16 normalized features: `laps_remaining`, `tire_compound` (one-hot), `tire_age`, `weather` (one-hot), `track_temp`, `safety_car`, `compounds_used` (bitmask), `mandatory_pit_needed`. All in [0, 1]. |
| **Action** | 6 discrete, masked: `STAY_OUT`, `PIT_SOFT/MED/HARD/INTER/WET`. Invalid actions filtered per state. |
| **Reward** | Dense `-lap_time` per step. = `-total_race_time` over an episode. Zero during SC laps. Terminal penalty for rule violation. |
| **Dynamics** | `base_pace + tyre_deg (with cliff) + fuel + weather×compound + out_lap_warmup + noise` |
| **Discount** | γ = 1.0 (fixed-length episodes; avoids late-race bias) |
