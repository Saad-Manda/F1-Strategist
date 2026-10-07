# R0 teaching sequence

Generated from `sequence.txt`. These are planned purposes, not published reading bodies.

Reading IDs name concept clusters. `requires`/`teaches` in `outline.json` form the reading-level prerequisite graph.
Core readings never depend on further-depth pages. Practice follows the final core reading.

## 1 · Foundations (project phase 1)

### 1.1 · Build the interaction loop (`p1-loop`)

Prerequisite lessons: basic Python only.

Practice: `p1-loop` → `labs/phase-1/p1-loop.html`; existing Python pack follows.

- **Agents, environments and episodes** (core, about 6 minutes) · `readings/p1-loop/agent-environment-loop.html`
  Trace a toy delivery agent through a complete episode; distinguish agent, environment and policy without notation.
- **One step: actions, observations and rewards** (core, about 6 minutes) · `readings/p1-loop/one-step.html`
  Record a delivery transition and explain each field, including the next observation and reward units.
- **Resetting and ending an episode** (core, about 6 minutes) · `readings/p1-loop/episode-endings.html`
  Trace success versus a time limit using reset and the five step outputs; distinguish termination, truncation and collector cutoff before targets appear.
- **Spaces and the environment contract** (core, about 6 minutes) · `readings/p1-loop/spaces-and-contract.html`
  Construct a tiny GridWorld contract, validate shapes/dtypes and reset seeds, explain info and render_mode, and locate check_env.

### 1.2 · Describe state and observations (`p1-state`)

Prerequisite lessons: p1-loop.

Practice: `p1-state` → `labs/phase-1/p1-state.html`; existing Python pack follows.

- **State versus observation** (core, about 6 minutes) · `readings/p1-state/state-observation.html`
  Compare two identical observations with different hidden battery charge; distinguish simulator state from what the agent sees.
- **When the present is enough** (core, about 6 minutes) · `readings/p1-state/markov-property.html`
  Calculate different next-step outcomes for the hidden-charge example and explain why omitted information matters.
- **A model of decisions and outcomes** (core, about 6 minutes) · `readings/p1-state/mdp-model.html`
  Introduce the MDP tuple one symbol at a time using a delivery transition table; defer calculating expectations to the probability lesson.
- **Working with incomplete observations** (core, about 6 minutes) · `readings/p1-state/missing-information.html`
  Compare adding a sensor, using observation history and a belief-state idea; explain why an encoder cannot invent missing information.

### 1.3 · Reason about rewards and returns (`p1-return`)

Prerequisite lessons: p1-loop.

Practice: `p1-return` → `labs/phase-1/p1-return.html`; existing Python pack follows.

- **Reward versus accumulated return** (core, about 6 minutes) · `readings/p1-return/reward-return.html`
  Sum three delivery rewards; discuss the reward hypothesis as a modeling assumption and show a proxy objective that fails.
- **Discounting step by step** (core, about 6 minutes) · `readings/p1-return/discounting.html`
  Calculate a three-step discounted return and distinguish a discount factor from a learning rate.
- **Finite and continuing horizons** (core, about 6 minutes) · `readings/p1-return/horizons.html`
  Compare a finite undiscounted task with a continuing discounted task; state bounded-reward assumptions and time-in-state requirements.
- **Computing returns and their units** (core, about 6 minutes) · `readings/p1-return/return-calculation.html`
  Implement reverse return accumulation; distinguish realized return from expected return and trace reward centering on fixed versus variable horizons.

### 1.4 · Probability and expectation for decisions (`p1-probability`)

Prerequisite lessons: p1-state, p1-return.

Practice: Theory only; continue to the next lesson without a browser/Python requirement.

- **Probabilities over possible outcomes** (core, about 6 minutes) · `readings/p1-probability/probability-outcomes.html`
  Normalize a two-outcome table and calculate joint probabilities under an explicit independence assumption.
- **An average weighted by probability** (core, about 6 minutes) · `readings/p1-probability/weighted-expectation.html`
  Calculate expected reward and expected continuation separately; compare sample averages with exact model averages and rare outcomes.

### 1.5 · Evaluate policies and actions (`p1-values`)

Prerequisite lessons: p1-probability.

Practice: `p1-values` → `labs/phase-1/p1-values.html`; existing Python pack follows.

- **Policies and legal actions** (core, about 6 minutes) · `readings/p1-values/policies-legal-actions.html`
  Specify deterministic and stochastic policies; calculate legal-action probabilities and tie handling with an action mask.
