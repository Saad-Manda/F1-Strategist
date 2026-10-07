# Reading-course rebuild: R0 handoff

R0 completed locally on 2026-10-05. The published v1 course is still in place.
These tracked inputs belong to the standalone `prerequisite/` project and are
excluded from static publication because they live outside `site/`.

Read [OUTLINE.md](OUTLINE.md) for the full module → lesson → reading sequence,
purposes, practice destinations and application handoffs. Edit `sequence.txt`
to revise these planned purposes. `outline.json` is an R0 design artifact, **not**
the runtime v2 registry; schema implementation begins in R1.

## Inventory and coverage

- `coverage-map.json` inventories all 79 old pages, including seven phase indexes,
  as 398 educational sections. It retains complete section HTML/text, code,
  tables, lists, subordinate headings and 129 glossary terms. Inline equations,
  examples and warnings remain inside their full source sections, including those
  without separate headings. Each section has explicit destination IDs and a
  disposition. A destination list identifies a split across teaching purposes;
  it does not authorize copying the whole section into every page.
- `legacy-v1-identities.json` captures all 108 old page/section resource identities,
  their assignment boundaries, 25 lesson/lab contracts, module checklists,
  project stages, saved-progress field names, resume forms and runtime hashes.
- `legacy-routes.json` captures all 140 existing HTML routes and resource identities
  before any removal. R1 must review actual relocation destinations: a broad old
  document needs topic choices or a module, never an arbitrary first subsection.
- `outline.json` contains the reading-level concept graph: each stable semantic
  ID names the concept cluster introduced by its goal; `requires` lists preceding
  clusters and `teaches` supplies that cluster. Within lessons, each required page
  builds on its preceding core page. Lesson prerequisites connect to the final
  required concept in the prerequisite lesson, whose preceding chain is transitive.
  Application chains follow all required module concepts. Optional pages contribute
  no dependency needed by the core path.

The outline contains 108 core, 23 application and three further-depth pages across
27 teaching lessons. These are planned pages, not authored or verified page bodies.
The consolidated glossary is a separate reference destination; its final layout is
deferred to authoring. Estimated times are pacing targets to revise after writing.

## Decisions and prerequisite review

Keep the seven subject areas and phase mappings. Retain the existing 25 practical
lesson anchors, each with exactly one delivered lab/pack. Add two theory-only
lessons: `p1-probability` before values/Bellman expectations and `p9-probability`
before REINFORCE. A theory-only lesson ends by acknowledging its last core reading
and proceeding to the next lesson; it must not manufacture practice requirements.
Keep existing stable lesson IDs as well as lab IDs, but model their relationship
explicitly so future lesson changes need not rename a lab.

Split the old documents into short purposes, rather than merging practical anchors.
General state/observation reasoning precedes the MDP formalization. Endings are
introduced in the first interaction lesson and revisited for tabular targets and
GAE. Probability/expectation precedes stochastic backups. Vectors, shapes and
chain-rule gradients precede neural updates. Logs and score gradients precede
policy-gradient derivations; the baseline proof precedes actor–critic and GAE.
PPO depends on GAE and its mathematical prerequisites, without requiring self-play,
Double DQN or PER. Its F1 comparison/application pages explicitly require the
earlier planning and DQN evaluation concepts they use.

Keep the optional discounted-contraction/value-iteration and Adam derivations
after their core explanations. All required tensor math, shaping telescoping,
baseline proof, score-function derivation and both PPO clipping branches stay core.
The roadmap keeps data/calibration, both dashboard stages and rule-based baselines.

## Intentional moves and corrections for authors

- Move the early exploration discussion into exploration and fresh stochasticity
  into sampling/modeling; retain curriculum hooks in tabular training application.
- Separate project-specific lap/tyre examples from generic teaching. Preserve their
  numerical witnesses, full transition traces and shared-dynamics warnings in the
  named application pages. The staged environment includes compound life, wear
  cap, fuel, weather, pit ordering, safety cars, masks and centered rewards.
- State reward-hypothesis and scalar-objective limitations; do not describe every
  possible goal as demonstrably equivalent to a scalar reward. Distinguish
  environment overfitting from reward hacking rather than treating them as synonyms.
- Keep the reward-centering proof and state fixed-horizon assumptions explicitly;
  variable-length trajectories can change rankings. Preserve gamma=1 finite-horizon
  reasoning separately from continuing discounted convergence assumptions.
