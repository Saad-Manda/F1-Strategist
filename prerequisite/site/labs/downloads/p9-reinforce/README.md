# p9-reinforce

Standalone Python 3.10+ exercise. Extract this folder anywhere. All tensors use CPU.
Tested with Python 3.12.7, NumPy 2.5.1 and PyTorch 2.13.0+cpu.

```text
python -m pip install -r requirements.txt
python broken.py
python checks.py --candidate broken.py
python starter.py
python checks.py --candidate starter.py
```

Broken code runs but fails checks. Starter reports Exercise incomplete until implemented.
Checks import only the chosen candidate and helpers; they never import solution.py.
Open solution.py only when you want the reference. Invalid contract inputs raise ValueError.
Hand witnesses use float64 and tolerance 1e-9. Stochastic scores are not pass/fail gates.

Implement probabilities(logits[B,A], legal=None) with an optional boolean legal mask of the same shape, and reinforce_loss(logits, actions[B], returns[B], legal=None). Use stable log probabilities, negative mean loss and detached returns. Reject malformed/nonfinite tensors, invalid or illegal actions and empty legal rows. Run the fixed-budget seeded bandit CLI after checks.

Derive the loss sign and score gradient. Distinguish logits, probabilities, one sampled update and expected performance.

Optional: python compare.py --candidate starter.py --seed 7.
