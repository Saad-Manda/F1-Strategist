# R5: Neural value learning

R5 adds 22 authored readings: 18 required core, one optional Adam derivation, and
three F1 application readings. Four unchanged browser/Python practice pairs follow
the network, stability, Double/dueling and PER lessons. The course now has 80
authored readings; 54 later readings remain planned. The active site stays v1 until
R7, and preview origins with existing legacy learner data remain protected.

Run `python scripts/preview.py --readings --port 8050` and open
<http://127.0.0.1:8050/>. Add `--subdirectory` for `/site/`. Checkpoints acknowledge
learning and transfer, separately from production implementation verification.

## Content and coverage

`neural-coverage.json` maps 46 frozen source sections, including cross-module
references, to their existing canonical destinations. All 22 R5 destinations have
source coverage; the R0 snapshot and recorded exercise evidence are unchanged.

| Material | Replacement witnesses |
| --- | --- |
| Table to shared function | Nearby observations change together; corrected 172,800-state count; capacity versus generalization and the limits of tabular convergence arguments. |
| Tensor foundations | Explicit scalars/vectors/matrices, dot products, batch axes, transpose, dtype/device, broadcasting and singleton shapes. |
| Forward/loss/gradient | Original two-hidden-unit forward output 0.5; complete first-layer chain rule; pack loss 0.3125, weight/bias gradients and analytic SGD update; selected-action gather versus all-output supervision. |
| Optimizers | Complete pack-compatible update, accumulated gradients and held-out fixed-label fit; optional Adam moments, bias correction and scalar step. |
| Target/replay stability | Shared moving labels, independent copy versus alias, no-grad versus eval, hard/soft synchronization, 139-update half-gap witness, FIFO replacement sampling and warm-up/cadence. |
| Complete DQN | Executable masked optimizer update with checked [B,D]/[B,A]/[B] shapes, active terminal rows, detached targets/errors/weights, finite loss, clipping and optional Double/smooth-L1 settings. |
| Double DQN | Four-pair maximization-bias example; online [5,4,100], target [1,7,99], legal masks and targets 1.5 versus 4.5; first-index ties and terminal empty masks. |
| Dueling | Complete planned MLP, 35,655 parameters, V/A axes, effective mean centering, raw-head offset invariance and selected-action gradient coupling. |
| PER | Raw priority versus powered mass, [1,4,9] probabilities [1/6,1/3,1/2], global weights [1,1/2,1/3], supplied loss 2, correction identity and normalized expected loss 7/3, feedback/index/duplicate conventions. |
| F1 transfer | Raw/centered physical units, MSE versus smooth-L1 gradients, architecture and all mechanism combinations, project counters/configuration, tree insertion exponent bug, normalization differences and full-resume versus inference state. |
| Evidence | Four downloaded pack walkthroughs; live arithmetic versus the local supervised-fit CLI and recorded CPU chain ablations, exact chain budgets and limitations, independent integration checks and matched physical-cost evaluation. |

Deliberate corrections:

- A shared nonlinear value function does not inherit finite-table convergence;
  target/replay mechanisms mitigate problems without universally preventing failure.
- Double DQN mitigates a source of overestimation; it does not eliminate all bias.
  A plain multi-output network already shares its trunk.
- Mean subtraction uniquely defines effective deviations, not raw advantage outputs
  or all network parameters. The dueling V is an arithmetic mean over representable
  outputs, not automatically the optimal legal or policy value.
- Terminal masks never select a placeholder action. Nonterminal masks must be
  nonempty; multiplying an invalid maximum by zero risks NaN.
- Positive priority ensures support, not appearance in every batch. Global-buffer
  versus minibatch weight normalization are different; neither normalized estimator
  should be described as an unqualified exact unbiased correction.
- The supplied project plan reads maximum powered tree mass and powers again on
  insertion. The application documents the raw/mass boundary correction without
  modifying production files or the project implementation plan.
- Smooth L1 limits output-error derivatives, not all parameter gradients. Initial
  one-step labels need not already equal full-race returns. Reward centering is an
  engineering choice with common-horizon assumptions, not a performance diagnosis.
- The plan's epsilon decay is 200,000 decisions and beta advances on sample calls;
  Phase 4's 500,000-decision example and the lab's hard target cadence are distinct.
- Inference checkpoints and faithful training resume need different saved state;
  deterministic repeated starts are not independent scenario evidence.

API and mechanism references were checked against official PyTorch documentation
and the Double DQN, dueling and PER papers, linked at their relevant readings.
Teaching code is executed as numerical/contract tests; no comparison CLI, production
training or fixture-recording command is part of this implementation.

## Validation and handoff

The existing generic preview now exposes four authored modules. Home Continue walks
every required core/practice/application/checklist step; optional Adam does not gate
completion. The final authored-module boundary hands off to project Phase 6. No
required preview reading or practice handoff links to a legacy prerequisite page.

Automated checks passed: 47 Python tests across inventory, v2 contracts, reading
shells, all authored numerical examples, static delivery and isolated-copy
regeneration/packaging; all 98 JavaScript tests; all four unchanged R5 reference-pack
checkers; deterministic project/resource checks; R0 inventory and v2 metadata audits;
all 22 destination mappings; and `git diff --check`. The full Python selection took
706 seconds on Windows. After correcting the live-versus-recorded evidence
descriptions, all 26 final reading/numerical/static/portability checks passed in
678 seconds, including root/nested HTTP validation and isolated-copy reproducibility.

Real-browser review traversed all 18 core readings, four browser/Python handoffs and
three application readings. Witnesses reproduced the analytic SGD parameters,
independent target storage and FIFO retention, Double/vanilla and terminal targets,
dueling common-offset invariance, exact PER probabilities/weights and the broken
transformed insertion. Preparation remained incomplete until all checklist items
were acknowledged, then persisted after reload with optional Adam unacknowledged.
The authored boundary links to Phase 6 and labels the next learning module planned.
Nested `/site/` review confirmed reading completion survives navigation. At 390 and
320 px, the long DQN reading has no page overflow; drawer focus wraps both ways,
Escape restores its trigger, and Enter completes a reading into the correct lab.

R6 should author the remaining multiple-agent, self-play and policy-gradient/PPO
readings while preserving practice identities and the independent PPO dependency
path. R7 remains responsible for active navigation, migration and legacy retirement.
