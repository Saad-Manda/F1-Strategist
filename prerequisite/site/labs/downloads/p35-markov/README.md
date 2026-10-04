# p35-markov: Can a forecast equal knowing the future?

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

Implement advance(distribution, matrix), sample_next(state, rng, matrix), and decision_values(state, matrix). The RNG supplies random() in [0,1). Validate all probability rows and shapes. decision_values returns expected scores for NONE and UMBRELLA. Check distribution arithmetic and categorical samples using the supplied seeded checks.

Functions to implement:

- `advance(distribution, matrix)`
- `sample_next(state, rng, matrix)`
- `decision_values(state, matrix)`

Inputs are Python lists/numbers as described. Invalid inputs raise `ValueError`.
`exercise_common.py` supplies only validation, model data, and the demo CLI, so focus on
the RL concept. `fixtures.json` holds small hand-calculated examples; checks also use
additional cases. Floating-point comparisons use absolute/relative tolerance 1e-9;
probability normalization uses tolerance 1e-10. Tied optimal actions are both accepted.

Browser computations and Python should agree on exact mathematics. Seeded sampled
paths are reproducible within each implementation: browser uses an LCG, Python uses
`random.Random`, so matching numeric seeds do not imply identical cross-language paths.
The weather checker uses 10,000 independent draws for each of three seeds per row,
with explicit frequency tolerance 0.02; it also checks categorical boundaries exactly.


## Optional help

Return to the webpage to request individual hints. The file `solution.py` contains the
reference answer; open it only when you want it. To check the reference explicitly:

```text
python checks.py --candidate solution.py
```

Explain and transfer: Explain row versus column multiplication, why samples vary, and why perfect foresight is only a bound. Describe how you would keep an evaluation oracle from observing randomness unavailable to your agent.

Optional extension: change one model reward or transition probability. Calculate the
new expected results before running your implementation. Original checks still target
the original model; update your extension's independent witnesses separately.
