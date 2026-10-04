# p9-ppo

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

Implement frozen(log_probs) as an independent detached clone; ppo_loss(new_log_probs, old_log_probs, advantage, epsilon=.2) as negative mean of the minimum surrogate with detached old data/advantages; diagnostics() returning ratios, clip_fraction and sampled approx_kl. Validate nonempty matching finite vectors and ε in [0,1). Optional compare.py --integration runs real CPU MaskablePPO and Windows factory tests; it is separate from the objective checks.

Explain both advantage signs, loss sign, old-policy freezing and KL diagnostics. What experience budgets and masked evaluation settings must match before comparing algorithms?

Optional: python compare.py --candidate starter.py --integration. First install gymnasium stable-baselines3 sb3-contrib. Run in a terminal; the Windows main guard is included.
