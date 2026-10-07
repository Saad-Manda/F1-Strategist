# R8 replacement and delivery review — 2026-10-06

R8 completes local verification and packaging of the active reading course. The
release is `reading-20261006-r8`; HTML, metadata checks and the complete JavaScript
module graph use the same cache version. Publication remains a separate task.

## Delivered artifact

`dist/rl-prerequisites-static.zip` is reproducible from the current `site/` bytes.
It contains 555 files: 277 HTML pages, all 25 standalone exercise ZIPs, runtime
assets, pack sources and recorded fixtures. Its compressed size is 2,762,260 bytes;
the payload totals 15,203,148 bytes. SHA-256:

```text
86af01ccaa445fbb962ab8bfc1bc65c02e530f3964c8ac36a74aa247849567cf
```

The course has seven modules, 27 lessons, 134 authored readings (108 core,
23 applications and three optional depth readings), 131 required readings and
25 browser/Python practice pairs. Two lessons are theory-only. HTML includes
134 reading/application pages, 27 guides, seven module pages, 25 labs,
79 compatibility relocations and five entry/reference pages. The glossary has
129 terms. Authoring sources, tests, caches, environments and project plans are
excluded. Extract at a document root or `/site/`; see [DEPLOYMENT.md](../DEPLOYMENT.md).

## Verification

- All 127 Python tests passed in the existing Python 3.12.7 environment. These
  include numerical witnesses, pack/reference contracts, content coverage,
  navigation, resources, archive HTTP behavior and isolated-copy regeneration.
- After the final runtime/cache change, all 14 Python shell/page/navigation,
  static-delivery and portability tests passed again. The isolated copy builds
  and checks the course without production code or the ignored plan directory.
- All 82 JavaScript tests passed with Node 22.19.0. A new coordinator integration
  traverses all 131 required readings, 25 independent browser/Python steps and
  seven checkpoints, reloads saved state, round-trips the v2 export/import and
  verifies that resetting GAE preserves other records and reopens required work.
- The additional reading-acknowledgment regression covers idempotence, unknown
  IDs and optional acknowledgments preserving the previous guided resume. The
  shared acknowledgment helper now enforces those rules for callers.
- `check_project.py`, strict `check_course_v2.py --publish`, final archive check
  and `git diff --check` passed. Deterministic generators reproduce the active
  pages; retired body/link/section generators cannot resurrect legacy teaching.
  R0 source evidence, all lab models, reference packs, ZIPs and recorded fixture
  bytes remain preserved.
- Extracted-archive HTTP checks exercise every published file at root and nested
  mounts and confirm missing paths return 404. The final archive was extracted
  separately and served at `http://127.0.0.1:8084/site/` for advanced browser QA.

## Real-browser journeys

A fresh disposable origin completed the entire novice Foundations path: 19 core
readings, four applications, four browser/Python practice pairs and the separate
three-item preparation checkpoint. The four readings in 1.1 have distinct URLs
and ordered handoffs. The theory-only probability lesson skips fabricated practice.
Checkpoint acknowledgments survive reload; Home reports 23 required readings,
four browser labs and four verified Python practices, then continues to Planning.
Python acknowledgments in browser QA are synthetic self-attestations; the actual
pack/reference checks are covered independently by the Python suite.

Live novice witnesses distinguish terminal versus truncated loop endings, hidden
state with identical observations, reverse returns (`G0=2.5` for gamma 0.5 and
rewards `[2,-1,4]`), and legal-action value calculations (`Vπ=4`, `V*=5`).

Representative advanced journeys on the final extracted nested archive traverse
four neural-stability readings, four GAE readings, five PPO readings, their three
practice pairs and all five PPO application readings. Live experiments show
independent online/target storage, replay eviction and seeded uniform sampling;
GAE terminal advantages `[2.3,1]` versus truncation `[4.73,3.7]` with final-observation
bootstrap; and PPO's advantage-sign clipping branches with frozen old rollout
likelihoods. Recorded ablations retain their evidence labels and fixed budgets.
The Module 7 checkpoint remains incomplete when other Module 7 lessons are unread.
Home correctly resumes the first unfinished Module 7 prerequisite after this
advanced path. An optional Library visit leaves that resume and required count
unchanged.

Packaged Home and an advanced reading fit 390/320 px without document overflow.
Visual review confirms readable prose and headings. The mobile drawer focuses
Close contents, wraps Shift+Tab to the final module, makes the background inert,
closes with Escape and restores focus to Course contents. Earlier milestone
reviews cover the remaining lab/table/equation responsive samples. Automated
checks verify static onward links and no-JavaScript saving explanations; a fully
JavaScript-disabled browser session was not run.

Chrome file selection now succeeds. Confirmed combined legacy import keeps one
browser acknowledgment and one verified Python lab while revised readings remain
unread. A corrupt v2 file is rejected with the original counts retained. Lab-only
legacy import retains Python work without inventing browser/read acknowledgments.
No console errors were captured on the packaged advanced tab.

## Limits

The real-browser Export button was exercised, but the browser tool timed out
waiting for its download event and did not expose a retrievable file. Access to
Chrome's download-manager page was rejected by browser security policy; that
action was not retried through a workaround. Consequently, downloading and
re-importing the exact browser-exported file remains a manual QA check. The
actual coordinator's legacy/lab-only/v2 import validation, export round-trip,
failed-write rollback and complete/partial progress behavior pass automated tests.

Storage and recovery limits remain those documented in [R7_REVIEW.md](R7_REVIEW.md):
close/reload older v1 tabs before retaining progress; loaded older writers cannot
be made to honor the new lock protocol. Completion saving requires JavaScript,
usable localStorage and exclusive Web Locks. Origin changes require progress
transfer. Browser self-attestation is preparation evidence, not proof of production
implementation or training outcomes.

No production training, fixture recording, deployment, Git staging, commit or push
was performed. This review completes R8's local delivery scope with the browser
download/manual round-trip limitation explicitly recorded.
