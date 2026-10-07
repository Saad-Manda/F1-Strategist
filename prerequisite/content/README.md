# V2 reading authoring and R1 contracts

`course-registry.json` is the canonical v2 course registry. It was initialized from
the frozen R0 outline; edit it directly as R2–R6 author the reading bodies. Do not
regenerate it from R0 and lose authored status or deliberate curriculum refinements.
R7 publishes this registry under `site/assets/`; it is authoritative for the active site.

## Registry schema version 2

The Python definition/validator is `scripts/course_v2.py`; the browser definition is
`site/assets/course-model-v2.js`. Cross-language tests compare all reading contexts
and malformed metadata cases. The runtime validator checks metadata; publication
additionally checks the actual files with the Python fragment validator.
Static archive validation checks authored metadata and rendered reading routes;
it does not require the excluded authoring fragments inside a downloaded site.

| Record | Required fields and semantics |
| --- | --- |
| Course | `schemaVersion: 2`, ordered `modules`, `lessons`, `readings`, `projectStages`. No v1 `resources`/section-assignment semantics. |
| Module | Stable `id`, `title`, `objective`, project `phase`, canonical `route`, ordered `lessons` and `applications`, `projectCheckpoint`. Display number derives from position. |
| Lesson | Stable `id`, `title`, owning `module`, canonical `route`, earlier `prerequisites`, nonempty ordered core `required`, ordered further-depth `optional`, `practice`. |
| Practice | `null` for theory only, otherwise `{labId, route}`. Lab IDs are independent of lesson IDs. Every delivered lab maps once; paths and phase must match its delivered contract. |
| Reading | Stable semantic `id`, `title`, owning `module`, owning `lesson` (null for application), `role`, canonical `route`, specific `goal`, `minutes` (integer 1–60), `source`, `status`, `requires`, `teaches`. |
| Role/status | `core`, `further-depth`, or `application`; `planned` or `authored`. Further-depth never supplies a prerequisite needed by a required page. |
| Concept graph | IDs identify taught concept clusters. `teaches` is `[id]`; `requires` names clusters that the required sequence has already introduced. Ownership occurs in exactly one main sequence. |
| Checkpoint | `route` is the module route plus `#project-checkpoint`; `required` equals its application sequence. `checks` contains distinct stable IDs and unchanged project-preparation text. Existing title/plan/readiness labels are retained. |
| Project stages | Preserve all phases 0, 0.5, 1, 2, 3, 3.5, 4, 5, 6, 7, 8 and 9; a stage has its matching learning module or null. |

Reading IDs use `<semantic-group>/<semantic-slug>` and persist across reordering,
title edits and owner changes. The initial semantic groups match their lessons or
modules; the **registry ownership** determines page context, not a filename prefix
or a query string. Routes derive from identity: `readings/<id>.html` for core/depth,
`applications/<id>.html` for applications. Lessons/modules use `lessons/<id>.html`
and `modules/<id>.html`. IDs never derive from display positions; traversal and URL
queries are rejected. Legacy `kind`/anchor/range fields are invalid in v2 readings.

## Authoring sources and navigation

Create `readings/<semantic-group>/<slug>.html` or
`applications/<semantic-group>/<slug>.html` here, at exactly the registered `source`
path relative to `prerequisite/`. Supply an HTML **body fragment** with paragraphs,
headings, a complete example, a recap, a common mistake and self-check explanation
as appropriate. The fragment validator checks structural integrity and rejects
shell tags, h1, scripts, active attributes, duplicate heading anchors and tiny
placeholders. It is a structural check, not a substitute for educational review.
Change that reading's status to `authored` when its actual body exists.

The draft check permits absent sources only for `planned` readings. A source with
planned status is an error; an authored reading cannot omit its body. `--publish`
requires every body; all 134 readings now pass this validation after R6.
There are no fabricated HTML placeholders or copied old documents in the source tree.

`navigation-v2.json` is the generated offline navigation manifest used for cross-language
verification. After changing course metadata, regenerate it with:

```powershell
python scripts/check_course_v2.py --write
python scripts/check_course_v2.py
```