- **State values and action values** (core, about 6 minutes) · `readings/p1-values/state-action-values.html`
  Compare two delivery actions using their expected returns; define V and Q only after the examples.
- **One Bellman backup** (core, about 6 minutes) · `readings/p1-values/bellman-backup.html`
  Derive the return decomposition and calculate a backup with reward and two successor values; explain terminal continuation and finite gamma=1.
- **Expectation versus maximization** (core, about 6 minutes) · `readings/p1-values/expectation-maximization.html`
  Compute policy evaluation and greedy improvement from the same table; separate expectation over outcomes from maximization over legal actions.
- **Evaluation and optimality** (core, about 6 minutes) · `readings/p1-values/evaluation-optimality.html`
  Compare a policy Bellman equation with an optimality equation; recap masking and time-dependent finite-horizon values.
- **Why repeated backups can converge** (further-depth, about 6 minutes) · `readings/p1-values/bellman-fixed-points.html`
  Work a discounted contraction example and distinguish its assumptions from finite-horizon backward induction.

### Module application and project preparation

- **Building the F1 environment contract** (application, about 8 minutes) · `applications/foundations/environment-contract.html`
  Map the 16-feature observation, six actions, masks, seeding and ending flags to the toy contract; retain the complete step trace.
- **Composing one race transition** (application, about 8 minutes) · `applications/foundations/race-dynamics.html`
  Trace compound pace/life, capped wear cliff, fuel, weather, pit-lap ordering and fresh safety-car sampling through pure shared dynamics.
- **Reward units and the race objective** (application, about 8 minutes) · `applications/foundations/reward-units.html`
  Prove negative lap-time accumulation and fixed-horizon centering numerically; state variable-length caveats and avoid describing a plan as executed evidence.
- **Wrapping and verifying shared dynamics** (application, about 8 minutes) · `applications/foundations/environment-verification.html`
  Explain the stateful Gymnasium wrapper, pure dynamics, environment tests and readiness checkpoint; introduce dashboard and rule-based baseline handoffs.

## 2 · Planning and uncertainty (project phase 3.5)

### 2.1 · Plan with a known finite model (`p35-backward`)

Prerequisite lessons: p1-values.

Practice: `p35-backward` → `labs/phase-3.5/p35-backward.html`; existing Python pack follows.

- **Planning versus learning** (core, about 6 minutes) · `readings/p35-backward/planning-learning.html`
  Compare access to a transition model with access to sampled transitions using the same tiny task.
- **A known finite model** (core, about 6 minutes) · `readings/p35-backward/finite-model.html`
  Enumerate time-indexed states and legal actions, assign terminal values and count states before solving.
- **Backward induction by hand** (core, about 6 minutes) · `readings/p35-backward/backward-induction.html`
  Preserve the worked pit-now versus stay-out example and show why greedy one-step decisions fail.
- **Implement and independently verify a solver** (core, about 6 minutes) · `readings/p35-backward/verify-solver.html`
  Compare a tiny backward solver with brute-force action sequences; include terminal and no-legal-action cases.
- **Backward induction and value iteration** (further-depth, about 6 minutes) · `readings/p35-backward/value-iteration.html`
  Work a discounted iterative example and contrast stopping rules with an acyclic finite horizon.

### 2.2 · Plan over uncertain outcomes (`p35-stochastic`)

Prerequisite lessons: p35-backward, p1-probability.

Practice: `p35-stochastic` → `labs/phase-3.5/p35-stochastic.html`; existing Python pack follows.

- **Recap probability and expectation** (core, about 6 minutes) · `readings/p35-stochastic/expectation-refresher.html`
  Recompute a hazard/no-event weighted average and state conditional independence before combining hazards and weather.
- **Weighted outcome backups** (core, about 6 minutes) · `readings/p35-stochastic/weighted-backups.html`
  Calculate a complete stochastic Bellman cell; keep successor-dependent costs inside the correct expectation.
- **Rare outcomes and risk** (core, about 6 minutes) · `readings/p35-stochastic/rare-outcomes.html`
  Compare average cost with a rare costly outcome; distinguish risk-neutral optimization from a changed risk objective.
- **A complete stochastic planning example** (core, about 6 minutes) · `readings/p35-stochastic/stochastic-solver.html`
  Extend the independently checked solver with safety-car hazard, legal masks and a second random process; validate probability sums.

### 2.3 · Model and sample changing conditions (`p35-markov`)

Prerequisite lessons: p35-stochastic, p1-state.