- Preserve the three-race transition-matrix calculation, hazard examples, real DP
  state count and independent brute-force solver checks. State when noise=0 gives
  an exact expected cost and when nonlinear effects invalidate that conclusion.
- Preserve the hand-run TD/SARSA examples, epsilon probabilities including ties,
  encoder state counts and tyre-cliff aliasing. Add explicit interval-edge examples
  and Expected SARSA distinctions required by the delivered exercises.
- Preserve the tiny-network forward/gradient calculation, tensor warm-up, target
  storage versus detachment, replay and update timing. Do not conflate the warm-up's
  all-output mean squared loss with DQN's selected-action loss. Explain Huber/squared
  loss conventions where the project plan and exercises differ.
- Keep Double DQN's masked 1.5 versus 4.5 witness, dueling identifiability example
  and PER's [1,4,9] probabilities/weights. Follow delivered raw-priority and global
  importance-weight normalization contracts. Rewrite the old dueling centering
  explanation coherently instead of preserving its mid-example correction.
- Keep multi-car reward comparisons, blocking/undercut mechanics and the E1/E2/E3/
  E5/E6 ledger; do not substitute more training for a mechanically unreachable goal.
  Preserve shaping conditions, telescoping proof and terminal-potential limitations.
- Keep full rock-paper-scissors arithmetic, opponent mixtures, independent snapshots,
  recency sampling, first-opponent initialization, AEC cleanup and shuffled-pairing
  baseline. Apparent bimodality is not evidence of specialization by itself.
- Keep softmax-score arithmetic, baseline proof and numerical GAE recursion. Explain
  bootstrap eligibility separately from crossing an episode boundary: truncation can
  bootstrap its final observation without propagating advantages into a reset episode.
- Keep both PPO clipping branches, frozen old-policy likelihoods and the warning that
  clipping is not a hard ratio constraint. Keep build-versus-buy, vector rollout
  counts, worker-local masks, evaluation mode and fair-transition budgets (including
  the roughly 7.7× budget discrepancy and both proposed fixes).
- Preserve the distinction between ordinary pickle and SB3's cloudpickle mechanism.
  A blanket assertion that lambda factories fail in SubprocVecEnv is incorrect.
  Retain the actual local exercise and captured-resource failure. API-dependent
  explanations must be checked against primary documentation when authored in R2–R6.
- Rewrite historical implementation-plan references as proposed contracts and recorded
  findings, not proof of current production behavior. Preserve supplied exercise-file
  references and recorded-fixture provenance; no training is needed for R0.

## Progress and later milestones

No reading completion equivalence is approved in R0. New and substantially rewritten
readings remain unread unless R1 supplies an explicit reviewed equivalence decision.
The old full resource registry is retained so old section acknowledgments can be
validated without feeding their IDs into a v2 validator. Browser acknowledgment and
raw lab evidence have different identities and must be migrated separately.

R1 now provides v2 schema/source validation, reviewed route/equivalence/checklist maps,
resume translation and the tested write/rollback protocol; see
[the R1 authoring and migration contract](../content/README.md). R2 begins the shell
and the four `p1-loop` readings. R7 will enable migration after the replacement
content is delivered; the legacy snapshots here remain frozen.

## Reproduce and verify

From `prerequisite/`:

```powershell
python scripts/audit_reading_rebuild.py
python -m unittest discover -s tests -p test_reading_rebuild.py
```

`--write` captures the current v1 inputs and regenerates R0 artifacts. Do not use it
to overwrite the pre-rebuild baseline after changing or retiring legacy content.
Keep this snapshot frozen for migration. The default check is nonmutating, portable
and needs only Python's standard library. It checks concept order, optional-page
independence, unique reading routes, valid destinations and all practice mappings.
The tests independently inspect source headings and selected numerical/API witnesses,
and reject missing/duplicated practice, missing coverage and future/optional dependencies.
These checks establish inventory consistency; they do not certify unwritten content.

Completion verification: the nonmutating audit passed; all seven standard-library
tests passed; the combined R0, existing inventory and curriculum pytest selection
passed **32 tests**. `git diff --check` passed.

R0 files: this directory, `scripts/audit_reading_rebuild.py` and
`tests/test_reading_rebuild.py`. No published HTML/runtime, exercise math, ZIPs,
fixtures, learner storage or production F1 files changed. No browser test is needed
for these offline curriculum artifacts; real-browser checks begin at R2.
