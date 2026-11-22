# Prerequisites

Everything for learning what each project phase needs, in one self-contained folder. Nothing
here imports, or is imported by, the main project (`src/`, `tests/`, `configs/`).

```
prerequisites/
  site/     the reading: seven prerequisite sets as HTML pages, one hub (site/index.html), one glossary
  labs/     the doing: notebooks and code exercises that the pages point to, plus reference solutions
  tools/    serve.py (open the site), nav.py (site structure checks)
```

## Reading

Open `site/index.html`, or serve it (use this if the sidebar ticks do not carry from page to
page when opened straight from disk):

```
cd prerequisites
python tools/serve.py
```

## Labs

Every page of a set that has labs ends in a lab block. In-page labs (hand calculations,
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

Details, including where the solutions are: `labs/README.md`. Phases 1, 3.5, 4 and 5 have labs today;
the other sets get theirs phase by phase.

## Maintaining the site

`site/assets/course.js` is the single source of truth for the course structure (phases,
pages, labs). After changing it or adding a page:

```
cd prerequisites
python tools/nav.py check          every page listed, titled and linked correctly
python tools/nav.py hub            regenerate site/index.html from the manifest
```