Practice: `p35-markov` → `labs/phase-3.5/p35-markov.html`; existing Python pack follows.

- **Transition matrices and chains** (core, about 6 minutes) · `readings/p35-markov/transition-matrix.html`
  Count and normalize the existing three-race 3-by-3 weather example; discuss unobserved rows rather than dividing by zero.
- **Sampling is not knowing the future** (core, about 6 minutes) · `readings/p35-markov/sampling-not-foresight.html`
  Trace seeded sampling from a fitted chain and distinguish a sampled rollout from privileged future information.
- **Variation between rollouts** (core, about 6 minutes) · `readings/p35-markov/rollout-variability.html`
  Compare multiple traces and distributions of returns; distinguish deterministic calculations from stochastic evaluation.
- **Checking transitions against the model** (core, about 6 minutes) · `readings/p35-markov/empirical-checks.html`
  Compare empirical transition frequencies with the specified matrix using sample counts and uncertainty.

### Module application and project preparation

- **Modeling the F1 planning state** (application, about 8 minutes) · `applications/planning/oracle-model.html`
  Preserve DP state-size arithmetic, hazard/weather assumptions, masks and the noise=0 expectation argument with its limitations.
- **An achievable oracle and a foresight bound** (application, about 8 minutes) · `applications/planning/oracle-bound.html`
  Distinguish Oracle A and B, cost versus reward signs, a real-scale backward cell and the optimality-gap metric.
- **Shared dynamics and independent oracle checks** (application, about 8 minutes) · `applications/planning/oracle-verification.html`
  Map solver/weather modules and rollout harness to brute force, probability and consistency checks; explain checkpoint evidence.

## 3 · Learning from samples (project phase 4)

### 3.1 · Learn action values from transitions (`p4-td`)

Prerequisite lessons: p1-values.

Practice: `p4-td` → `labs/phase-4/p4-td.html`; existing Python pack follows.

- **Learning from transitions** (core, about 6 minutes) · `readings/p4-td/sampled-learning.html`
  Replace an exact expectation with a sampled transition; explain bootstrapping as estimating from an estimate.
- **Target, error and update** (core, about 6 minutes) · `readings/p4-td/td-error.html`
  Calculate target, TD error and learning-rate update separately on a three-state toy.
- **Q-learning step by step** (core, about 6 minutes) · `readings/p4-td/q-learning.html`
  Preserve four hand-run updates, distinguish learning rate and discount, and state finite-table convergence conditions without promising a practical guarantee.
- **Terminal targets and legal actions** (core, about 6 minutes) · `readings/p4-td/terminal-masked-targets.html`
  Contrast termination, time-limit bootstrap and cutoff; calculate a masked maximum and handle terminal rows with no legal successor.

### 3.2 · Discover actions through exploration (`p4-explore`)

Prerequisite lessons: p4-td.

Practice: `p4-explore` → `labs/phase-4/p4-explore.html`; existing Python pack follows.

- **Why greedy discovery fails** (core, about 6 minutes) · `readings/p4-explore/greedy-discovery.html`
  Show a never-visited rewarding action under greedy-only selection.
- **Epsilon-greedy probabilities** (core, about 6 minutes) · `readings/p4-explore/epsilon-probabilities.html`
  Derive probabilities including the exploratory share on greedy actions, ties and legal-action masks.
- **Behavior and evaluation policies** (core, about 6 minutes) · `readings/p4-explore/behavior-evaluation.html`
  Compare exploratory training with greedy evaluation using separate random streams and recorded evidence.
- **Ties, masks and exploration schedules** (core, about 6 minutes) · `readings/p4-explore/exploration-schedules.html`
  Calculate the existing linear-decay example; enforce masks inside random sampling and explain reproducibility limits.

### 3.3 · Compare on-policy and off-policy targets (`p4-sarsa`)

Prerequisite lessons: p4-explore.

Practice: `p4-sarsa` → `labs/phase-4/p4-sarsa.html`; existing Python pack follows.

- **Which policy supplies the target?** (core, about 6 minutes) · `readings/p4-sarsa/policy-targets.html`
  Compare Q-learning's maximum with the action actually sampled by a behavior policy.
- **Sampled SARSA** (core, about 6 minutes) · `readings/p4-sarsa/sampled-sarsa.html`
  Trace the risky-push versus safe-pit example and pre-commit the next action before changing Q.
- **Expected targets** (core, about 6 minutes) · `readings/p4-sarsa/expected-sarsa.html`
  Calculate Expected SARSA with epsilon-greedy probabilities and distinguish it from sampled SARSA and Q-learning.
