# System Architecture

This document describes the high-level architecture, module design, data flow, and key design decisions in the Stratex platform.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    FastF1 Data Ingest                      │
│  Laps (Compound, TyreLife, LapTime, PitInTime/OutTime)   │
│  Weather (AirTemp, TrackTemp, Rainfall)                   │
│  RaceControl (SC, VSC, RedFlag timestamps)                │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│                  Calibration Layer                         │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │ Tyre Deg     │ │ Fuel Effect  │ │ Scenario         │  │
│  │ Curves +     │ │ per Circuit  │ │ Templates        │  │
│  │ CLIFF model  │ │ (kg/lap,     │ │ (historical      │  │
│  │ per compound │ │  s/kg)       │ │  weather + SC    │  │
│  │ per circuit  │ │              │ │  traces)         │  │
│  └─────────────┘ └──────────────┘ └──────────────────┘  │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │ Pit Lane     │ │ Out-Lap      │ │ Weather×Compound │  │
│  │ Time Loss    │ │ Warmup       │ │ Penalty Matrix   │  │
│  │ per circuit  │ │ Penalty      │ │                  │  │
│  └─────────────┘ └──────────────┘ └──────────────────┘  │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│              Gymnasium MDP Environment                    │
│                                                           │
│  lap_time = base_pace                                     │
│           + tyre_deg(compound, age) + CLIFF(age)          │
│           + fuel_effect(laps_remaining)                    │
│           + weather_compound_penalty(regime, compound)     │
│           + out_lap_warmup(laps_since_pit, compound)      │
│           + noise                                         │
│                                                           │
│  Action masking: invalid actions filtered per state       │
│  Obs normalization: all features → [0, 1]                │
│  SC handling: reward = 0 during safety car laps           │
│  Rules: two-compound enforcement via masking + penalty    │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│                     Agent Layer                            │
│  ┌───────────┐ ┌───────────┐ ┌────────────────────────┐ │
│  │ Baseline  │ │ Tabular   │ │ Dueling Double DQN     │ │
│  │ (rule-    │ │ Q-learning│ │ + Prioritized Replay   │ │
│  │  based)   │ │ + SARSA   │ │ + Action masking       │ │
│  │           │ │ (binned   │ │                        │ │
│  │           │ │  states)  │ │                        │ │
│  └───────────┘ └───────────┘ └────────────────────────┘ │
│                                    ▼ (stretch)            │
│                        ┌────────────────────────┐        │
│                        │ MaskablePPO (SB3)      │        │
│                        │ Multi-Agent Self-Play  │        │
│                        └────────────────────────┘        │
└───────────────┬──────────────────────────────────────────┘
                │
                ▼
