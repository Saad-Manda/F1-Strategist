# R4: Planning and learning from samples

R4 adds 34 authored readings: 28 required core, one optional depth, and five
application readings. Planning has three lessons and three application readings;
Learning from samples has four lessons and two application readings. All seven
unchanged browser/Python practice pairs now have dedicated reading handoffs.
The course has 58 authored readings; 76 later readings remain planned.

Run `python scripts/preview.py --readings --port 8040` and open
<http://127.0.0.1:8040/>. Add `--subdirectory` for `/site/`. The active course remains
v1 until R7. Fresh preview progress uses the existing protected, locked v2 store;
legacy progress migration remains disabled. Preparation acknowledges learning and
transfer; it does not certify implementation of the production project.

## Educational coverage

`planning-tabular-coverage.json` maps frozen source sections to their canonical
destinations, including relevant cross-module sections. It supplements the R0
inventory without changing it. General concepts precede F1 application material.

| Material | Teaching evidence |
| --- | --- |
| Model versus samples, finite planning | A/B model, horizon boundary, reachable versus rectangular state counts, reward-max versus cost-min recurrence. |
| Backward induction and independent verification | Four-lap old-tyre timing: 52 optimum, 58 never-pit, hand cells and ties; executable solver checked against direct action-sequence enumeration and the unchanged A/B pack. |
| Optional value iteration | Discounted continuing one-state trace to 4, residual bound and assumptions; optional depth does not gate required work. |
| Expectations and rare outcomes | Weighted 17-second continuation, immediate cost inside expectation, 1% catastrophic branch, sensitivity threshold, conditional independence and geometric interruption duration. |
| Stochastic planning | Complete SC/weather/service-bit solver, zero terminal values, forced final service, adaptive-policy enumeration and recovery of the deterministic answer. |
| Markov weather | Correct empirical counts, within-episode transitions, row validation, inverse-CDF boundaries, distributions versus sampled traces, empirical uncertainty and held-out checks. |
| Oracle transfer | Complete state dimensions, information limits, known-weather versus Markov oracle inequality, real-scale weighted backup, shared dynamics, masks, timing and independent verification. |
| TD and Q-learning | Four hand updates, alpha/gamma distinction, convergence assumptions, complete pack-compatible update, true termination versus truncation, successor mask and negative-value traps. |
| Exploration | Discovery failure, exact epsilon/tie probabilities, inverse-CDF selector, evaluation freeze, schedule counted in decisions, seed streams and visitation limitations. |
| SARSA | Three hand episodes, sampled commitment, truncation cleanup, Expected SARSA calculation, complete shared learner shell and collector, interrupted pending-action failure. |
| Discretization | Correct Cartesian count, half-open boundaries and final endpoint, NumPy insertion semantics, float32 neighbors, full-key cliff collision, encoder version and semantic validation. |
| Tabular project transfer | Complete 16-vector decoder, eight-field key, used-mask bits, legal actions, serialization, centered reward units, curriculum switches, frozen evaluation and oracle-relative gap. |

Deliberate corrections to the original material:

- The stated DP product is 726,000, and the eight-dimensional tabular product is
  172,800. Report implemented dimensions and memory, not the old inconsistent totals.
- An oracle's expected-cost information bound has the opposite reward sign. It is
  conditional on aligned tasks and information, can be an equality, and is not a
  pathwise performance guarantee on every sampled race.
- Zero-noise dynamics equal a stochastic expectation only under the relevant
  additive/linearity assumptions; clipping supplies a concrete counterexample.
  Safety cars and wet initial states do not imply universal monotonic cost changes.
- Constant alpha, an exploration floor and a finite training budget do not prove
  exact Q-learning convergence or adequate visitation.
- The correctly implemented terminal SARSA toy need not leak pending actions.
  Demonstrate an interrupted collector or broken truncation cleanup instead.
- Epsilon counts the random branch; its nongreedy probability is smaller. Zero
  epsilon can still randomize tied maxima under the unchanged pack convention.
- Age-bin collisions must match the entire key. A finer encoder cannot restore
  information already removed from the raw observation.
- Centering reward can help numerical scales and initialization, but it does not
  inherently speed relative fixed-target convergence or fix inadequate visitation.

Primary references checked: Watkins and Dayan's Q-learning paper, Gymnasium's time
limit guidance, and NumPy's digitize documentation, linked at the relevant readings.
Teaching code executes in prerequisite order without running a production training
experiment. The Python and browser packs retain their original contracts and bytes.

## Preview and verification

Available-module labels and preparation UI now derive from the registry. Each
checkpoint separately tracks its application pages, checklist and learning/practice
requirements. Handoffs derive the following project stage: Planning → Phase 4,
Learning from samples → Phase 5. Completed modules continue into the next authored
learning module; the boundary before planned neural readings goes to project work.
Lab review links and Before-the-lab links lead to dedicated lesson/readings routes.

Checks passed: 35 focused Python checks (R0, v2, reading routes and executed
Foundations/R4 examples); all 97 JavaScript checks; all seven unchanged R4 reference
pack checkers; deterministic project/resource audits; R0 inventory and dependency
audit; complete coverage of all 34 R4 destinations; and `git diff --check`.
The complete 39-check Python selection passed in 274 seconds. After adding the
stationary-distribution derivation and its numerical witness, the fixed-input
reading/math/static-delivery/isolated-copy selection passed all 18 checks in 233
seconds. These include root/nested HTTP, archive validation, standalone generation,
JavaScript checks and reproducible packaging. Publication validation correctly
rejects the 76 still-planned readings.

Real-browser evidence: all 28 required R4 readings followed their numbered order
into the seven unchanged lab pages. A/B rows chose DIRECT at one decision and VIA
at two; the stochastic row tied at p=1/3; Markov marginals reached [0.7,0.3]; TD gave
2.75 with illegal 99 excluded; the epsilon row was [0.9,0.1,0]; SARSA committed and
executed slip with target −10 versus maximum 6; split bins put 0.5 in the higher bin.
Explicit browser acknowledgment, Python explanation/verification and next-lesson
controls worked across all seven practice pairs. Three Planning and two tabular
application acknowledgments reached their checkpoints with 3/3 and 2/2 counts.
Preparation remained incomplete until checklist evidence was added, then became
complete for both modules and persisted on revisit. Optional value iteration had
no acknowledgment button and did not gate either module. No production training
or browser comparison training was initiated for the walkthrough.

Nested-mount checks at 390/320 px showed no horizontal page overflow on the long
stochastic solver. The settled mobile drawer wrapped its availability label,
highlighted the current reading, focused Close, made main inert, wrapped Shift+Tab,
and restored the toggle on Escape. Enter acknowledged the reading and opened its
browser practice. The viewport was restored after testing.

R5 should author neural value learning while preserving the R0 snapshot, practice
contracts and preview-only activation until R7. No production code, exercise math,
fixture or pack/archive bytes changed. No training, deployment, staging, commit or
push was performed.