- **A fair small comparison** (core, about 6 minutes) · `readings/p4-sarsa/algorithm-comparison.html`
  Align seeds, masks, reward units and evaluation policies; preserve the shared learner-shell exercise and detect target leakage.

### 3.4 · Encode observations in a table (`p4-bins`)

Prerequisite lessons: p4-td, p1-state.

Practice: `p4-bins` → `labs/phase-4/p4-bins.html`; existing Python pack follows.

- **Representing observations in a table** (core, about 6 minutes) · `readings/p4-bins/table-representation.html`
  Calculate the existing Cartesian state count and explain table growth versus generalization.
- **Interval boundaries** (core, about 6 minutes) · `readings/p4-bins/interval-boundaries.html`
  Work boundary, overflow and underflow cases; state the convention for digitize/searchsorted explicitly.
- **Aliasing training cannot fix** (core, about 6 minutes) · `readings/p4-bins/state-aliasing.html`
  Preserve the tyre-cliff bin collision and show two states sharing a code but requiring different actions.
- **Choosing and testing an encoder** (core, about 6 minutes) · `readings/p4-bins/encoder-checks.html`
  Test feature order, edges and distinct strategically important states; distinguish quantization from missing physical state.

### Module application and project preparation

- **Mapping observations and masks to the Q-table** (application, about 8 minutes) · `applications/tabular-learning/tabular-contract.html`
  Retain dimension-by-dimension discretization, reward-scale arithmetic, recorded bin/action-mask bugs and their tests.
- **Training, curriculum and evaluation** (application, about 8 minutes) · `applications/tabular-learning/tabular-training.html`
  Explain curriculum switches, SARSA pre-commit mechanics, evaluation cadence and optimality gaps; map readiness to unchanged practice evidence.

## 4 · Neural value learning (project phase 5)

### 4.1 · Replace a table with a differentiable function (`p5-network`)

Prerequisite lessons: p4-td, p4-bins.

Practice: `p5-network` → `labs/phase-5/p5-network.html`; existing Python pack follows.

- **Tables versus functions** (core, about 6 minutes) · `readings/p5-network/tables-functions.html`
  Preserve dimensionality arithmetic and show one shared function predicting values for nearby observations.
- **Vectors and tensor shapes** (core, about 6 minutes) · `readings/p5-network/vectors-shapes.html`
  Explain scalar/vector/matrix and batch dimensions with a two-observation, three-action example before matrix multiplication.
- **Forward pass and loss** (core, about 6 minutes) · `readings/p5-network/forward-loss.html`
  Preserve the tiny-network forward pass, selected-action gather, squared loss and batch reduction with explicit shapes.
- **Derivatives and backpropagation** (core, about 6 minutes) · `readings/p5-network/gradients.html`
  Calculate a scalar derivative and apply the chain rule to the same tiny network; distinguish gradient direction from loss value.
- **One optimizer update** (core, about 6 minutes) · `readings/p5-network/optimizer-update.html`
  Trace zero_grad, backward and step; introduce SGD and Adam's role, finite checks and the delivered tensor exercise.
- **How Adam rescales a gradient** (further-depth, about 6 minutes) · `readings/p5-network/adam-moments.html`
  Calculate a first/second moment update and bias correction; explain that the core optimizer usage needs no hidden derivation.

### 4.2 · Stabilize neural temporal-difference learning (`p5-stability`)

Prerequisite lessons: p5-network, p4-explore.

Practice: `p5-stability` → `labs/phase-5/p5-stability.html`; existing Python pack follows.

- **Why neural TD targets move** (core, about 6 minutes) · `readings/p5-stability/moving-targets.html`
  Trace a bootstrap target changing as online weights change; explain correlated samples and feedback.
- **Target networks and detachment** (core, about 6 minutes) · `readings/p5-stability/target-detachment.html`
  Distinguish independent snapshot storage, no-grad target calculation and hard/soft updates with the existing update-rate arithmetic.
- **Replay decorrelation and reuse** (core, about 6 minutes) · `readings/p5-stability/replay.html`
  Build a minimal buffer; explain capacity, sampling, warm-up and reuse without implying samples become independent automatically.
- **A complete DQN update** (core, about 6 minutes) · `readings/p5-stability/complete-dqn-update.html`
  Trace gather, masks, ending flags, detached targets, loss and optimizer shapes; separate training steps from target-sync timing.

### 4.3 · Improve selection and value representation (`p5-double-dueling`)

