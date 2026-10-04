# p5-network

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

Implement predict(x[B,D], weight[A,D], bias[A]), scalar mean mse(), and train_step with zero_grad → forward → backward → step. Reject mismatched shapes and nonfinite inputs. Use float64 witnesses. Run the fixed 200-step fit with even-index training examples and odd-index held-out examples; report initial and final held-out error.

- `predict(x, weight, bias)`
- `mse(prediction, labels)`
- `train_step(model, optimizer, x, labels)`

Float64 tensors (NumPy float arrays for PER) make hand witnesses reproducible.
Invalid inputs described above raise ValueError. Hand examples use tolerance 1e-9;
analytic SGD checks use 1e-10. Sampling checks use 10,000 draws for each seed
7,19,31 with frequency tolerance .02. Sampling is with replacement; Python and
browser RNGs do not generate identical traces. Scores are not correctness gates.

After implementing: `python compare.py --candidate starter.py --seed 7`. Reports include budgets and versions. Try other seeds.

Explain and transfer: Trace shapes from inputs to scalar loss. Explain gradient clearing and the held-out split, and why this is not yet reinforcement learning.
