# R3: Foundations and project preparation

The preview now contains all five Foundations lessons: 19 required core readings,
one optional depth reading, four unchanged browser/Python practice pairs, and four
F1 application readings. Twenty new fragments extend R2's four readings. The other
110 readings remain planned. The active published registry and existing Home,
module, lesson and lab pages remain v1 until R7; the new probability overview has
no v1 predecessor and is generated alongside the dedicated reading routes.

Run `python scripts/preview.py --readings --port 8030` and open
<http://127.0.0.1:8030/>. Add `--subdirectory` to review the same journey at `/site/`.
Use a fresh preview origin: the R2 storage guard still protects legacy learner data,
and migration is intentionally enabled only at R7. Saving uses the existing locked,
validated transaction protocol. Visiting, Previous, Next and sidebar navigation do
not acknowledge readings. Application completion is separate from lesson reading
counts; optional depth does not require acknowledgment or gate completion.

## Content and coverage review

`foundations-coverage.json` inventories every frozen Phase 1 section with its R0
destination, authored targets and explicitly later-milestone targets. It is a review
record alongside the immutable source inventory, not a replacement for that inventory.
The following records the actual teaching witnesses and deliberate changes.

| Original material | Replacement evidence and disposition |
| --- | --- |
| Agent loop, reward hypothesis, episodic/continuing tasks | R2 chain contract; `reward-return`, `horizons`; qualify the reward hypothesis as a modeling proposal and retain proxy exploitation. |
| Exploration/exploitation and fresh stochasticity | Fresh sampling and information limits are taught in `race-dynamics`; exploration algorithms retain the R0 placement in R4, not an assumed prerequisite of Foundations. |
| MDP tuple, Markov property, state/observation | Delivery-chain transition table, hidden-switch histories, stochastic Markov example, sufficient summaries, intrinsic deadline and belief/memory alternatives across the four state readings. |
| Returns and discount | [2, −1, 4] suffixes [5, 3, 4] and discounted [2.5, 1, 4]; reverse implementation, finite/continuing bounds, deadline-dependent decisions, positive scaling and fixed-offset assumptions. |
| Policies, masks, V/Q and Bellman equations | The unchanged A/B pack's Q = [3, 5, 99], half-policy value 4 versus legal optimum 5; general stochastic reward/successor equations, terminal reward once, zero terminal continuation, finite time index and evaluation versus improvement. |
| Probability needed by those equations | Required theory-only lesson teaches normalized outcomes, joint/conditional probability, independence assumptions, expectation, sample averages and rare-event counterexample before stochastic backups. |
| Bellman convergence depth | Optional fixed-point trace 0 → 1 → 1.5 → 1.75 → 1.875, contraction assumptions and residual bound; no later required reading depends on this proof. |
| Generic GridWorld construction | Consolidate repeated class boilerplate into the complete chain and race toy; retain 5×5 normalized coordinates, boundary moves, eight-step −8 goal trace versus fifty-step −50 external-cap trace in `environment-verification`. Use Gymnasium's checker and accurately allow coincident flags. |
| Piece-by-piece race toy | Retain one-compound and quadratic compound tradeoffs; complete final pure timing/transition functions, cliff/fuel/weather/warmup/pit/SC branches, fresh geometric hazard sampler and assembled checked Gym environment. |
| Project vector, actions and complete pit example | `environment-contract` retains all 16 indices, six labels, five mask rules, seed/options/info contracts and the MEDIUM→HARD trace. Explicit inclusive remaining-lap convention avoids the old mixed lap labels. |
| Reward scale, offsets, gamma one | `reward-units` derives negative seconds and penalized return, 52-lap 4784 shift, 208-second ranking difference, transparent wrapper, discounted ranking reversal and unequal-length counterexample. Neural-specific optimization follows in R5. |
| Pure dynamics and stateful wrapper walkthrough | Eight planned dynamics responsibilities, reset/step/observation/info separation, no mutation or hidden future leakage, expectation versus noise removal, and ten independently testable contract groups. |
| Original glossary and phase index | Concepts are introduced on the required path; the original reference and roadmap source remain frozen for R7's course-wide replacement. Setup, dashboard, baseline and deployment stages remain on the preview roadmap. |

