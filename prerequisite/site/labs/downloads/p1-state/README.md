# p1-state: Can identical observations hide different futures?

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

Implement encode_state(mode, remaining=None). Return mode for the continuing switch, or the tuple (mode, remaining) for an intrinsic finite-horizon variant. Reject invalid modes and negative/non-integer horizons. The supplied world uses the encoder in each transition trace.

Functions to implement:

- `encode_state(mode, remaining=None)`

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

Explain and transfer: Give the two histories that disprove sufficiency of the broken observation. Explain when remaining time belongs in state. For your project, identify a variable whose omission would change future reward or transition distributions.

Optional extension: change one model reward or transition probability. Calculate the
new expected results before running your implementation. Original checks still target
the original model; update your extension's independent witnesses separately.
