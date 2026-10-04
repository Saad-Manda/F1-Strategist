# p5-stability

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

Implement FIFO push, seeded uniform sample with replacement, independent make_target in evaluation mode with frozen parameters, hard sync every interval optimizer steps, and detached targets r+γ max Qtarget(s′). Set continuation to zero only at true termination. Reject nonpositive capacities/batches/sync intervals, invalid batch shapes and γ outside [0,1]. Run compare.py for paired 192-transition, 48-update CPU ablations.

- `push(buffer, item, capacity)`
- `sample(buffer, batch_size, rng)`
- `make_target(online)`
- `sync_target(target, online, step, interval)`
- `targets(target, next_states, rewards, terminated, gamma)`

Float64 tensors (NumPy float arrays for PER) make hand witnesses reproducible.
Invalid inputs described above raise ValueError. Hand examples use tolerance 1e-9;
analytic SGD checks use 1e-10. Sampling checks use 10,000 draws for each seed
7,19,31 with frequency tolerance .02. Sampling is with replacement; Python and
browser RNGs do not generate identical traces. Scores are not correctness gates.

After implementing: `python compare.py --candidate starter.py --seed 7`. Reports include budgets and versions. Try other seeds.

Explain and transfer: Distinguish storage independence, lag and detachment. Explain replacement sampling and truncation bootstrapping. State what recorded runs can show and why one curve cannot verify code.
