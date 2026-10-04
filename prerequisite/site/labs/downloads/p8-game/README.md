# p8-game

Python 3.10+, standard library only.
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

Implement payoff(learner, opponent) for integer actions 0,1,2; expected_payoff(policy, opponent) for normalized nonnegative length-three distributions; action_update(values, action, reward, alpha) updating only the chosen entry; and best_response(opponent) returning all maximizing indices. Reject malformed distributions, invalid actions and α outside [0,1].

- `payoff(learner, opponent)`
- `expected_payoff(policy, opponent)`
- `action_update(values, action, reward, alpha)`
- `best_response(opponent)`

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

After checks, run `python compare.py --candidate starter.py --seed 7`.

Explain and transfer: Explain pure versus mixed strategies and exact versus sampled evaluation. Why does a fixed-opponent win fail to demonstrate equilibrium?
