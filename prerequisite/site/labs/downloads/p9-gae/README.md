# p9-gae

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

Implement gae(rewards, values, next_values, terminated, trace_continue, gamma=.9, lam=1), returning advantages and value targets (advantages+values). Each input is a same-length one-dimensional NumPy vector; flags are boolean. next_values explicitly describes each transition’s final next observation. Bootstrap only nonterminals; cut recursion on trace_continue=False and at the end of the array. Reject invalid shapes, nonfinite inputs, discounts outside [0,1] and terminal rows with an enabled trace.

Explain separate bootstrap and trace masks. Derive the λ=1 endpoint term and describe how you would obtain final observations from an auto-reset collector.