Prerequisite lessons: p5-stability.

Practice: `p5-double-dueling` → `labs/phase-5/p5-double-dueling.html`; existing Python pack follows.

- **Maximization bias** (core, about 6 minutes) · `readings/p5-double-dueling/maximization-bias.html`
  Compare noisy action estimates and demonstrate why selecting their maximum can exaggerate value.
- **Double DQN selection and evaluation** (core, about 6 minutes) · `readings/p5-double-dueling/double-selection.html`
  Preserve online [5,4,100], target [1,7,99], legal mask and 1.5 versus 4.5 targets; avoid a universal performance claim.
- **Dueling value and advantage** (core, about 6 minutes) · `readings/p5-double-dueling/dueling-values.html`
  Build two heads on a shared trunk and compare their roles using a small action-value vector.
- **Identifiability and centering** (core, about 6 minutes) · `readings/p5-double-dueling/dueling-centering.html`
  Derive constant-offset ambiguity and mean centering; preserve the delivered centering convention and distinguish it from policy advantages.
- **Legal-action handling** (core, about 6 minutes) · `readings/p5-double-dueling/double-dueling-masks.html`
  Trace illegal actions, ties and terminal empty masks through selection and evaluation; state where dueling centering and legal selection differ.

### 4.4 · Prioritize replay samples correctly (`p5-per`)

Prerequisite lessons: p5-stability, p1-probability.

Practice: `p5-per` → `labs/phase-5/p5-per.html`; existing Python pack follows.

- **Why prioritize samples?** (core, about 6 minutes) · `readings/p5-per/prioritize-errors.html`
  Compare TD errors and explain stale priorities, epsilon and possible overuse of noisy transitions.
- **Raw priority versus probability** (core, about 6 minutes) · `readings/p5-per/priority-probability.html`
  Normalize powered raw priorities on a tiny buffer and verify the sum; distinguish priority from sampling probability.
- **Importance weights** (core, about 6 minutes) · `readings/p5-per/importance-weights.html`
  Calculate inverse-probability weights and beta/normalization, including the zero-priority safeguard.
- **Updating and checking priorities** (core, about 6 minutes) · `readings/p5-per/priority-updates.html`
  Trace sampling, weighted loss and detached error feedback; test empirical frequencies and preserve the pack's conventions.

### Module application and project preparation

- **Reward scale, loss and gradients** (application, about 8 minutes) · `applications/neural-value-learning/dqn-reward-scale.html`
  Preserve the numerical scale trap and centering assumptions; explain effects on targets, TD errors and priorities without promising invariance in neural optimization.
- **Integrating a DQN learner** (application, about 8 minutes) · `applications/neural-value-learning/dqn-integration.html`
  Map observation dimensions, architecture, replay, schedules and all extension flags to one complete update and unchanged packs.
- **Reading DQN checks and ablation evidence** (application, about 8 minutes) · `applications/neural-value-learning/dqn-evidence.html`
  Separate recorded PyTorch fixtures from live training; audit walkthrough and target/mask/shape checks before the project checkpoint.

## 5 · Multiple agents and rewards (project phase 6)

### 5.1 · Understand joint rewards and credit (`p6-credit`)

Prerequisite lessons: p1-state, p4-td.

Practice: `p6-credit` → `labs/phase-6/p6-credit.html`; existing Python pack follows.

- **Joint actions and rewards** (core, about 6 minutes) · `readings/p6-credit/joint-actions.html`
  Trace a two-agent transition and identify shared state, observations, actions and individual or team reward.
- **Team reward versus contribution** (core, about 6 minutes) · `readings/p6-credit/team-contribution.html`
  Compare equal team rewards with different individual actions; explain credit assignment without assuming causal attribution.
- **Credit assignment examples** (core, about 6 minutes) · `readings/p6-credit/credit-examples.html`
  Preserve lap-time, position and dense-proxy comparisons; show a proxy rewarding behavior that hurts the objective.
- **Limits and useful diagnostics** (core, about 6 minutes) · `readings/p6-credit/credit-diagnostics.html`
  Compare three reward designs with fixed scenarios and counterfactual diagnostics; distinguish attribution from correlation.

### 5.2 · Shape rewards without changing the objective (`p6-shaping`)

Prerequisite lessons: p1-return, p1-values, p6-credit.

Practice: `p6-shaping` → `labs/phase-6/p6-shaping.html`; existing Python pack follows.

- **Base objectives and reward bonuses** (core, about 6 minutes) · `readings/p6-shaping/base-bonuses.html`
  Work an ad-hoc position-bonus counterexample before introducing a principled alternative.
