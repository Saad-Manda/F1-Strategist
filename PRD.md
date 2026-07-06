# Product Requirements Document (PRD) — PitGenius

## 1. Product Overview
**PitGenius** is an AI strategist tool for F1 Pit & Tire Strategy optimization. Using Reinforcement Learning models trained on historical F1 data, PitGenius simulates F1 races lap-by-lap and learns optimal pit stop decisions (when to pit and which tire compound to choose). It features a visual dashboard allowing users to analyze race replays, compare different strategist agents, and explore "what-if" counterfactual scenarios of real historical Grand Prix races.

## 2. Goals & Objectives
- **Simulate realistic F1 races** using historical data from FastF1 to model tire degradation, pit lane loss, safety cars, and weather changes.
- **Beat rule-based strategist baselines** by at least 1-2 seconds in average race time over a series of seeds.
- **Visualize agent decision making**: Expose state representations, value functions (Q-values), and decision logs to provide full transparency of the agent's strategy.
- **Compare multiple RL algorithms**: Support Tabular Q-learning, SARSA, DQN, and PPO.

## 3. Core Features & Phases

### Phase 0: Data Foundation & Calibration
- Ingest race data (laps, tyre age, weather, safety cars) using FastF1 API.
- Calibrate tire degradation curves, track empirical safety car probabilities, and record pit stop time losses for selected circuits.
- Export calibration parameters as JSON/parquet files.

### Phase 1: Gym Environment Simulator
- Implement a custom Gymnasium environment (`F1StrategyEnv`) following standard Farama conventions.
- Model the race as an MDP:
  - **State**: `laps_remaining`, `tire_compound`, `tire_age`, `weather_regime`, `track_temp`, `safety_car_active`, and `compounds_used_so_far` (two-compound rule check).
  - **Action**: Stay out or pit to Soft, Medium, Hard, Intermediate, or Wet.
  - **Reward**: dense `-lap_time` penalty per lap.
- Validate simulator using random and fixed strategies.

### Phase 2: Dashboard Skeleton (FastAPI + React)
- Setup a FastAPI backend that runs simulations and returns step-by-step race results.
- Setup a React frontend dashboard showing lap times, compounds, and pit stops.

### Phase 3: Rule-Based Baseline Strategist
- Implement standard strategies (e.g. fixed 1-stop/2-stop, threshold-based pace delta).
- Run baseline across multiple seeds to establish benchmark race times.

### Phase 4: Tabular Q-Learning & SARSA Agent
- Implement discrete state binning for continuous features.
- Train Q-learning (off-policy) and SARSA (on-policy) agents.
- Compare learning rates and policies on dry, no-safety-car scenario libraries.

### Phase 5: DQN (Deep Q-Network)
- Implement DQN in PyTorch to bypass state binning.
- Implement experience replay buffer and target networks.
- Evaluate DQN against tabular Q-learning and baseline.

### Phase 6: Multi-Car Environment & Rivals
- Extend the simulator to N cars, adding `position`, `gap_to_car_ahead`, and `gap_to_car_behind` to the state.
- Add simple overtaking dynamics (probabilistic pass based on pace delta and dirty air penalty).
- Design and evaluate shaped rewards for multi-car competition.

### Phase 7: Historical Replays & Explainability
- Run the best trained RL agent against historical race scenarios.
- Display a side-by-side comparison of the actual historical race strategy and the agent's optimized strategy.
- Display visual explanations of the agent's choices (e.g., live Q-value bars for each action).

## 4. Technical Constraints
- The entire stack must run efficiently on a standard laptop CPU.
- Experience replay memory limits and neural network size must be optimized for fast training.
- Simulation and learning seeds must be pinned for deterministic results.