This command writes no published pages or learner data. `reading_context`/`readingContext`
derive module/lesson numbering, Reading X of Y, Previous, explicit Next and completion
eligibility from the same model. A final core reading leads to the mapped Browser lab;
a theory-only final reading leads to the next lesson (or first module application).
Application sequences end at their checkpoint. Further-depth completion never blocks
required learning and its final page returns to the owning lesson. R2 supplies the
visible shell and acknowledgment behavior; explicit Next is independent of Home resume.

## Reviewed compatibility decisions

`progress-migration.json` records one reviewed decision for every old resource,
practice anchor and checklist item. All **108** old reading identities currently
map to unread: substantial rewriting and new boundaries do not justify completion
equivalence. Future equivalence requires explicit target IDs, a reason and authored
targets. Coverage destinations alone never confer completion.

All 25 lab meanings are unchanged. The map preserves browser acknowledgments by
lab ID; raw `rl-labs:v1` fields retain attempts, predictions, reflection, hints,
solution usage and verified completion. A signature covers the actual learning/
calculation contract rather than old teaching links. Checklist text is identical
and can carry forward, but never acknowledges replacement application readings.
Resume translation targets an unfinished reading/practice/checkpoint in the surviving
lesson or its module; a removed lesson can specify null plus a module fallback.

`route-relocations.json` reviews all 108 old page/section identities. Narrow destinations
can redirect; broad sources present explicit topic choices with their module as fallback.
Indexes point to modules, glossaries to the consolidated glossary. Targets are validated
against v2 canonical routes. R7 renders these inputs as 79 static relocation pages,
outside Library/course contents. Known single-target identities redirect; broad topics
offer explicit choices. Unknown routes remain 404 and unknown anchors never redirect.

The frozen identity snapshot stays in `curriculum/legacy-v1-identities.json`, outside
the published reading tree. Old imports validate against this snapshot before any
translation; new v2 IDs never enter the legacy validator or vice versa. Retained
legacy progress is separately validated and carried in v2 exports for recovery.

## Progress schema and exact storage protocol

`reading-session.js` loads the published registry/migration bundle and checks its
release before storage access. `reading-store.js` coordinates every active reading,
lab, import, reset and notice writer through `course-progress-v2.js`. Existing saved
work is prepared without writes; migration waits for explicit confirmation that older
course tabs have been closed or reloaded. Fresh visits also make no progress writes.
R1 contract tests use disposable in-memory storage; R7 adds coordinator/control tests
and browser checks on disposable local origins.

The course progress schema is:

```json
{
  "version": 2,
  "readings": [],
  "browser": [],
  "checks": {},
  "resume": null,
  "migration": null
}
```

Readings contain valid v2 reading IDs (further-depth acknowledgments are permitted
but optional); browser contains **lab IDs**. Checks map module IDs to valid check IDs.
Resume is null, `{kind: "reading", reading}`, `{kind: "lesson", lesson, step}` for
browser/python on a mapped lesson, or `{kind: "checkpoint", module}`. Migration is
null or `{fromVersion: 1, noticePending: boolean}`. The notice is cleared only by
an explicit saved acknowledgment; preparing, importing or revisiting does not clear it.
Unknown fields/IDs, invalid types, duplicate acknowledgments and impossible resume
forms are rejected. Theory-only lessons need only their core readings to complete.

Combined exports use `{format: "rl-course-progress", version: 2, course, labs,
retainedLegacy}`. `labs` still has v1 lab semantics; `retainedLegacy` is null or
`{course: <validated v1 course or null>, labs: <validated v1 labs>}`. Lab-only v1 and
combined v1 imports are supported. Validating an import completes before any writes.
Export/import remains necessary across origins; this introduces no synchronization.

Persistent course storage uses `rl-course:v2` with envelope `{version: 2, course,
retainedLegacy}`. Lab storage stays `rl-labs:v1`. **Never delete or overwrite
`rl-course:v1`.** The first retained legacy snapshot also gets a persistent backup
under `rl-course:migration-backup:v1`, never replaced by later imports.

The transaction protocol is compensating rollback/recovery, not a native database
transaction. Its commit point is successful, verified removal of the journal:

1. Hold the same exclusive `rl-course-progress:v2` storage lock for recovery, reads,
   preparation and commit. `withProgressLock` accepts a browser locks manager;
   without one, persistent migration/import stays disabled and progress remains
   available for export. Low-level synchronous helpers require this caller discipline.
