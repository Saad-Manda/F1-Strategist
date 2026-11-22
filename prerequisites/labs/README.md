# Prerequisite labs

Hands-on labs for the prerequisite sets in `../site/`. Every page there ends in a
lab block; the ones that involve code point here. Labs are self-contained toys: nothing in
this folder imports, or is imported by, `src/`.

Run everything from the `prerequisites/` folder (the parent of this one), with the project's environment active
(`requirements.txt` already covers what the labs need).

```
python -m labs status              what passes, per lab; also refreshes the ticks on the doc site
python -m labs open  p1-01         open a lab (notebook labs launch JupyterLab)
python -m labs check p1-04         run a lab's checks
python -m labs check p1-cap 3      capstones: check a single stage
python -m labs hint  p1-04         first hint;  `hint p1-04 2` shows hints 1 and 2
```

## The kinds of lab

| Kind | What you get | How it is checked |
|---|---|---|
| Notebook | `lab.ipynb` with TODO cells | Check cells inside the notebook; `labs check` re-runs it top to bottom |
| Code + tests | a `.py` file with stubbed functions and a test file | `labs check` runs the tests |
| In page | questions, hand calculations and widgets inside the doc page itself | Checked in the browser, nothing to run here |

A code lab may begin with a short in-page warm-up (a hand calculation). It is checked in the
browser like any in-page question; the lab itself is passed by its code checks.

A stub looks like this. Replace the `raise` with your code:

```python
def toy_fuel_penalty(laps_left):
    # TODO: FUEL_PER_LAP times laps_left
    raise NotImplementedError("TODO p1-cap: FUEL_PER_LAP times laps_left")
```

## Where things are

```
labs/<phase>/<lab>/          your working copies: edit these (phase1, phase35, phase4, phase5, ...)
labs/solutions/<phase>/<lab>/ reference solutions, for after you have tried
labs/labkit/                shared helpers and small environments (given code)
labs/.progress.json         your local record of passed notebook tasks (git-ignored)
```

Hints come in three steps, from "where to look" to "nearly the answer". The solutions folder
mirrors the lab folders file for file.

## For authoring (not needed to do the labs)

Solutions are the source of truth; starters are generated from them and must not be edited
by hand as an author.

```
python -m labs.tools.py2nb phase1               build solution notebooks from labs/tools/nb_src/
python -m labs.tools.make_starter phase1        generate starters (skips labs that already exist)
python -m labs.tools.make_starter phase1 --force   regenerate, DISCARDING any learner edits
python -m labs.tools.selftest phase1            solutions pass; starters fail only on TODOs
python -m labs.tools.site phase1                put lab blocks into the doc pages and the manifest
```
