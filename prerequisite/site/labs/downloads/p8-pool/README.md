# p8-pool

Python 3.10+; NumPy.
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

Implement snapshot(policy) returning an independent read-only NumPy array; add_snapshot(pool, policy, capacity) returning a bounded pool without mutating its input; pool_probabilities(weights) normalizing positive finite weights; and sample_indices(weights, count, seed) using NumPy’s seeded generator. Validate distributions, capacities and counts. Implement coverage(policy) against all three pure opponents.

- `snapshot(policy)`
- `add_snapshot(pool, policy, capacity)`
- `pool_probabilities(weights)`
- `sample_indices(weights, count, seed)`
- `coverage(policy)`

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



Explain and transfer: Explain checkpoint independence, immutability, eviction and sampling separately. What opponent coverage can reveal forgetting that latest-only evaluation misses?