2. Before loading or importing, recover any `rl-course:transaction:v2` journal under
   the lock. A valid journal is `{version: 1, before: {<three keys>: <raw string or null>}}`.
   Restore all three original values, verify them and remove/verify the journal.
   A corrupt journal makes no mutations. Recovery failure blocks further writes.
3. Prepare/migrate/validate both course and labs in memory. Preparation is read-only.
   Invalid/corrupt input cannot fall back to an empty replacement or discard saved work.
4. Capture original raw strings for `rl-labs:v1`, `rl-course:v2` and the backup key.
   Write and verify the journal **before** changing any of them.
5. Write/verify labs, then the v2 envelope, then the first backup if applicable.
   Remove/verify the journal. Only after that return success and update live stores/
   counters. Preserve the old data and memory view until success.
6. On any failure, restore/verify every original string (remove keys originally absent).
   Clear the journal only if every restoration succeeded. An incomplete rollback keeps
   the journal, reports a recovery warning and refuses new imports until recovered.
   A page/process interruption leaves the same journal for the next load to roll back.

R7 routes all v2 writers (including lab controls, notice clearing and reset) through
this protocol and the same lock, and versions HTML and its runtime graph together.
An older v1 tab does not obey the new lock; migration asks users to close/reload it
before permitting saves. A legacy-key storage event disables subsequent saves until
reload. This guard cannot prevent an already loaded old script from writing before
the event arrives. No protocol can promise recovery while storage itself remains blocked;
the validated in-memory bundle stays exportable. These integration requirements are
tested at the contract, coordinator and control levels; R7 browser evidence and remaining
R8 delivery checks are recorded in [R7_REVIEW.md](R7_REVIEW.md).

## Checks

```powershell
python -m unittest discover -s tests -p test_course_v2.py
node --test tests/test_course_v2.mjs
python scripts/check_course_v2.py
python scripts/check_course_v2.py --publish
```

The final command passes after R6; negative tests construct planned readings explicitly. R1 tests cover
ownership, duplicate routes/IDs, source contracts, independent lab mapping, Python/JS
parity, legacy/v2/lab-only migration, reviewed equivalence, changed meanings, renamed/
removed/reordered lessons, checkpoints, all transaction failure points, silent writes,
blocked storage, failed rollback, interrupted recovery and retained export data.
`check_project.py` checks the active v2 generator, metadata, lab packs, frozen coverage
and preservation of exercise/fixture bytes.

R1 completed locally on 2026-10-05. Verification: 14 schema/source standard-library
tests and 26 JavaScript migration/navigation tests passed; the existing full
JavaScript selection passed 89 tests. The focused Python course/navigation selection
passed 41 tests. The broader selection using the existing project virtual environment
passed 61 checks including standalone-copy generation/testing; its archive comparison
overlapped an asset edit and was rerun with fixed inputs, passing all three static
archive/HTTP checks. The active system Python lacks Gymnasium, so the existing virtual
environment supplied it without installing anything. The strict publication check
correctly rejects all 134 still-planned reading bodies. All deterministic generators
passed, including unchanged pack/fixture/archive checks; `git diff --check` passed.

At R1, no browser UI changed and no learner storage was accessed. R2 still needed the new
visible reading shell and four authored 1.1 readings; R7 owns live migration and
relocation activation. No production F1 code, exercise calculation, fixture or
download ZIP changed. No training, deployment, staging, commit or push was performed.

R6 is implemented: all seven modules have complete preview paths through unchanged
practice into F1 application and preparation. See [R6_REVIEW.md](R6_REVIEW.md) for
coverage, validation and the R7 handoff;
[R5_REVIEW.md](R5_REVIEW.md) records the Neural value learning review;
[R4_REVIEW.md](R4_REVIEW.md) records the Planning/tabular review;
[R3_REVIEW.md](R3_REVIEW.md) records the Foundations review;
[R2_REVIEW.md](R2_REVIEW.md) records the original shell/storage review. R7 activates
the v2 store and navigation; see [R7_REVIEW.md](R7_REVIEW.md) for the switch review.
All 134 bodies are authored, with no planned readings remaining. Strict publication
validation passes. R8 delivery verification and packaging are complete; see
[R8_REVIEW.md](R8_REVIEW.md) for the archive, browser journeys and verification limits.
Deployment remains separate.
