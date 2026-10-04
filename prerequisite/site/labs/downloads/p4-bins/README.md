# p4-bins: Can more episodes recover a distinction your bins erased?

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

Implement bin_index(x, edges) with strictly increasing edges beginning at 0 and ending at 1; preserve the right-hand boundary convention and keep x=1 in the last valid bin. Implement table_size(bin_counts, actions=2), returning states, entries, bytes for float64 payload. Reject invalid observations, edges, counts, and action counts. The comparison script uses your encoder to train coarse, split, and nonuniform tables.

Functions to implement:

- `bin_index(x, edges)`
- `table_size(bin_counts, actions=2)`

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

Explain and transfer: Explain the endpoint convention and why a coarse policy’s ceiling cannot improve with more training. Which neighbouring project observations need different actions, and how would you test their encodings before judging a learning curve?

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