- **Potential differences** (core, about 6 minutes) · `readings/p6-shaping/potential-differences.html`
  Calculate gamma times next potential minus current potential and distinguish it from an arbitrary bonus.
- **Telescoping returns and terminal treatment** (core, about 6 minutes) · `readings/p6-shaping/telescoping.html`
  Expand a finite return term by term; account for terminal potential, gamma and variable horizons.
- **Conditions and counterexamples** (core, about 6 minutes) · `readings/p6-shaping/shaping-conditions.html`
  State policy-invariance assumptions; preserve a non-telescoping implementation failure and terminal-potential counterexample.

### 5.3 · Model interaction and changing opponents (`p6-opponent`)

Prerequisite lessons: p6-credit, p35-stochastic.

Practice: `p6-opponent` → `labs/phase-6/p6-opponent.html`; existing Python pack follows.

- **Interaction mechanics** (core, about 6 minutes) · `readings/p6-opponent/interaction-mechanics.html`
  Use a generic blocking/overtaking toy to show when relative position actually affects future actions.
- **Opponents as part of transitions** (core, about 6 minutes) · `readings/p6-opponent/opponent-transitions.html`
  Compare a fixed scripted rival with an adaptive rival; distinguish joint model from a single-agent effective model.
- **Missing state versus a changing policy** (core, about 6 minutes) · `readings/p6-opponent/missing-changing.html`
  Contrast aliasing with nonstationarity using two identical observations and changed opponent behavior.
- **Nonstationarity and evaluation design** (core, about 6 minutes) · `readings/p6-opponent/opponent-evaluation.html`
  Evaluate against fixed, named opponents; separate mechanical model defects from inadequate training.

### Module application and project preparation

- **Position, overtaking and dirty air** (application, about 8 minutes) · `applications/multiple-agents/multi-car-dynamics.html`
  Retain 19-dimensional observations, fixed rivals, undercut/blocking mechanism and probabilistic overtake ordering.
- **Tracing interaction defects** (application, about 8 minutes) · `applications/multiple-agents/multi-car-bugs.html`
  Trace E1 double-counting, E2 overwritten overtakes, E3 dynamics/reward inconsistency, E5 shaping and E6 smaller findings with their consequences.
- **Reward comparisons and reachable objectives** (application, about 8 minutes) · `applications/multiple-agents/multi-car-checks.html`
  Map the staged blocking toy, three reward configurations and tests to checkpoint checks; state what passing tests cannot establish.

## 6 · Self-play and evaluation (project phase 8)

### 6.1 · Choose strategies against opponents (`p8-game`)

Prerequisite lessons: p6-opponent, p4-explore, p1-probability.

Practice: `p8-game` → `labs/phase-8/p8-game.html`; existing Python pack follows.

- **Best response to whom?** (core, about 6 minutes) · `readings/p8-game/best-response.html`
  Compare policies against two fixed opponents and explain why a single optimal response can be fragile.
- **Payoff matrices** (core, about 6 minutes) · `readings/p8-game/payoff-matrices.html`
  Preserve the complete rock-paper-scissors witness and calculate payoffs against an opponent mixture.
- **Mixed strategies and equilibrium** (core, about 6 minutes) · `readings/p8-game/mixed-equilibrium.html`
  Calculate a best response to a mixture and illustrate equilibrium without promising convergence of independent neural learners.
- **Robustness beyond one opponent** (core, about 6 minutes) · `readings/p8-game/robustness.html`
  Compare independent learning, centralized training and empirical fictitious play; distinguish snapshot mixtures from exact strategy averages.

### 6.2 · Retain historical opponents (`p8-pool`)

Prerequisite lessons: p8-game, p5-stability.

Practice: `p8-pool` → `labs/phase-8/p8-pool.html`; existing Python pack follows.

- **Forgetting historical opponents** (core, about 6 minutes) · `readings/p8-pool/forgetting.html`
  Trace a cyclic best-response sequence and why newest-only evaluation misses forgetting.
- **Independent snapshots** (core, about 6 minutes) · `readings/p8-pool/independent-snapshots.html`
  Compare copying parameters with sharing mutable storage; define evaluation mode and fixed snapshots.
- **Sampling an opponent pool** (core, about 6 minutes) · `readings/p8-pool/pool-sampling.html`
  Calculate normalized uniform/recency-biased probabilities and preserve the first-opponent degenerate-seed failure.
