# R2 reading-shell review — 2026-10-05

Lesson 1.1 has four distinct, complete reading bodies in `readings/p1-loop/`:
agents/environments/episodes, one step and transition records, reset and episode
endings, and spaces/environment checks. The same three-position delivery example
continues into the existing `p1-loop` browser experiment and Python pack. Grid
array formats are introduced separately without changing the chain exercise.
Every page explains its code/API terms, gives worked evidence and a self-check,
and ends with its explicit next action. Mathematical learning targets are deferred.
Gymnasium API details were checked against the official links in the readings.

`scripts/build_readings.py` validates the canonical source before rendering four
portable pages, shared navigation and preview metadata. Its default mode checks
reproducibility. `scripts/check_project.py` includes it. The R0 audit now limits its
legacy route inventory to the frozen R0 route set, so newly authored pages never
enter that historical baseline. Existing coverage/identity snapshots stay unchanged.

## Review the complete path

From the portable `prerequisite/` directory:

```powershell
python scripts/build_readings.py --write
python scripts/preview.py --readings --port 8024
```

Open `http://127.0.0.1:8024/`. For a nested mount, add `--subdirectory` and open
`http://127.0.0.1:8024/site/`. The preview overlays canonical Home/module/lesson/lab
routes in memory. Its lab retains the existing experiment, model and downloadable
pack, with review links redirected to the new readings. The active v1 Home and
legacy documents stay in place until the complete replacement is switched at R7.
The new sidebar displays the full planned order; only authored readings and their
practice path are actionable. R2 supplies no placeholder reading bodies.

## Completion and progress

Finish reading and continue acknowledges only the current reading, saves through
the R1 transactional store under an exclusive lock, then follows the explicit Next
destination. Completed readings show Continue. Next/Previous/sidebar browsing and
scrolling do not acknowledge anything. Home Continue selects unfinished required
work; it does not redirect the reading's fixed Next sequence. Browser acknowledgment
and Python completion remain separate, and Python needs explanation plus local-check
confirmation. Prediction, attempts, hints, requested solution, verification and
explanation retain the existing seven-field practice contract and independent lab ID.

The preview initializes only fresh v2 progress. It refuses writes on origins with
legacy course data, lab-only data, retained backups or interrupted journals. It does
not activate migration or recovery against learner origins. Corrupt/blocked storage
keeps completion unsaved and offers static Next plus export. Preview imports accept
fresh v2 exports only; invalid imports retain existing work. R7 owns legacy imports,
live migration, recovery and route relocation UI.

## Verification

Real browser checks used disposable localhost origins at root and `/site/`:

- Home → Foundations → lesson 1.1 → all four distinct readings → browser/Python.
- Visiting/Previous leaves completion unchanged; repeated acknowledgment stays at
  one completion; reload restores it; Home Continue finds the missing reading.
- RIGHT, RIGHT gives rewards −1/+5, total +4 and termination; cap one stops at
  observation 1, reward −1 and truncation. Existing experiment controls are preserved.
- Hint/solution requests and Python reflection/completion controls work and persist.
- Desktop and 390/320 px reading layouts; 320 px has no horizontal page overflow.
  The mobile drawer fits, scrolls internally, wraps Tab/Shift+Tab, and Escape restores
  the Course contents button. Closed-details descendants were excluded from the
  focus trap after testing found retained layout boxes for hidden elements.
- A second tab's completion updates the open drawer without changing its expanded
  groups or focused Close contents control. Keyboard Enter follows the reading path.

Automated checks cover source validity, distinct/reproducible rendering, all static
links and fragment destinations without JavaScript, active-v1 isolation, executable
reading snippets, unchanged pack numerical witnesses, simultaneous ending flags,
fresh progress/reload, queued saves, legacy-origin protection, failed-save rollback,
full practice-field export/import and invalid-import retention. All 94 JavaScript
tests pass. The existing pack checker passes environment and episode collection.
Deterministic generators preserve all 25 packs and existing exercise/fixture bytes.
Archive/root/nested HTTP and isolated-copy tests also verify portable delivery.
The standalone suite subprocess allowance is 600 seconds to accommodate accumulated
generator, test and archive validation time on Windows; earlier shorter runs timed out.
The page validator also caches resolved anchor targets per audit; a focused test
checks repeated links share resolution while outside paths remain rejected.
Final verification passed 29 focused Python checks (including archive/root/nested
HTTP and the fresh standalone-copy run), all 94 JavaScript checks, the deterministic
project generators, the unchanged chain pack checker and `git diff --check`.

R3 next: author the remaining Foundations lessons and application sequence. Reuse
this shell and canonical identities; extend preview availability with authored
content. Full publication validation still rejects the 130 planned reading bodies.
No production F1 code, exercise calculations, fixtures or download ZIPs changed.
No training, deployment, staging, commit or push was performed.
