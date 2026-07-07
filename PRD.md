# Product Requirements Document (PRD) — Stratex

## 1. Product Overview

**Stratex** is an AI strategist tool for F1 Pit & Tire Strategy optimization. Using Reinforcement Learning models trained on historical F1 data, Stratex simulates F1 races lap-by-lap and learns optimal pit stop decisions (when to pit and which tire compound to choose). It features a visual dashboard allowing users to analyze race replays, compare different strategist agents, explore agent decision logic (Q-values, action masks), and run "what-if" counterfactual scenarios against real historical Grand Prix races.

## 2. Goals & Objectives

- **Simulate realistic F1 races** using historical data from FastF1 to model tire degradation (including the cliff effect), fuel burn-off, pit lane loss, out-lap warmup, safety cars, and weather-compound interactions.
- **Beat rule-based strategist baselines** by a statistically significant margin in mean race time over 50+ paired seeds (not a single run).
- **Visualize agent decision making**: Expose state representations, Q-values, and action masks at each lap decision to provide full transparency of the agent's strategy.
- **Compare multiple RL algorithms**: Support Tabular Q-learning, SARSA, Dueling Double DQN (with PER), and MaskablePPO.

## 3. Core Features & Phases

### Phase 0: Data Foundation & Calibration (~3–5 days)
- Ingest 2–4 seasons of race data for 2–4 circuits via FastF1 (laps with `Compound`, `TyreLife`, `Stint`, `PitInTime`/`PitOutTime`; `weather_data`; race control messages).
- Compute fuel-corrected lap times (subtract estimated fuel effect before fitting degradation).
- Fit **piecewise tire degradation curves with cliff** per compound per circuit using `scipy.optimize.curve_fit` — not simple polynomials.
- Calibrate: fuel sensitivity (s/kg), pit lane time loss, out-lap warmup penalty, safety car probability per lap, weather×compound penalty matrix.
- Extract **scenario templates** (lap-by-lap weather + SC traces from real races).
- Export as `calibration.json` + `scenarios.parquet` per circuit.
- **Definition of done**: EDA notebook with degradation curves (showing cliff), SC-rate plots; at least ~10 scenario templates per circuit.

### Phase 1: Gym Environment Simulator (~3–5 days)
- Implement `F1StrategyEnv(gym.Env)` following Farama Gymnasium conventions.
- **Transition dynamics**:
  ```
  lap_time = base_pace + tyre_deg(compound, age) + CLIFF(age)
           + fuel_effect(laps_remaining)
           + weather_compound_penalty(regime, compound)
           + out_lap_warmup(laps_since_pit, compound)
           + noise
  ```
- **State** (16 normalized features, all in [0, 1]):
  - `laps_remaining / total_laps`
  - `tire_compound` (one-hot, 5 dims)
  - `tire_age / max_age`
  - `weather_regime` (one-hot, 3 dims: dry/damp/wet)
  - `track_temp` (normalized)
  - `safety_car_active` (binary)
  - `compounds_used` (3-bit bitmask for dry compounds)
  - `mandatory_pit_needed` (binary: still need 2nd compound?)
- **Action** (6 discrete, masked): `STAY_OUT | PIT_SOFT | PIT_MEDIUM | PIT_HARD | PIT_INTER | PIT_WET`.
- **Action masking**: `action_masks()` filters invalid actions per state (no INTER/WET in DRY; forced pit for two-compound rule near race end; no same-compound pit).
- **Reward**: `-lap_time` per step. Zero during safety car laps. Terminal penalty for two-compound rule violation.
- **Discount**: γ = 1.0 (safe for fixed-length episodes; avoids late-race pace bias).
- Validate with `stable_baselines3.common.env_checker.check_env()`.
- **Definition of done**: Env registered with Gymnasium; passes `check_env`; at least 10 pytest tests covering tire cliff, out-lap penalty, fuel effect, action masking, reward bounds, observation normalization, and episode termination.

### Phase 2: Dashboard Skeleton (~2–3 days)
- Minimal FastAPI backend with `GET /race/{circuit}/{seed}` returning a lap-by-lap replay.
- Minimal React frontend animating the replay: lap-time trace, tyre-compound color coding, pit-stop markers.
- Feed random/fixed policies from Phase 1 — no trained agent yet.
- **Definition of done**: Open dashboard locally and watch a simulated race play out.

### Phase 3: Rule-Based Baseline Strategist (~1–2 days)
- Implement reactive baselines: fixed 1-stop/2-stop plans, threshold-based pace delta trigger.
- Wire into dashboard.
- **Definition of done**: Baseline produces sensible strategies; race-time distribution (mean ± std over 50+ seeds) recorded as benchmark.

### Phase 4: Tabular Q-Learning & SARSA (~4–6 days)
- **State binning**: Aggressively discretize to ~518K table entries (12 bins for laps_remaining, 10 for tire_age, 3 for track_temp). The unbinned state space (~43M entries) is too sparse.
- Implement masked ε-greedy exploration (explore only among valid actions from `action_masks()`).
- Starting hyperparams: α=0.1, γ=1.0, ε decaying 1.0 → 0.05 over first 50% of training.
- **Curriculum learning**: Start on dry, no-SC scenario subsets. Expand to full library after convergence.
- Train both Q-learning (off-policy) and SARSA (on-policy) for comparison.
- **Definition of done**: Learning curve plateauing; trained agent beats baseline mean race time on 50+ paired seeds; Q-learning vs SARSA comparison plotted; agent visible in dashboard.

