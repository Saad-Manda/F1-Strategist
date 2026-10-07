# R6: Multiple agents, self-play and policy gradients

R6 adds 54 authored readings: 43 required core readings and 11 F1 applications.
Eleven lessons include ten unchanged browser/Python practice pairs and the
theory-only policy-probability lesson. All 134 registered readings are now authored;
strict source publication validation passes. The active course remains v1 until
R7 switches navigation and enables reviewed migration.

Run `python scripts/preview.py --readings --port 8060` from `prerequisite/` and open
<http://127.0.0.1:8060/>. Add `--subdirectory` for `/site/`. Preview progress is
separate from production implementation verification and protects legacy origins.

## Content and preservation

`advanced-coverage.json` maps 178 frozen source sections, including cross-module
references, to canonical destinations. It preserves source IDs, dispositions,
reasons and glossary handoffs; every one of the 54 R6 destinations has coverage.
The R0 inventory and all exercise, reference solution, fixture and pack ZIP bytes
remain unchanged.

| Material | Replacement witnesses |
| --- | --- |
| Joint reward and credit | All four joint choices; shared reward 3 versus contributions 2 and 1; nonlinear counterexample; individual/team objectives and counterfactual assumptions. |
| Reward shaping | Base objectives versus proxies; finite discounted telescope with endpoint term; route returns at discounts 1 and .5; failure potential 10 and mismatched-discount counterexamples. |
| Opponent effects | Connected CROSS expectation .6 versus −.6; disconnected value 1; missing mechanics, hidden state and policy change; fixed reactive opponents need not imply nonstationarity. |
| F1 interaction | 19 features, first-layer parameter change, five fixed rivals, dirty-air and passing formulas, time/reward defects; copied two-car intervention with blocked and released outcomes. |
| Game theory | Full RPS matrix, mixed expected payoff, uniform equilibrium and exploitability; cyclic best responses, snapshot independence and limits of neural self-play convergence claims. |
| Historical pools | Weighted sampling, overflow-safe normalization, frozen snapshots, FIFO, project recency weights, one-entry pool edge case and opponent-type initialization. |
| Evaluation | Stable-ID pairing, scenario versus training-seed uncertainty, sample standard error, stratified comparisons, fixed schedules, actual Parallel/AEC lifecycle checks and transition counting. |
| Policy gradients | Stable softmax/log probabilities, masks, score identity, trajectory likelihood-ratio derivation and discount convention; complete detached REINFORCE update and hand-calculated gradient. |
| Baselines and actor–critic | Expected-gradient proof; variance 6.25 → 0 with the good baseline versus 56.25 with a poor baseline; action-dependent bias; exact versus sampled advantage; separate actor/critic gradient paths. |
| GAE | Two-step and four-step hand examples, lambda extremes, complete reverse recursion, batch/time shape convention, separate bootstrap and trace masks, terminal/time-limit/cutoff boundaries. |
| PPO | Independent frozen rollout storage; likelihood ratios; all four sign/ratio branches, loss .05 and log-probability gradients; clip fraction versus flat branches, sampled KL, unsafe large steps and full minibatch cycle. |
| F1 PPO transfer | Library choice, masked collection/evaluation, VecEnv final observations, timeout conventions, main guard and serialization, complete bounded spawn script, fair experience budgets and recorded integration provenance. |

The required policy-gradient path follows probability/gradient tools → REINFORCE →
baseline/actor–critic → GAE → PPO, with earlier Foundations/neural/TD prerequisites.
Its transitive prerequisite graph contains no multiple-agent or self-play lessons.
Optional depth cannot supply a missing required prerequisite.

## Corrections and limits retained

- Team reward does not identify causal contributions. A dense gap-change reward can
  telescope under consistent undiscounted measurement; arbitrary bonuses generally
  change the task. Shaping invariance needs the correct discount and boundary term.
- Unblocked tyre/weather costs can still produce pit-timing effects. The specific
  blocked-traffic mechanism needs a connected joint transition; a pace cap alone
  does not implement full crossing-order resolution. The traffic witness starts
  from fresh inputs and checks an intervention rather than asserting learning.
- The Phase 8 sketch's independent single-car environments do not automatically
  inherit Phase 6 shared traffic mechanics. Episode pools differ from averaging
  network weights or independently mixing actions. A one-entry recency pool needs
  an explicit special case; random network initialization is not a uniform policy.
- Simultaneous API dictionaries do not prove information-safe simultaneous choices.
  Parallel transitions retain final reward/flag keys even when no agents remain;
  an AEC selected dead agent takes `None`, including truncations.
- For the explicitly discounted start-state objective, the sampled score weight is
  gamma^t times return-to-go. Practical transition-weighting conventions are stated
  separately. An action-independent baseline preserves expectation under the given
  assumptions; a poor baseline can increase variance.
