# R7 — Active course, migration and compatibility

Completed locally on 2026-10-06. The active `site/` uses the v2 registry and all
134 authored readings: 131 required and three optional, 27 lessons (two theory-only),
seven modules and 25 unchanged browser/Python practice pairs.

## Authoritative routes and generators

`build_readings.py` generates the complete active course: Home, roadmap, Library,
glossary, catalog, module/lesson guides, reading/application pages, wrapped lab pages,
relocations and runtime metadata. There are 280 generated files. The phase page
builders supply pure lab bodies to the same renderer, so regeneration cannot scrape
or nest a previously delivered shell. The first lab's retained authoring body is
`content/labs/p1-loop.html`.

Every lab reference and reading/practice return uses a canonical v2 destination.
Library lists all readings; the catalog lists the 25 practice pairs. The consolidated
glossary retains 129 vocabulary entries with reviewed definitions and module links.
Home displays actual required-reading/browser/Python counts. Continue checks unfinished
required work within the surviving resume lesson or module, then the main sequence;
optional reading pointers never divert it into optional work.

Coverage passed before legacy teaching bodies were replaced. The frozen R0 inventory
retains source HTML and hashes for more than 300 sections, plus 108 legacy reading
identities. Four reviewed coverage maps connect those sections to replacement readings.
The two additional introductory probability readings supply explicit prerequisites
absent from the legacy sequence. Frozen artifacts remain outside publication.

The 79 old HTML files now contain reviewed relocations only. All 108 page/section
identities resolve to reviewed single destinations or explicit topic choices, with
module fallbacks. Unknown anchors never trigger a guessed redirect; unknown files
remain ordinary static-host 404s. These pages are absent from Library/course contents.
`build_neural_readings.py`, `build_reading_links.py` and `build_reading_sections.py`
are retired no-op entry points. `build_course.py` and `build_navigation.py` delegate
to the active renderer. The old sidebar/body-generation path is retired.

## Progress and coordinated cache switch

All active reading acknowledgments, browser acknowledgments, lab controls, imports,
lab resets and migration-notice acknowledgments share `reading-store.js`, the same
exclusive browser storage lock, and the validated journal/rollback protocol.
Preparation is read-only. Existing v1 or lab-only saves remain exportable while saves
wait for the explicit “closed or reloaded other course tabs” migration acknowledgment.
Rewritten readings start unread. All 25 lab meanings and original record fields,
browser acknowledgments and unchanged checklist meanings are retained.

`rl-course:v1` is never overwritten or deleted. The first migration backup is never
replaced. Imports validate combined v1, lab-only v1 or combined v2 before any mutation;
the UI asks before replacing the current bundle. Corrupt or blocked storage preserves
original strings, disables completion saves and offers raw recovery export. Failed
transactions preserve the previous memory view and restore original storage, or leave
the recovery journal when restoration cannot finish. An older-tab legacy-key event
blocks subsequent saves until reload. An already loaded v1 script ignores the new
lock, so users must actually close/reload it; the event guard cannot prevent its first
concurrent write.

HTML, CSS references, JavaScript imports, experiment imports and migration metadata
use release `reading-20261006-r7-2`. Runtime metadata is loaded without cache and its
release/schema are checked before storage access. The bootstrap displays a reload
action if module loading fails. Old navigation/lab-shell URLs serve reload stubs;
active HTML does not import them. Retired active v1 context/progress scripts are removed.

## Verification

- All 80 JavaScript checks passed, including transactional recovery/failure cases,
  concurrent session merging, migration activation, all supported import formats,
  exact Continue scopes, stale-release rejection and restored lab controls.
- The full Python selection passed 126 tests; its sole remaining obsolete error-text
  assertion was corrected and its focused rerun passed, covering all 127 tests.
  The selection includes numerical reading witnesses, unchanged extracted packs,
  standalone-copy generation/testing/packaging and archive HTTP checks at root and
  nested mounts. Static asset validation now distinguishes URL directory bases from
  files and validates the relocation JSON relative to its module.
- `check_project.py` passed all deterministic generators, frozen coverage checks,
  exercise/fixture preservation, all 25 archives and site resource audits.
  `check_course_v2.py --publish` passed all 134 authored sources.
  The final generated page selection passed seven checks; `git diff --check` passed.
- Browser review used disposable local origins only. Fresh root-origin acknowledgment
  persisted and Home continued to the second reading with 1/131 reading, 0/25 browser,
  0/25 Python counts. Nested legacy-course migration retained the selected prediction,
  reflection, two revealed hints, solution usage and local-check confirmation with
  0/131 reading, 1/25 browser, 1/25 Python counts. Notice acknowledgment persisted
  after reload. Lab-only migration showed 0/131 reading, 0/25 browser, 1/25 Python;
  it did not invent a browser acknowledgment.
- The mobile drawer at 390px opened as a dialog with focus on Close contents,
  Shift+Tab wrapped to the final visible module, and Escape restored focus to the
  contents button. Home had no horizontal overflow at 390px or 320px. The temporary
  viewport override was reset. Broad legacy topics displayed static choices; a phase
  index redirected to its module and a reviewed narrow anchor to its exact reading.

Browser file selection rejected the synthetic upload through the available tool.
Coordinator/import tests pass; a real-browser file import/export round trip remains
an explicit R8 check. Disposable fixtures are under `tests/browser/` and excluded
from the published site and delivery archive. Existing learner origins were untouched.

## R8 handoff

R8 still owns the full novice Foundations journey, representative advanced journeys,
final delivery review and rebuilding `dist/rl-prerequisites-static.zip`. R7 validates
archives in temporary test locations; it does not refresh the delivery artifact.
No production F1 code, training run, fixture recording, exercise calculation or
download ZIP changed. No deployment, staging, commit or push was performed.
