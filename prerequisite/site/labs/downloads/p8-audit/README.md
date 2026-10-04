# p8-audit

Python 3.10+; NumPy, PettingZoo and Gymnasium.
Extract anywhere. All files are standalone; no repository or backend required.

```text
python -m pip install -r requirements.txt
python broken.py
python checks.py --candidate broken.py
python starter.py
python checks.py --candidate starter.py
```

Broken code runs but fails checks. Untouched starter reports Exercise incomplete.
Implement TODOs or repair a copy; pass its filename to --candidate. Checks never
import solution.py. Open that optional reference only when you request help.

## Contract

Implement schedule(scenarios, opponents, master_seed) with explicit scenario/opponent IDs and stable per-scenario seeds; paired_scores(rows_a, rows_b) matching unique scenario IDs; experience(vector_envs, vector_steps) counting transitions; parallel_round(env, actions) submitting the exact live-agent set once; and aec_round(env, actions) using each selected agent’s own flags and None cleanup. The pack supplies a real PettingZoo one-round RPS environment and its AEC conversion. Validate IDs, budgets and actions.

- `schedule(scenarios, opponents, master_seed)`
- `paired_scores(rows_a, rows_b)`
- `experience(vector_envs, vector_steps)`
- `parallel_round(env, actions)`
- `aec_round(env, actions)`

Floating comparisons use 1e-9; normalized probability rows use 1e-10. Invalid
inputs described above raise ValueError. Seeded frequency checks use 10,000 draws
for seeds 7,19,31, with tolerance .02. Browser and Python RNGs are different;
identical seeds reproduce within each implementation, not between languages.
Counterfactuals and exact payoffs are model calculations, not measured training.
No test requires a learner to outperform a baseline on a lucky seed.

Tested locally: Python 3.12.7, NumPy 2.5.1, Gymnasium 1.3.0 and PettingZoo 1.27.0
(only install the packages listed in this pack's requirements). The audit's tiny
constant observation and A/B names trigger official API-test recommendations;
the lifecycle assertions still pass. These recommendations are not suppressed.

After checks, run `python compare.py --candidate starter.py` for actual Parallel/AEC and official API tests.

Explain and transfer: List what a fair evaluation fixes and what it measures. Explain the shuffled-pairing statistic, joint transitions versus per-agent calls, hidden commitments and selected-agent cleanup.
