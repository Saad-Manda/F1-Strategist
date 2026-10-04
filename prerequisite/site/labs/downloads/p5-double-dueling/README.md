# p5-double-dueling

Python 3.10+; NumPy and CPU PyTorch.
Tested: Python 3.12.7, NumPy 2.5.1, PyTorch 2.13.0+cpu.
Extract anywhere; no repository or backend is required. Use an existing PyTorch
installation or install requirements. All tensors run on CPU.

```text
python -m pip install -r requirements.txt
python broken.py
python checks.py --candidate broken.py
python starter.py
python checks.py --candidate starter.py
```

The broken candidate runs and deliberately fails checks. The untouched starter
reports Exercise incomplete. Repair a copy or implement TODOs; pass its filename
to --candidate. Checks import that candidate and helpers, never solution.py.
Reference solution.py is optional help: open only when you request it.

## Contract

Implement detached double_targets with online/target/boolean legal arrays [B,A], rewards/boolean terminated [B], returning [B]. Select using online legal values, gather from target. Terminal rows may have no legal successor; nonterminal rows may not. Implement differentiable dueling(V[B,1], A[B,A]) with row-wise centering. Reject nonfinite values, malformed shapes/flags and γ outside [0,1].

- `double_targets(online_values, target_values, rewards, terminated, legal, gamma)`
- `dueling(value, advantage)`

Float64 tensors (NumPy float arrays for PER) make hand witnesses reproducible.
Invalid inputs described above raise ValueError. Hand examples use tolerance 1e-9;
analytic SGD checks use 1e-10. Sampling checks use 10,000 draws for each seed
7,19,31 with frequency tolerance .02. Sampling is with replacement; Python and
browser RNGs do not generate identical traces. Scores are not correctness gates.



Explain and transfer: Explain selection versus evaluation, derive both targets, prove common-offset invariance and locate legal masks in a batched update.
