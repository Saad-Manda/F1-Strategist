# p9-advantage

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

Implement advantages(returns, values), actor_loss(log_probs, advantage), and critic_loss(values, targets). Inputs are nonempty matching finite vectors; advantages return detached differences, actor uses negative mean of detached advantage times log probability, critic uses mean squared error with detached targets. Verify actor/critic gradient paths separately.

Explain what expectation remains unchanged, why action dependence can bias it, and why baseline quality affects variance. Trace actor and critic gradients.


