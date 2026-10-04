# p6-shaping

Python 3.10+, standard library only.
Extract anywhere. All files are standalone; no repository or backend required.

```text
python -m pip install -r requirements.txt
python broken.py
python checks.py --candidate broken.py
python starter.py
python checks.py --candidate starter.py
```

Broken code runs but fails checks. Untouched starter reports Exercise incomplete.
Implement TODOs or repair a copy; pass its filename to --candidate. Checks never
import solution.py. Open that optional reference only when you request help.

## Contract

Implement shaped_return(rewards, potentials, gamma, shaping_gamma=None), taking T rewards and T+1 finite potentials. Default to matching discounts, but support explicit mismatch for diagnosis. Implement route_returns(gamma=1, failure_potential=0, shaping_gamma=None), returning base/bonus/shaped/boundary/shift rows for DIRECT, VIA+FINISH and VIA+WAIT. Validate finite inputs and discounts in [0,1].

- `shaped_return(rewards, potentials, gamma, shaping_gamma=None)`
- `route_returns(gamma=1, failure_potential=0, shaping_gamma=None)`

Floating comparisons use 1e-9; normalized probability rows use 1e-10. Invalid
inputs described above raise ValueError. Seeded frequency checks use 10,000 draws
for seeds 7,19,31, with tolerance .02. Browser and Python RNGs are different;
identical seeds reproduce within each implementation, not between languages.
Counterfactuals and exact payoffs are model calculations, not measured training.
No test requires a learner to outperform a baseline on a lucky seed.

Tested locally: Python 3.12.7, NumPy 2.5.1, Gymnasium 1.3.0 and PettingZoo 1.27.0
(only install the packages listed in this pack's requirements). The audit's tiny
constant observation and A/B names trigger official API-test recommendations;
the lifecycle assertions still pass. These recommendations are not suppressed.



Explain and transfer: Derive the finite-horizon telescope including the endpoint term. Explain matching discounts, terminal potentials and why objective preservation does not guarantee faster training.
