# Testing Reference Guide

This document describes the testing strategy, evaluation methodology, and execution instructions for Stratex.

## Testing Framework

We use **pytest** for all unit, integration, and regression tests.

## Test Execution Commands

- **Run all tests**: `pytest`
- **Run with verbose output**: `pytest -v`
- **Run a specific test file**: `pytest tests/test_env.py`
- **Run with coverage**: `pytest --cov=src`

## Test Scope

### 1. Environment Unit Tests (`tests/test_env.py`)

- **Tire Reset**: Verify that taking a pit action resets tire age to 0 on the next step.
- **Tire Compound Rules**: Verify that the environment tracks compounds used (bitmask) and enforces the two-compound dry-race rule:
  - Agent cannot finish without using at least 2 different dry compounds.
  - Action masking forces a pit stop if the rule isn't met near race end.
- **Episode Termination**: Verify `terminated=True` on the final lap, and `truncated` is never set (fixed lap count).
- **Reward Bounds**: Check that rewards are negative (lap times are positive) and within realistic limits (e.g., 80–120s for dry, 90–180s for SC/wet).
- **Reward Zeroed During SC**: Verify that reward = 0 during safety car laps (agent has no control over SC pace).
- **Tire Cliff Behavior**: Run a stint past the cliff threshold and verify lap times increase sharply (quadratically, not linearly).
- **Out-Lap Penalty**: Verify the first lap after a pit stop includes the warmup penalty (1–3s depending on compound).
- **Fuel Effect**: Verify that lap times decrease as `laps_remaining` decreases (lighter car = faster laps), at the calibrated rate.
- **Action Masking**: Verify that `action_masks()` returns:
  - `False` for INTER/WET actions in DRY conditions.
  - `False` for STAY_OUT when the two-compound rule must be satisfied and only 1–2 laps remain.
  - `True` for at least one action at every state (no deadlocks).
- **Observation Normalization**: Verify all observation values are in [0, 1] range.

### 2. Dynamics Tests (`tests/test_dynamics.py`)

- **Degradation Formula**: Verify that `tyre_degradation(compound, age)` produces the correct piecewise output:
  - Linear below `cliff_age`.
  - Quadratic above `cliff_age`.
- **Weather×Compound Matrix**: Verify that running slicks in WET conditions produces a massive penalty (~10–15s) and inters in DRY produces an overheating penalty (~3–5s).
- **Fuel Linearity**: Verify `fuel_effect` is approximately `0.033 × fuel_kg_per_lap × laps_remaining`.

### 3. Agent Integration Tests (`tests/test_agents.py`)

- **Random Strategy Baseline**: Ensure a random agent can run through a complete episode without crashes or assertion errors.
- **Baseline Validity**: Verify that the rule-based baseline always satisfies the two-compound rule and produces a complete valid race.
- **Q-Learning Exploration**: Sanity check that epsilon-greedy exploration decays correctly and that the agent explores among *valid* actions only (respects action mask).
- **Agent Beats Random**: After a short training run (~1000 episodes), verify that the trained agent's mean race time is lower than a random agent's. This is a regression test, not a performance benchmark.
- **DQN Target Update**: Verify that the target network updates at the specified interval and that the online and target networks diverge between updates.

## Evaluation Methodology

> [!IMPORTANT]
> All agent evaluations MUST follow this protocol. Single-seed results are meaningless for stochastic environments.

### Paired-Seed Evaluation

Because the environment is stochastic (safety cars, weather), **always evaluate over many episodes/seeds** (minimum 50, ideally 100+).

For fair head-to-head comparisons, use **paired seeds** — run the baseline and the RL agent on the **identical** sequence of scenario draws, so differences reflect strategy quality, not random luck.

```python
seeds = list(range(100))
for seed in seeds:
    baseline_time = run_episode(baseline_agent, seed=seed)
    dqn_time = run_episode(dqn_agent, seed=seed)
    # Same weather, same SC events, different strategy
```

### Reported Metrics

| Metric | When |
|--------|------|
| Mean race time ± std | Phases 1–5 (single car) |
| Mean finishing position ± std | Phase 6+ (multi-car) |
| Pit stop count distribution | Always |
| Compound usage distribution | Always |
| Two-compound rule violation rate | Always (should be 0%) |
| Win rate vs baseline | Phase 6+ |

### Reward Hacking Checks

Always manually inspect full episode traces before trusting a learning curve:

1. **"Never pit" hack**: Does the agent avoid pitting entirely? Check pit count distribution.
2. **"Pit every lap" hack**: Is the pit loss undermodeled? Check mean stops per race.
3. **Single-lap compound trick**: Does the agent pit for a 2nd compound on the very last lap just to satisfy the rule? Check stint lengths.
4. **Safety car exploitation**: Does the agent time pits suspiciously well relative to SC events? Compare pit timing distribution to SC timing.