- **Coverage and evaluation over time** (core, about 6 minutes) · `readings/p8-pool/pool-coverage.html`
  Evaluate historical opponents, pool size and replacement; separate coverage metrics from a convergence claim.

### 6.3 · Design a defensible comparison (`p8-audit`)

Prerequisite lessons: p8-pool, p35-markov.

Practice: `p8-audit` → `labs/phase-8/p8-audit.html`; existing Python pack follows.

- **Fair pairings and baselines** (core, about 6 minutes) · `readings/p8-audit/fair-pairings.html`
  Align starting conditions, roles and seeds; preserve the shuffled-pairing null baseline for apparent bimodality.
- **Stochasticity and uncertainty** (core, about 6 minutes) · `readings/p8-audit/uncertainty.html`
  Compare sample counts, variability and uncertainty; distinguish an observed two-peak histogram from evidence of specialization.
- **Multi-agent lifecycle** (core, about 6 minutes) · `readings/p8-audit/agent-lifecycle.html`
  Trace generic AEC and Parallel APIs, selected-agent cleanup, per-agent ending dictionaries and live/dead agent sets.
- **A defensible comparison** (core, about 6 minutes) · `readings/p8-audit/comparison-protocol.html`
  Specify opponents, transitions, pairings, held-out scenarios and recorded-versus-live evidence before interpreting results.

### Module application and project preparation

- **Blocking and opponent initialization** (application, about 8 minutes) · `applications/self-play/self-play-mechanics.html`
  Preserve the Phase 6 blocking dependency, first-opponent problem and the staged toy intervention demonstrating consequences.
- **The F1 multi-agent interface and pool** (application, about 8 minutes) · `applications/self-play/self-play-integration.html`
  Map Parallel environment, independent learner loop and pool parameters to validated lifecycle/snapshot contracts.
- **Historical evaluation and evidence** (application, about 8 minutes) · `applications/self-play/self-play-evidence.html`
  Map bimodality null tests and readiness items to the plan; explain which claims the listed tests do and do not support.

## 7 · Policy gradients and PPO (project phase 9)

### 7.1 · Prepare probability and gradient tools (`p9-probability`)

Prerequisite lessons: p1-probability, p5-network.

Practice: Theory only; continue to the next lesson without a browser/Python requirement.

- **Policy probabilities and logs** (core, about 6 minutes) · `readings/p9-probability/policy-probabilities.html`
  Normalize logits with softmax, explain logarithms using likelihood products and calculate log probability of a sampled action.
- **Gradients of log probabilities** (core, about 6 minutes) · `readings/p9-probability/score-gradient.html`
  Derive a small softmax score vector and show that probability-weighted scores sum to zero; introduce trajectory likelihood assumptions.

### 7.2 · Learn a policy from sampled returns (`p9-reinforce`)

Prerequisite lessons: p9-probability, p1-return.

Practice: `p9-reinforce` → `labs/phase-9/p9-reinforce.html`; existing Python pack follows.

- **Gradient intuition** (core, about 6 minutes) · `readings/p9-reinforce/gradient-intuition.html`
  Compare increasing a rewarded action's probability with directly differentiating the reward; explain ascent versus loss minimization.
- **The score-function derivation** (core, about 6 minutes) · `readings/p9-reinforce/score-function.html`
  Derive the likelihood-ratio identity and episodic return-to-go under stated differentiability/support assumptions.
- **REINFORCE by hand** (core, about 6 minutes) · `readings/p9-reinforce/reinforce-example.html`
  Preserve the worked softmax gradient and noisy-bandit update with probabilities, return and gradient signs.
- **Implement and diagnose a sampled update** (core, about 6 minutes) · `readings/p9-reinforce/sampled-update.html`
  Trace log_prob times detached return, batch reduction and optimizer; show variance and destructive steps in the delivered exercise.

### 7.3 · Reduce variance with a value baseline (`p9-advantage`)

Prerequisite lessons: p9-reinforce, p4-td.

Practice: `p9-advantage` → `labs/phase-9/p9-advantage.html`; existing Python pack follows.

- **Value baselines** (core, about 6 minutes) · `readings/p9-advantage/value-baselines.html`
  Compare raw returns with the worked value-baseline example and explain the baseline's prediction target.
- **Why action-independent baselines work** (core, about 6 minutes) · `readings/p9-advantage/baseline-proof.html`
  Sum baseline-weighted score gradients over actions and identify action independence and detached actor weights.
