# Prerequisites

Everything for learning what each project phase needs, in one self-contained folder. Nothing
here imports, or is imported by, the main project (`src/`, `tests/`, `configs/`).

```
prerequisites/
  site/     the course: one HTML page set per phase, a hub (site/index.html), the Pit Wall
            (site/pitwall.html) and a glossary
  labs/     the doing: notebooks and code exercises that the pages point to, plus reference solutions
  tools/    serve.py (open the site), nav.py (site structure), verify.py (check everything)
```

## The course

Each phase the project needs is a **case**: a mystery about the plan, opened on the phase's first
page ("Case brief") and closed on its last ("Back to the plan"), where the verdict on what the plan
should change is written up.

| Phase | Case |
|---|---|
| 1 · RL | The 5,000-second head start |
| 3.5 · DP oracle | Beating the oracle |
| 4 · Q-learning | The learner that can't see the window |
| 5 · DQN | The champion who keeps pitting |
| 6 · Multi-car | The undercut that doesn't exist |
| 8 · Self-play | The run that dies at episode zero |
| 9 · PPO | The learner that learns nothing |

Inside a phase:

- **"Your call"**: a content page opens with a question about the toy race. You answer before
  reading on; the page's reveal explains the answer.
- **The Pit Wall** (`site/pitwall.html`): a 20-lap toy race you can play, with one mode per phase:
  race, oracle, table learner, DQN replay, rival, pit-timing duel, Training room. Pages embed the
  mode they need. Every number in it is checked against the Python labs (see *Checking* below).
- **Championship points** (sidebar): page read 1, "Your call" answered 1, in-page lab 3, code lab
  5, capstone 10, case closed 10, a Pit Wall personal best within 1 s of the optimum 5 per mode.
  Nothing is locked; points only show how far you are. Progress is kept in the browser's local
  storage.

## Reading

Open `site/index.html`, or serve it (use this if the sidebar ticks do not carry from page to
page when opened straight from disk):

```
cd prerequisites
python tools/serve.py
```

## Labs

Every page of a phase that has labs ends in a lab block. In-page labs (hand calculations,
quizzes, widgets) are done in the browser. Code labs live in `labs/` and are run from inside
this folder, with the project's Python environment active:

```
cd prerequisites
python -m labs status              what passes, per lab; also refreshes the ticks on the site
python -m labs open  p1-01         open a lab (notebook labs launch JupyterLab)
python -m labs check p1-04         run a lab's checks
python -m labs check p1-cap 3      capstones: check a single stage
python -m labs hint  p1-04         first hint;  `hint p1-04 2` shows hints 1 and 2
```

All seven phases have labs. Details, including where the solutions are: `labs/README.md`.

## Maintaining the course

### What to edit, and what not to

The page HTML in `site/phase-*/` is the source for the reading: edit it directly. Some parts of the
site are **generated** from other files. Edit their source and regenerate; a hand edit to the
generated file is overwritten by the next regeneration (and `verify.py` reports it).

| Generated | Source | Regenerate with |
|---|---|---|
| lab blocks at the end of pages, and the `lab` entries in `course.js` | `labs/solutions/<phase>/<lab>/lab.yaml`, `labs/tools/site_src/<phase>/*.html` (in-page labs and quizzes) | `python -m labs.tools.site phase9` |
| the hub's course map, `site/index.html` | `site/assets/course.js` | `python tools/nav.py hub` |
| solution notebooks, `labs/solutions/**/*.ipynb` | `labs/tools/nb_src/<phase>/*.py` | `python -m labs.tools.py2nb phase9` |
| learner starters, `labs/<phase>/` | the solutions | `python -m labs.tools.make_starter phase9` (skips labs that exist) |
| `site/assets/progress.js` | your lab results | `python -m labs status` |
| Pit Wall data: `site/assets/pitwall/replay_policy.js`, `pitgame_data.js`, `training_data.js` | training runs in Python | `python -m labs.tools.pitwall_replay_export train --seed 1 --races 2000`, `python -m labs.tools.pitwall_duel_game_export export`, `python -m labs.tools.pitwall_training_export export` (the last trains for about 15 minutes on 10 cores) |

`site/assets/course.js` is the single source of truth for the course structure: phases, cases,
pages (with titles and their "Your call"), and labs. After adding, removing or renaming a page,
update it and run `python tools/nav.py hub`.

The Pit Wall's JavaScript (`site/assets/pitwall/engine.js`, `oracle.js`, `learner.js`, `duel.js`,
`pitgame.js`, `replay.js`) mirrors Python in `labs/labkit/`. Change both together; the parity
checks fail when they disagree.

### Checking

Run this before committing any change to the course:

```
cd prerequisites
python tools/verify.py            # about a minute
python tools/verify.py --full     # also every lab's selftest and a re-train of recorded runs: minutes
```

It runs, and reports on, each of:

- **structure** (`nav.py check`): every page is in the manifest, titled and linked, with no broken links.
- **style** (`nav.py style`): warnings only. A page's core path should stay under 900 words, its first
  interactive should come within 400, and a list of filler words is banned.
- **answers**: every quiz answer is one of its options, and every "Your call" has exactly one reveal.
- **generated**: the generated files above match their sources.
- **pitwall**: every Pit Wall mode gives the same numbers as the Python it mirrors.

It changes nothing on disk. Node must be on PATH for the Pit Wall checks.
