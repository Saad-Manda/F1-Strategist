# p5-per

Python 3.10+; NumPy.
Tested: Python 3.12.7, NumPy 2.5.1.
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

Implement probability/global-normalized weight vectors, maximum raw insertion priority (1 for an empty buffer), abs(error)+epsilon updates, and arithmetic mean of weighted per-item losses. Use NumPy arrays. Reject nonpositive/nonfinite priorities, α/β outside [0,1], nonpositive epsilon, mismatched loss/weight vectors, negative losses or weights outside [0,1].

- `distribution(raw_priorities, alpha, beta)`
- `new_priority(raw_priorities)`
- `update_priority(td_error, epsilon=1e-6)`
- `weighted_loss(losses, weights)`

Float64 tensors (NumPy float arrays for PER) make hand witnesses reproducible.
Invalid inputs described above raise ValueError. Hand examples use tolerance 1e-9;
analytic SGD checks use 1e-10. Sampling checks use 10,000 draws for each seed
7,19,31 with frequency tolerance .02. Sampling is with replacement; Python and
browser RNGs do not generate identical traces. Scores are not correctness gates.



Explain and transfer: Trace raw priority → mass → probability → importance weight → loss. Explain double exponentiation and where detachment belongs in PyTorch.