- A detached actor advantage prevents an unintended baseline derivative. A zero
  scalar actor loss can still have a nonzero gradient. Shared-trunk critic updates
  remain intentional, and exact advantages differ from sampled residual estimates.
- Truncation bootstraps from the final observation while cutting episode recursion.
  Reset value 100 produces the wrong residual 93.7 rather than 3.7. SB3's timeout
  reward adjustment and an explicit bootstrap are alternative collector conventions;
  applying both double-counts the endpoint value.
- PPO clipping removes particular incentives; it does not bound all actual ratios
  or parameter steps. All four pack ratios are outside the interval, but only two
  objective branches are flat. Frozen old tensors need independent storage as well
  as detachment, and rollout reuse has a finite collection/update cycle.
- Ordinary pickle and SB3's cloudpickle wrapper differ: lambda failure under one
  does not prove failure under the other. Captured locks can fail even with
  cloudpickle. Worker-local resources/masks, a main guard, bounded waits and cleanup
  are demonstrated by an actual spawn script without a training run.
- DQN's 5,000 × 52 = 260,000 decisions and PPO's 2,000,000 requested transitions are
  unequal budgets. Full 1,024-transition PPO rollouts yield 2,000,896 actual samples;
  workers do not multiply `total_timesteps` again. Compare common experience counts,
  tuning/compute allowances and matched physical evaluation; descriptive unequal
  runs cannot identify a fixed-budget algorithm effect.
- Recorded deterministic repeated starts are not independent race uncertainty.
  Dense lap-time reward, rare pit actions and PER error are distinct concepts;
  reward centering and normalization are choices requiring justified conventions.

API references link to the official
[MaskablePPO documentation](https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html),
[SB3 VecEnv documentation](https://stable-baselines3.readthedocs.io/en/master/guide/vec_envs.html),
[PettingZoo API](https://pettingzoo.farama.org/api/parallel/) and
[Python multiprocessing documentation](https://docs.python.org/3/library/multiprocessing.html),
plus the original shaping, GAE and PPO papers at relevant readings. Current online
documentation is distinguished from the fixture's recorded versions and the locally
tested Python 3.12.7, NumPy 2.5.1, PyTorch 2.13.0+cpu, Gymnasium 1.3.0,
PettingZoo 1.27.0, SB3/sb3-contrib 2.9.0 and cloudpickle 3.1.2.

## Validation and R7 handoff

Passed on fixed site/source inputs:

- 64 Python tests covering frozen inventory, v2 contracts, reading shell, all
  authored numerical examples, static delivery and isolated-copy regeneration,
  root/nested HTTP checks and reproducible packaging (952.60 seconds on Windows).
- All 99 JavaScript tests, including the full required-course journey, all 25 lab
  identities, checkpoint separation, revocation and independent PPO prerequisites.
- All ten unchanged R6 reference-pack checkers; deterministic project/resource
  checks; R0 inventory audit; v2 strict publication check; and `git diff --check`.
- Seventeen new numerical/API tests execute all R6 teaching-code blocks, test
  gradients against analytic values and pack contracts, run actual Parallel/AEC
  conversion and DummyVecEnv final-observation behavior, test serialization and run
  the standalone ordinary-spawn example. No comparison training CLI was run.

Tests that previously assumed some readings remained planned now construct a
planned-reading case explicitly, retaining rejection and migration-equivalence
coverage after the course becomes fully authored. The preview's availability label
now correctly states that all learning modules are authored.

Real-browser review traversed all 43 core and 11 application reading sequences,
the theory-only probability handoff, ten browser/Python handoffs and all three
preparation checkpoints. Checkpoints require separate acknowledgments and PPO
preparation persisted after reload. The GAE time-limit witness reproduced
[4.73,3.7]; PPO's negative branch reproduced −.8 and −1.3. Preview lab explanations
were explicitly labeled reviewer QA, using the checked reference implementations;
they are not evidence that a learner completed their starter exercise.

At the nested mount, the long worker example has no document overflow at 390 and
320 px; its code block scrolls locally. Drawer focus wraps in both directions,
Escape restores the trigger, and Enter completes the application into its exact
next route. A screenshot confirmed the narrow reading layout. Browser automation
had intermittent timeouts; saved state was inspected before continuing, and the
remaining walkthrough succeeded after reconnection. This review does not replace
R7 migration/cache-switch testing or R8's full novice journey and final delivery QA.

R7 should make the v2 registry authoritative, migrate validated existing/imported
progress under the shared lock/transaction protocol, update all public navigation
and lab return links, generate reviewed relocations, retire legacy generators and
coordinate cache versions. Active v1 remains intact until that work. No production
F1 code, exercise math, fixture or pack/archive bytes changed; no production
training, fixture recording, deployment, staging, commit or push was performed.
