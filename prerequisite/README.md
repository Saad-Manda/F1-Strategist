# RL prerequisite learning project

This folder contains the complete static RL learning website, its standalone Python
exercise packs, authoring scripts, tests, and documentation. You can copy this folder
out of the F1 project and use it independently. Project plans are optional external
references; production code, race data, and the main project's environment are not needed.

The guided course includes one home, roadmap, seven modules, 25 lesson guides and
a complete reference library. Validated context connects exact theory assignments,
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
origin requires exporting/importing progress. `rl-course:v1` stores explicit reading,
browser, checkpoint, and resume acknowledgments alongside the existing lab records.
Legacy lab exports remain accepted, without inventing reading completion.
The generated home, roadmap, seven modules, 25 lesson guides, and reference
library now use the N2 assignments and project-phase handoffs. Start at `site/index.html`;
phase indexes and the lab catalog are reference views. Reading/lab return controls
preserve the invoking lesson and the ordered theory → browser → Python journey.
Continue resumes an unfinished guided step and returns to outstanding module checkpoints.
Reference browsing preserves resume. Lesson completion requires theory acknowledgment,
browser acknowledgment, and completed local lab reflection/verification. Reset controls
explain experiment, lesson, and whole-course scope; whole-course reset asks for confirmation.
Blocked or corrupt storage shows a warning and supports page-local work and export.
See [N5_PROGRESS_REVIEW.md](docs/N5_PROGRESS_REVIEW.md) for migration and validation details.

Regenerate course pages with `python scripts/build_course.py --write`; without
`--write`, the command checks drift. It is included in `scripts/check_project.py`.
`python scripts/build_navigation.py --write` attaches course guidance to all reading
and lab sources; check mode is also part of the normal validation command. The phase
page builders and reading-link builder apply the same shared navigation automatically.
