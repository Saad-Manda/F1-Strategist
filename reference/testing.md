# Testing Reference Guide

This document describes the testing strategy, test locations, and execution instructions for PitGenius.

## Testing Framework
We use **pytest** to write and run unit, integration, and regression tests.

## Test Execution Commands
- **Run all tests**: `pytest`
- **Run with verbose output**: `pytest -v`
- **Run a specific test file**: `pytest tests/test_env.py`

## Test Scope

### 1. Environment Unit Tests (`tests/test_env.py`)
- **Tire Reset**: Verify that taking a pit action resets tire age to 0.
- **Tire Compound Rules**: Verify that the environment tracks the compounds used so far and enforces the requirement to use at least two different dry compounds.
- **Episode Termination**: Verify that the episode terminates on the final lap.
- **Reward Bounds**: Check that rewards are negative and within realistic limits (e.g. typical lap times).

### 2. Agent Integration Tests (`tests/test_agents.py`)
- **Random Strategy Baseline**: Ensure a random agent can run through a complete episode without crashes or logic errors.
- **Q-Learning Exploration**: Sanity check that epsilon-greedy exploration decays correctly during training steps.
- **Agent Performance Check**: Run a quick validation check that a simple trained agent runs faster or equals the time of a random agent.
