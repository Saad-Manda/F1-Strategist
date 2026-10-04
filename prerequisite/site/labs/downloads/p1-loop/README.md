# p1-loop — Build the interaction loop

Extract this folder anywhere on your machine. Python 3.10+ is required; verified with
Python 3.12.7 and Gymnasium 1.3.0. No F1 project imports, data downloads, GPU, or web server.

## Set up and try the exercise

Run these commands **inside the extracted p1-loop folder**:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe starter.py --seed 7
```

The untouched starter reports “Exercise incomplete.” Fill in its three TODOs: `reset`,
`step`, and `collect_episode`. Supplied CLI/plotting-independent scaffolding is in
`exercise_common.py`; you do not need to edit it.

World: start at 0, LEFT=0, RIGHT=1. LEFT at 0 stays there. Arrival at 2 gives +5 and
terminates; all other transitions give -1. `reset` returns `(observation, info)`; `step`
returns `(observation, reward, terminated, truncated, info)`. Info is a fresh dict
containing `steps`. The base environment has no time limit; the supplied TimeLimit wrapper
adds an external collection cap. Trace dict keys are specified in starter.py.

```powershell
.\.venv\Scripts\python.exe starter.py --actions RIGHT,RIGHT --limit 6
.\.venv\Scripts\python.exe starter.py --actions RIGHT,RIGHT --limit 1
.\.venv\Scripts\python.exe checks.py --candidate starter.py
```

Checks report expected/observed behaviour and accept different correct implementations.
No check imports the solution as its oracle. The terminal script has two steps and total
reward 4; the one-step cap has total -1 and truncates at observation 1.

## Debugging investigation

Before reading any solution, predict this runnable variant's trace:

```powershell
.\.venv\Scripts\python.exe broken.py --actions RIGHT,RIGHT --limit 1
.\.venv\Scripts\python.exe checks.py --candidate broken.py
```

It intentionally fails a collection check. Compare the browser's one-step cap, inspect
its two boundary flags, and repair the collector in your own copy. A 20-step safety guard
keeps the intentionally broken example bounded; it is not the collection condition to learn.

## Optional answer and transfer

`solution.py` is an explicit reference answer. Open it only if you want it; the complete
pack contains inspectable solutions. The website provides hints and an explained solution
on request. Run `checks.py --candidate solution.py` to check that answer.

Explain who chooses actions, who returns rewards, and why both terminal and truncated
episodes stop collection. Then change the goal from 2 to 3 in your own variant and update
the observation space and independent expected traces. That extension has different
targets; the supplied checks intentionally apply only to the original world.

The browser random agent uses its own seeded generator; Python uses `random.Random`.
Identical seeds reproduce each platform's run, not identical random traces across platforms.
Compare their deterministic scripted actions against `fixtures.json` instead.

References: [Gymnasium Env contract](https://gymnasium.farama.org/api/env/) and
[handling time limits](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/).