### Phase 5: Dueling Double DQN (~3–5 days)
- Implement in PyTorch:
  - **Double DQN**: Online network selects actions, target network evaluates — fixes overestimation bias.
  - **Dueling architecture**: Separate V(s) and A(s,a) streams — helps because "stay out" dominates (~85% of decisions).
  - **Prioritized Experience Replay (PER)**: Sample proportional to TD error — pit transitions are 25-50× rarer than "stay out" but strategically critical.
  - **Action masking**: Set Q-values of masked actions to `-inf` before argmax.
- Small MLP: 2 hidden layers × 128 units. Replay buffer ~100K. Batch 64. LR 1e-3 → 1e-4.
- **Definition of done**: Three-way comparison (baseline vs Q-learning vs DQN) over 100 paired seeds. DQN at least matches tabular performance (not beating it on this small problem is a legitimate finding).

### Phase 6: Multi-Car Environment & Rivals (~3–5 days)
- Extend env to N cars. Add `gap_to_car_ahead`, `gap_to_car_behind`, `position` to state.
- **Overtaking model**: Probabilistic pass when pace delta > 0.5s/lap and gap < 1.0s for multiple laps. **Dirty air penalty**: 0–0.5s when within 1.5s of car ahead.
- **Reward redesign** — test 2–3 designs:
  1. Dense `-lap_time` + terminal position bonus.
  2. Per-lap gap-change (risky: may push tires too hard for short-term gap closure).
  3. Potential-based shaping (Ng et al. 1999) with Φ(s) = -position × constant.
- **Definition of done**: DQN agent trained against N rule-based rivals; dashboard shows multi-car race with positions; write-up comparing reward designs.

### Phase 7: Dashboard Polish & Historical Comparison (~3–5 days)
- Full multi-car replay, Q-value decision panel ("what the agent was thinking"), agent comparison charts.
- **Historical counterfactual**: Pick a real Grand Prix, let the agent re-strategize it, show side-by-side with actual result.
- Write the README properly (problem statement, architecture diagram, learning-curve plot, results table, design decision narration).
- **Definition of done**: Shareable, screenshot/GIF-worthy dashboard; polished README.

## 4. Stretch Goals

### Phase 8: Multi-Agent Self-Play (stretch)
- Multiple learning DQN agents racing each other.
- **Independent learners** as the pragmatic starting point (each car runs its own DQN).
- Self-play with **checkpoint pool**: Save policy every 1000 episodes. Sample opponents with recency bias (70% recent, 30% historical) to prevent forgetting.
- PettingZoo for formalized multi-agent API.
- **Definition of done**: Emergent undercut/overcut patterns arising naturally from training (not programmed).

### Phase 9: PPO via Stable-Baselines3 (stretch)
- Train **MaskablePPO** from `sb3-contrib` — PPO with native action masking support.
- Compare against DQN on the same multi-car benchmark.
- **Definition of done**: PPO vs DQN comparison; writeup on when to build from scratch vs use a library.

## 5. Engineering Practices

- **Config-driven**: Circuit calibration and agent hyperparameters in YAML, never hardcoded.
- **Type hints and docstrings** throughout `src/`.
- **Seed everything**: `numpy`, `torch`, `gymnasium`, `random`. Never trust a single seed.
- **Pinned versions**: `requirements.txt` with exact version pins for reproducibility.
- **pytest coverage**: Environment tests (cliff, masking, rewards), dynamics tests, agent regression tests.
- **TensorBoard logging**: Training curves, Q-value distributions, episode statistics logged to `runs/`.
- **Optional**: GitHub Actions running `pytest` on push.

## 6. Evaluation Methodology

- **Paired seeds**: Run all agents on identical scenario sequences. Differences reflect strategy quality, not scenario luck.
- **Report mean ± std** over 50+ seeds (ideally 100+), never a single best run.
- **Reward hacking checks**: Manually inspect episode traces. Watch for: never-pit, pit-every-lap, single-lap compound trick, suspiciously-timed SC pits.
- **Common pitfalls**:
  1. Rising learning curve ≠ good strategy. Agent may be exploiting a simulator flaw.
  2. Epsilon decaying too fast locks agent into mediocre early strategy.
  3. Unnormalized observations break DQN (features with larger magnitude dominate gradients).
  4. A strategy that wins in simulation but violates the two-compound rule is invalid.

## 7. Timeline Estimate

| Phase | Effort | Cumulative |
|-------|--------|-----------|
| Phase 0 (Data) | 3–5 days | 3–5 days |
| Phase 1 (Env) | 3–5 days | 6–10 days |
| Phase 2 (Dashboard skeleton) | 2–3 days | 8–13 days |
| Phase 3 (Baseline) | 1–2 days | 9–15 days |
| Phase 4 (Q-learning/SARSA) | 4–6 days | 13–21 days |
| Phase 5 (DQN) | 3–5 days | 16–26 days |
| Phase 6 (Multi-car) | 3–5 days | 19–31 days |
| Phase 7 (Polish) | 3–5 days | 22–36 days |
| Phase 8 (Self-play, stretch) | Open-ended | — |
| Phase 9 (PPO, stretch) | Open-ended | — |