┌────────────────────┐        ┌────────────────────────────┐
│ FastAPI Backend    │◀──────▶│  React Dashboard           │
│ Race simulation    │        │  Lap-time traces           │
│ Agent trajectories │        │  Q-value decision panel    │
│ Historical replay  │        │  Agent comparison charts   │
│ Paired-seed evals  │        │  Historical counterfactual │
└────────────────────┘        └────────────────────────────┘
```

## Component Details

### 1. Ingestion & Calibration (`src/data/`)

- **`fetch.py`**: Interacts with the FastF1 library. Fetches session-level data (laps with `Compound`, `TyreLife`, `Stint`, `PitInTime`/`PitOutTime`; `weather_data`; `race_control_messages`) and caches raw results locally. Filters using `pick_quicklaps()` plus additional `TrackStatus` filtering for safety car laps.
- **`calibrate.py`**: Performs regression analysis on fuel-corrected clean lap times to fit the transition model parameters per circuit:
  - **Tyre degradation curves with cliff**: Uses `scipy.optimize.curve_fit` with a piecewise model (linear phase + quadratic cliff) — *not* a simple polynomial, which would fail to capture the cliff.
  - **Fuel sensitivity**: Estimated at ~0.033 s/kg/lap (circuit-dependent).
  - **Pit lane time loss**: Computed from `PitInTime`/`PitOutTime` deltas.
  - **Out-lap warmup penalty**: Estimated from the pace difference between first-lap-on-new-tires vs second-lap.
  - **Safety car probability**: Empirical rate per lap per circuit from race control messages.
  - **Weather×compound penalty matrix**: Cross-tabulated from wet-race data.

### 2. Scenario Templates

A key design decision: rather than building a stochastic weather/safety-car Markov chain from scratch, the simulator samples **real historical races** as exogenous backdrops. Each scenario template is a lap-by-lap trace of weather conditions, track temperature, and safety car events extracted from an actual Grand Prix. This keeps randomness grounded in history rather than invented.

### 3. Simulator (`src/env/`)

- **`dynamics.py`**: Implements the full transition dynamics model:
  ```
  lap_time = base_pace(circuit)
           + tyre_degradation(compound, tyre_age)    # includes cliff
           + fuel_effect(laps_remaining)              # ~0.033 s/kg × fuel_kg
           + weather_compound_penalty(regime, compound)  # matrix lookup
           + out_lap_warmup(laps_since_pit, compound) # 1-3s on out-lap
           + noise                                     # ~N(0, 0.2)
  ```
  The **tire cliff** is modeled as a piecewise function: linear degradation up to a compound-specific threshold, then quadratic blowup. This is the phenomenon that *creates* the pit stop decision — without it, gradual degradation is always cheaper than the ~22s pit lane loss.

  The **out-lap penalty** models cold tire warmup (1-3s depending on compound). This is critical for undercut/overcut realism — the undercut works because the car staying out has warm-but-worn tires versus the pitting car's fresh-but-cold tires.

  During **safety car periods**, lap times are replaced with a fixed SC pace. The reward is zeroed during SC laps since the agent has no control over pace — only the pit/stay decision matters.

- **`f1_strategy_env.py`**: Implements the Gymnasium Env interface with:
  - **Action masking** (`action_masks()` method): Invalid actions are masked out per state. For example, INTER/WET tires are invalid in DRY conditions; pitting for the same compound is pointless; if the two-compound rule isn't met near race end, "stay out" is forced off. This prevents wasted exploration and is compatible with SB3's `MaskablePPO`.
  - **Normalized observations**: All features mapped to [0, 1]. Categoricals (compound, weather) are one-hot encoded. `compounds_used_so_far` is a 3-bit bitmask.
  - **Two-compound rule enforcement**: Dual mechanism — action masking prevents invalid endings + terminal penalty as safety net.
  - **`terminated` vs `truncated`**: `terminated=True` when the race ends naturally (final lap); `truncated` is not used since F1 races have fixed lap counts.

### 4. Reinforcement Learning Agents (`src/agents/`)

- **Baselines** (`baseline_agent.py`): Fixed-stop (1-stop or 2-stop plans) and threshold-based heuristic strategists (pit when pace delta exceeds a threshold).
- **Tabular Q-Learning/SARSA** (`q_learning_agent.py`): Bins continuous variables into a manageable table (~518K entries with aggressive binning: `laps_remaining` into 12 bins, `tire_age` into 10 bins, `track_temp` into 3 bins). The full unbinned state space (~43M entries) is too sparse for tabular methods — this binning design is intentional, not an afterthought.
- **Dueling Double DQN** (`dqn_agent.py`): Key improvements over vanilla DQN:
  - **Double DQN**: Uses the online network to *select* actions and the target network to *evaluate* them, fixing the overestimation bias.
  - **Dueling architecture**: Separates V(s) and A(s,a) streams, which is useful because "stay out" is correct ~85% of laps — the advantage of most actions is ~0.
  - **Prioritized Experience Replay (PER)**: Samples transitions proportional to TD error. Pit-stop transitions are 25-50× rarer than "stay out" transitions but are the *only* strategically important decisions. PER ensures they're adequately represented in training batches.
- **PPO** (`ppo_agent.py`, stretch): Via Stable-Baselines3's `MaskablePPO` for action-masked policy gradient training.

### 5. Application Tier (`backend/` & `frontend/`)

- **FastAPI backend** orchestrates simulations, executes policy evaluation on request, and serves race replay data including per-lap Q-values for explainability. Supports paired-seed evaluation (run multiple agents on identical scenario sequences).
- **React dashboard** displays comparative charts (Baseline vs. Q-Learning vs. DQN), a visual race replay with compound color coding and pit markers, a Q-value decision panel showing *why* the agent chose each action, and a historical counterfactual view comparing agent strategy vs. what actually happened.

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| γ = 1.0 for single-car phases | Fixed-length episodes (fixed lap count) make γ=1.0 safe. γ < 1.0 biases against late-race pace — at γ=0.97 over 52 laps, lap 50 is weighted 4.6× less than lap 1. |
| Scenario templates over parametric weather | Keeps stochastic elements grounded in real historical data. Avoids inventing a weather Markov chain. |
| Action masking over penalty-only | Prevents wasted exploration of nonsensical actions (wet tires on dry track). Compatible with MaskablePPO. |
| Dueling Double DQN over vanilla DQN | Double DQN fixes overestimation bias (3-line change). Dueling helps because "stay out" dominates. Zero additional compute cost. |
| PER over uniform replay | Pit decisions are 25-50× rarer but are the only decisions that matter. Uniform sampling starves the network of critical transitions. |
| Piecewise tire cliff over polynomial fit | Polynomials can't capture the sudden cliff. The cliff is what *creates* the pit stop decision — without it the agent has no reason to pit. |

## Prior Art & References

| Work | Relevance |
|------|-----------|
| TUMFTM/race-simulation (TU Munich, GitHub) | Monte Carlo race simulation with VSE. Benchmark for validation. |
| arXiv:2501.04068 — Explainable RL for F1 Strategy (RSRL) | Feature importance + decision tree surrogates for explainability. Informs dashboard design. |
| arXiv:2602.23056 — Multi-Agent Race Strategies | Self-play training for multi-agent F1 strategy. Validates Phase 8 approach. |
| Heilmeier et al. — Race Simulation for Strategy Decisions | Probabilistic overtaking model, SC modeling. Reference for Phase 6. |
| Ng, Harada & Russell 1999 — Potential-Based Reward Shaping | Provably policy-preserving shaping. Informs Phase 6 reward design. |
