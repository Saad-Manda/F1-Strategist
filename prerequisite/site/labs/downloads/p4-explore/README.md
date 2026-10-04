# p4-explore: How does an agent discover an action it currently dislikes?

Python 3.10+; standard library only. Tested with Python 3.12.7.
Extract this archive anywhere. Open PowerShell or another terminal in this folder:

```text
python broken.py
python checks.py --candidate broken.py
python starter.py
python checks.py --candidate starter.py
```

`broken.py` runs but intentionally fails checks. Fix a copy or complete the TODOs in
`starter.py`. The untouched starter exits with “Exercise incomplete”; this is expected.
Pass your own filename to `--candidate`. Tests import only that file and this pack's
helpers; they never import the reference solution or the F1 repository.

## Contract

Implement probabilities(values, legal, epsilon) and select_action(values, legal, epsilon, rng). Include uniform seeded tie-breaking, zero illegal probability, ε endpoints, and invalid-input rejection. rng.random() supplies one draw in [0,1); sample cumulative probabilities in action-index order. The comparison harness trains your selector and then evaluates its frozen table with ε=0.

Functions to implement:

- `probabilities(values, legal, epsilon)`
- `select_action(values, legal, epsilon, rng)`

Inputs are Python lists/numbers as described. Invalid inputs raise `ValueError`.
`exercise_common.py` supplies only validation, model data, and the demo CLI, so focus on
the RL concept. `fixtures.json` holds small hand-calculated examples; checks also use
additional cases. Floating-point comparisons use absolute/relative tolerance 1e-9;
probability normalization uses tolerance 1e-10. Tied optimal actions are both accepted.

Browser computations and Python should agree on exact mathematics. Seeded sampled
paths are reproducible within each implementation: browser uses an LCG, Python uses
`random.Random`, so matching numeric seeds do not imply identical cross-language paths.


## Optional help

Return to the webpage to request individual hints. The file `solution.py` contains the
reference answer; open it only when you want it. To check the reference explicitly:

```text
python checks.py --candidate solution.py
```

Explain and transfer: Explain why the random branch includes the greedy action and why training return differs from frozen greedy evaluation. What exploration schedule, cached state, and Q updates must be disabled or reset during project evaluation?

Optional extension: change one model reward or transition probability. Calculate the
new expected results before running your implementation. Original checks still target
the original model; update your extension's independent witnesses separately.

## Seeded local comparison

Once checks pass, run your candidate:

```text
python compare.py --candidate starter.py --episodes 1000 --seeds 7,31,89 --epsilon 0.2 --alpha 0.1
```

This prints JSON with every seed, final Q tables, training means, evaluation means, and
the mean across seeds for each variant. Evaluation freezes the table and disables
exploration. Policy and observations/rewards use separate random streams. Paired
variants use the same seeds and budgets; trajectories can differ with their policies.
These finite sampled results illustrate learning; no checker requires winning on a
particular seed. Alter epsilon or budget and explain the changes. Browser seed triplets
default to 7,8,9; pass those locally if you want matching seed labels, remembering the
browser LCG and Python random.Random generate different paths.
