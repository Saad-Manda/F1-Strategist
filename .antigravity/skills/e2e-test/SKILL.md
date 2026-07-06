# E2E Test Skill

Orchestration rules for running parallel subagents to conduct E2E tests.

## Usage Guidelines

1. Define subagents using `define_subagent` and assign them roles (e.g. Test Executor, Test Reporter).
2. Run subagents concurrently with shared workspace setting (`Workspace: 'share'`).
3. Collect and consolidate test logs and report final outcomes.
