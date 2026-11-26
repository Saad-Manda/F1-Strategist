# Stratex — F1 Pit & Tire Strategy RL Agent

> **Disclaimer**: This project uses [FastF1](https://github.com/theOehrly/Fast-F1), an unofficial, community-built library for accessing Formula 1 timing data. It is not an official FIA or Formula 1 data product.

Stratex is a reinforcement learning platform that solves the F1 pit stop and tire compound optimization problem. It calibrates tyre pace and wear, pit loss, safety cars and rain from 2021-2024 race data (FastF1 and OpenF1), says which numbers are measured and which are assumed (such as the tyre **cliff**), simulates races inside a custom Gymnasium MDP environment, and trains intelligent strategist agents that learn *when* to pit and *which* compound to choose.

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
│            Data Ingest (FastF1 + OpenF1)                 │
│  Laps, Compounds, TyreLife, Weather, Track status        │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│                  Calibration Layer                       │
│  Tyre pace & wear │ Pit loss │ SC & weather chains       │
│  Real-race traces │ Checks K1-K9 before anything trains  │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│              Gymnasium MDP Environment                   │
│  lap_time = base + deg + CLIFF + fuel + weather×compound │
│           + out_lap_warmup + noise                       │
│  Action masking · Normalized obs · Sampled SC & rain     │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│  Agents: Baseline │ Q-Learning/SARSA │ Dueling DDQN+PER  │
│                   │                  │ MaskablePPO (SB3) │
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
- **Rich Dynamics Model**: Compound pace and wear, a capped tyre cliff, fuel burn-off, weather×compound penalties (slicks in rain = massive penalty), and safety cars and rain drawn lap by lap from calibrated chains, with cheaper pit stops under SC and VSC.
- **Action Masking**: Invalid actions (wet tires on dry track, violating two-compound rule) are filtered out — agents never waste time exploring nonsensical moves.
- **Explainable Decisions**: Dashboard shows Q-values and action masks at every lap — you can see *why* the agent chose to pit, not just that it did.
- **Statistical Evaluation**: Paired-seed comparisons over 50+ seeds. Mean ± std reporting, not cherry-picked single runs.
- **Counterfactual Replay**: Compare the agent's strategy side-by-side with what actually happened in a historical Grand Prix.

## What Is Measured and What Is Assumed

`python -m src.calibration.run` writes `data/processed/<circuit>/calibration.json` for five circuits (Silverstone,
Monza and Spa, best run as 1-stop races; Hungaroring and Barcelona, 2-stop) and refuses to write anything if one of
the checks K1-K9 fails. Every number carries its source:

- **Fitted per circuit**: base pace, lap-time noise, green pit loss.
- **Pooled over 2021-2024 races of many circuits**: the dry tyre pattern (each circuit scales its wear), the pit loss
  share under SC and VSC, the safety car and weather chains, flag lap times, and how much slower the rain tyres are.
- **Assumed (prior)**: the tyre cliff (teams stop before it, so the data only shows it comes no earlier than the
  longest stints), gaps between tyres in the rain, rain tyre wear, fuel effect.

The 2025 season is held out of all fitting. Full documentation: [`docs/phase-0/`](docs/phase-0/index.md); every number
recomputed step by step: `notebooks/02_calibration.ipynb`.

## Repo Structure

```
stratex/
├── configs/                  # Circuit & agent configuration (YAML)
├── data/
│   ├── raw/                 # FastF1 cache and OpenF1 JSON (not tracked)
│   ├── interim/             # Frozen races, one parquet folder each (not tracked)
│   ├── processed/           # calibration.json + scenarios.parquet per circuit
│   └── checkpoints/         # Trained model files (planned)
├── src/
│   ├── common/              # Strict config loader, errors, calibration file schema
│   ├── data/                # Raw FastF1/OpenF1 files -> frozen parquet races
│   ├── calibration/         # Race conditions, models, checks, the calibration run
│   ├── env/                 # Race dynamics (built); Gymnasium MDP (planned)
│   ├── agents/              # Baseline, Q-learning, DQN, PPO (planned)
│   └── evaluation/          # Paired-seed evaluation framework (planned)
├── backend/                  # FastAPI backend (planned)
├── frontend/                 # React dashboard (planned)
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

# Frontend (once it exists, Phase 2)
# cd frontend && npm install && cd ..
```

### Running
```bash
# Data and calibration
python -m src.data.ingest          # raw files -> data/interim/ (offline)
python -m src.calibration.run      # -> data/processed/<circuit>/; exits non-zero if a check fails

# Tests
pytest                             # fast tests; pytest -m slow for the rest

# Planned, not working yet
uvicorn backend.main:app --reload  # Phase 2
cd frontend && npm run dev         # Phase 2

# Tests
pytest

# TensorBoard (training logs)
tensorboard --logdir=runs/
```

## MDP Design

The intellectual heart of the project — designing this well matters more than any algorithm choice. The race dynamics are built (`src/env/dynamics.py`); the Gymnasium environment around them is Phase 1.

| Component | Design |
|-----------|--------|
| **State** | 16 features, all in [0, 1]. The exact Markov state: `laps_to_go`, compound (one-hot, 5), `tyre_age`, weather (one-hot DRY/DAMP/WET), SC active, VSC active, two-compound rule still to meet. Plus three shortcuts computed from it: current degradation, current pit loss, cliff proximity. No track temperature (it would not change any lap time) and no compounds-used bitmask (one rule bit is enough). |
| **Action** | 6 discrete, masked: `STAY_OUT`, `PIT_SOFT/MEDIUM/HARD/INTER/WET`. The mask allows only tyres that fit the weather, no stop on the final lap, and forces a legal stop when the rule is still unmet with two laps to go. |
| **Reward** | `-lap_time` on **every** lap, safety car laps included, so the return is minus the race time. A pit stop's loss is added to the lap it is made on. A terminal penalty exists only as a backstop for code that ignores the mask. |
| **Dynamics** | `base_pace + compound offset + wear + capped cliff + warm-up + fuel + weather×compound + noise`; under SC or VSC the lap is the flag lap time. Pit loss is cheaper under SC (0.68x) and VSC (0.62x). |
| **Exogenous** | Track status (GREEN/SC/VSC) and weather (DRY/DAMP/WET) are drawn each lap from Markov chains counted from real races. |
| **Discount** | γ = 1.0 (fixed-length episodes; avoids late-race bias) |
