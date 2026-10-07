# RL prerequisite learning project

This folder contains the complete static RL learning website, its standalone Python
exercise packs, authoring scripts, tests, and documentation. You can copy this folder
out of the F1 project and use it independently. Project plans are optional external
references; production code, race data, and the main project's environment are not needed.

The guided course includes Home, roadmap, seven modules, 27 lesson guides, 134
focused readings, a glossary and 25 practice pairs. Validated context connects readings,
browser experiments and local Python practice. Explicit acknowledgments provide
Continue, live counters and combined course/lab export and import. A clickable course
sidebar shows all modules, numbered lessons (`1 → 1.1`) and named steps, with the
current reading highlighted. On mobile, Course contents opens the same navigation
in a drawer. Navigation uses rows and buttons; prose links underline on hover or focus.
See [UI_NAVIGATION_REVIEW.md](docs/UI_NAVIGATION_REVIEW.md) for the current UI review
and [N6_DELIVERY_REVIEW.md](docs/N6_DELIVERY_REVIEW.md) for the preceding delivery review.

## Preview and hosting

From **this folder**:

```powershell
python scripts/preview.py
```

Open `http://127.0.0.1:8000/`. For a nested mount, use
`python scripts/preview.py --port 8001 --subdirectory` and open
`http://127.0.0.1:8001/site/`. Both commands work from any directory when you provide
the script's path. Preview requires Python, but publishing requires no Python or Node.

Publish only **`site/`**, whose `index.html` is the entry point. See
[DEPLOYMENT.md](DEPLOYMENT.md). Publication is currently on hold.

## Local Python exercises

Download a lab ZIP from the website, extract it, and follow that pack's README.
Each pack includes its own dependencies and checks. Implement Python locally;
browser experiments use JavaScript. Reference solutions and explained help are optional.

## Author setup and checks

The reading-course rebuild has completed R0–R8: inventory, schema/migration contracts,
all seven learning modules, course activation, browser review and reproducible delivery. See
[the R0 handoff](curriculum/README.md) and [complete teaching outline](curriculum/OUTLINE.md)
for tracked coverage, prerequisites, legacy identities and all 25 practice mappings;
[the v2 authoring contract](content/README.md) defines sources, compatibility maps
and the tested save/rollback protocol. `python scripts/check_course_v2.py` checks
metadata; `--publish` also requires all authored reading bodies. The active site uses
the v2 registry. [R8_REVIEW.md](content/R8_REVIEW.md) records the final novice/advanced
journeys, archive counts, verification and remaining browser export limitation.

Preview all seven modules through
readings → browser/Python practice → F1 application → project checkpoint with
`python scripts/preview.py --port 8060`, then open
`http://127.0.0.1:8060/`. Add `--subdirectory` for `/site/`.
Existing learner work is validated and retained; close or reload older course tabs
before choosing Retain my progress. All 134 reading bodies pass strict source publication validation. Generate the active course pages
with `python scripts/build_readings.py --write`; omit `--write` to check them.
See [the R7 review](content/R7_REVIEW.md) for activation, compatibility and verification.

Python 3.10+ is the exercise/source minimum; the current project checks were verified
with Python 3.12.7. Use Node 22+ for the JavaScript checks. See the delivery review for
the exact versions observed during N1 verification.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt -r requirements-labs.txt
python scripts/check_project.py
python -m pytest tests -p no:cacheprovider -q
npm test
python scripts/build_static_delivery.py --write
```

On macOS/Linux activate with `source .venv/bin/activate`. Install CPU PyTorch using
your platform's appropriate official package distribution if needed. There are no npm
dependencies and no required `npm install`. `requirements-integration.txt` is only for
optional SB3/MaskablePPO integration and recording, not core generators or hosting.

Generators have a nonmutating check mode by default. See
[LAB_AUTHORING.md](docs/LAB_AUTHORING.md) for individual write commands. Do not run
`record_*` scripts as part of routine checks: those explicitly rerun experiments.

Optional project-plan validation:

```powershell
python scripts/validate_labs.py --check-local-plans --plans-directory ../.antigravity/plans
```

Ordinary checks do not discover or require that directory. The generated delivery ZIP
is `dist/rl-prerequisites-static.zip` with the site files at its root. Caches, environments,
author documents, scripts, tests, and ignored project plans are excluded.

## Structure and progress

- `site/`: learner website, experiments, pack sources/ZIPs, recorded fixtures.
- `scripts/`: portable generators, validators, preview, packaging, recording tools.
- `tests/`: Python/Node checks and content preservation baselines.
- `docs/`: author specifications, content reviews, milestone reviews, and course contracts.
- `dist/`: locally generated, ignored delivery artifacts.

Existing lab IDs and `rl-labs:v1` browser progress are preserved. Keeping the same
hosting origin retains localStorage across a source-folder move; moving to another
origin requires exporting/importing progress. `rl-course:v2` stores explicit reading,
browser, checkpoint and resume acknowledgments. The original `rl-course:v1` string
and first migration backup remain available for recovery. Legacy combined and lab-only
exports remain accepted; rewritten readings start unread. Imports replace course/lab
progress only after complete validation and a confirmed transaction.
Start at `site/index.html`. Library lists the new reading routes; old phase pages
contain reviewed topic relocations. Reading/lab return controls follow the ordered
reading → browser → Python journey. Continue checks unfinished required work within
the resumed lesson or module; reference visits preserve resume. The two theory-only
lessons require their readings without fabricated practice. Lab reset clears that lab's
record and browser acknowledgment; experiment reset clears its trace. Other reading,
lab and checklist records remain intact. Corrupt or blocked storage preserves original
data, disables completion saves and provides export/recovery controls.
See [R7_REVIEW.md](content/R7_REVIEW.md) and the
[progress protocol](content/README.md) for migration and validation details.

Regenerate the complete course with `python scripts/build_readings.py --write`
(`build_course.py` is a compatibility entry point); omit `--write` to check drift.
`scripts/check_project.py` includes this check. Phase page builders and
`build_navigation.py` share the v2 lab renderer. Legacy body, reading-link and section
generators are retired and cannot restore old teaching pages. R0 coverage artifacts
remain frozen authoring evidence outside the publish folder.