Corrections are deliberate:

- A bounded 16-feature observation is not automatically a full Markov state when
  weather scenario, interruption duration or capped age omits relevant information.
- The quadratic cliff contribution is capped; linear wear continues: A ages 10,
  16 and 100 cost 4.5, 4.8 and 9.0 in the toy.
- Centering negative time adds a positive baseline. Ranking preservation assumes a
  common horizon (or common discounted offset); early aborts and variable length
  require their own analysis. A −500 backstop alone is not proof of constraint safety.
- Gymnasium space membership does not enforce a custom eligibility mask. Generic
  `check_env` samples unmasked actions; the final toy accepts redundant pits and
  tests policy masking separately. The project must define bypass behavior explicitly.
- Different seeds can produce identical sampled schedules; repeated fresh draws
  should be evaluated statistically, not by asserting pairwise inequality.
- A fixed SC lap-time branch replaces green timing rather than adding to it; pit
  loss still counts. Removing noise returns an exact expectation only when the model
  actually computes it, particularly around nonlinear calculations.

API references were checked against Gymnasium's official environment, Taxi masking,
wrapper and checker documentation. Complete teaching code is executed by
`test_foundations_readings.py`; the unchanged pack implementations supply independent
state, return and value witnesses. No training or production F1 code is involved.

## Preview behavior and validation

The generator now derives numbering, lesson goals/prerequisites, theory-only practice
absence, optional-depth labels, application navigation and lab scripts from the registry.
Each available lab keeps its existing experiment, controls, downloads and seven saved
fields. Its Python continuation names the next lesson, or the module's first application.
Home Continue traverses required readings, browser, verified Python, applications and
checkpoint; it hands completed Foundations to project work rather than a planned page.

The checkpoint saves its three unchanged checklist meanings separately. Preparation
is complete only with required core readings, all applicable browser/Python practice,
all application readings and the checklist. It explicitly does not certify production.
Optional depth never gates it. The handoff retains dashboard Phase 2, baselines Phase 3
and the later Planning module.

Checks: 28 focused Python checks (R0 inventory, v2 schemas, reading routes and executed
teaching witnesses); all 96 JavaScript checks, including exhaustive available-path
Continue traversal and preparation/revocation; deterministic project checks and all
four unchanged Foundations reference-pack checkers. Root/nested static link checks
cover every authored route, overview, application and practice handoff without JS.
The fixed-input reading/math/static-delivery/isolated-copy selection passed all 11
checks in 405 seconds, including archive/root/nested HTTP validation, complete
standalone generation, JavaScript checks and reproducible packaging. R0 audit and
`git diff --check` passed. All four reference pack checkers passed without regeneration.

Real browser evidence: fresh root and nested preview origins; theory-only last reading
enters lesson 1.5; unchanged value experiment shows Vπ = 4 versus V* = 5; explicit
browser completion leads to Python; explanation/verification persists and its next link
opens application 1; four explicit application acknowledgments reach the checkpoint
with 4/4 application count. Checking all three statements while earlier learning is
unfinished correctly keeps preparation in progress. At 390 and 320 px, the nested
Bellman page has no horizontal page overflow. Drawer opens as a modal, focuses Close,
Shift+Tab wraps to the final visible summary, and Escape restores the toggle.
The final root walkthrough additionally followed every core reading sequence and
all four practice handoffs. The switch experiment reproduced FLIP/CLAIM's differing
hidden futures; the return experiment showed [2.5, 1, 4]. With all required learning
and practice acknowledged, the checkpoint changed to preparation complete, still
explicitly requiring production verification. Optional depth remained unacknowledged.
Home then offered the project-stage continuation. Keyboard completion persisted at
the nested mount. Preview services were restarted with the final generated content.

R4 should author Planning and tabular content using this generic shell and availability
logic. Future project handoffs should derive the following project stage rather than
reuse Foundations' Phase 2 link. Publish validation still correctly rejects planned
content. Do not migrate saved v1 reading acknowledgments before R7 or overwrite the
frozen legacy inventory when new routes are generated.