- **Advantages and actor–critic** (core, about 6 minutes) · `readings/p9-advantage/actor-critic.html`
  Calculate Q minus V and a one-step estimated advantage; distinguish exact advantages from sampled estimates.
- **Keeping actor and critic gradients separate** (core, about 6 minutes) · `readings/p9-advantage/separate-gradients.html`
  Trace actor loss and critic loss on one batch; detach advantage and explain shared-trunk versus accidental target gradients.

### 7.4 · Estimate advantages across a rollout (`p9-gae`)

Prerequisite lessons: p9-advantage, p1-loop.

Practice: `p9-gae` → `labs/phase-9/p9-gae.html`; existing Python pack follows.

- **TD residuals as advantage signals** (core, about 6 minutes) · `readings/p9-gae/td-residuals.html`
  Calculate two residuals using rewards, values and ending flags; distinguish critic error from an advantage estimator.
- **The lambda-weighted sum** (core, about 6 minutes) · `readings/p9-gae/lambda-sum.html`
  Preserve the hand-worked GAE example, lambda extremes and bias/variance assumptions.
- **Reverse recursion** (core, about 6 minutes) · `readings/p9-gae/reverse-recursion.html`
  Implement and manually verify the reverse recurrence on the same residuals and explicit batch/time shapes.
- **Terminals, time limits and rollout cutoffs** (core, about 6 minutes) · `readings/p9-gae/gae-boundaries.html`
  Separate bootstrap eligibility from recursion continuation; bootstrap the final observation at truncation without leaking into a reset episode.

### 7.5 · Limit incentives for policy changes (`p9-ppo`)

Prerequisite lessons: p9-gae.

Practice: `p9-ppo` → `labs/phase-9/p9-ppo.html`; existing Python pack follows.

- **Old versus current policy** (core, about 6 minutes) · `readings/p9-ppo/old-current.html`
  Freeze rollout log probabilities and distinguish current-policy updates from resampling old likelihoods.
- **Likelihood ratios** (core, about 6 minutes) · `readings/p9-ppo/likelihood-ratios.html`
  Calculate exp(new_log_prob minus old_log_prob), masked distributions and support requirements.
- **Both clipping branches** (core, about 6 minutes) · `readings/p9-ppo/clipping-branches.html`
  Work positive and negative advantages inside and outside the clipping interval; calculate min and gradient incentive.
- **What the surrogate limits** (core, about 6 minutes) · `readings/p9-ppo/surrogate-limits.html`
  Show an out-of-range ratio and explain why clipping is no hard trust-region or universal stability guarantee.
- **Minibatches and implementation checks** (core, about 6 minutes) · `readings/p9-ppo/ppo-minibatches.html`
  Trace frozen old data across epochs, detached advantages, critic updates and diagnostics; align with the delivered PPO exercise.

### Module application and project preparation

- **Building and using a PPO implementation** (application, about 8 minutes) · `applications/policy-gradients/library-choice.html`
  Preserve build-versus-buy reasoning and inventory library behavior that must be understood despite using a packaged learner.
- **Vector environments and masked PPO** (application, about 8 minutes) · `applications/policy-gradients/vector-library.html`
  Explain SB3/MaskablePPO learn/predict, rollout arithmetic, logging, evaluation masks and train/eval mode contracts; verify APIs during authoring.
- **Factories, serialization and worker contracts** (application, about 8 minutes) · `applications/policy-gradients/workers.html`
  Distinguish ordinary pickle from SB3 mechanisms; preserve the local spawn exercise, main guard, serializable factories and worker-local masks.
- **Fair algorithm comparison** (application, about 8 minutes) · `applications/policy-gradients/fair-budget.html`
  Preserve both fixes to the unequal-transition budget, worker-count arithmetic and curriculum compounding; align experience and evaluation protocols.
- **F1 PPO integration and verification** (application, about 8 minutes) · `applications/policy-gradients/ppo-integration.html`
  Map wrapper, agent, configuration, recorded integration evidence and test limitations to readiness without assuming self-play was studied.

## Coverage and identity baseline

Inventoried 108 legacy resource identities, 79 source pages including phase indexes, 398 sections and 140 HTML routes.

The outline has 27 teaching lessons, 134 planned pages and 25 uniquely mapped browser/Python practice anchors. The glossary is a separate consolidated reference; its final entry layout is deferred to authoring.

See `coverage-map.json` for complete section text/HTML, subheadings, glossary terms, code/table/list blocks and dispositions. See `legacy-v1-identities.json` and `legacy-routes.json` for pre-removal identity inputs. No reading completion equivalence is approved by this inventory.
