// Course manifest: the single source of truth for navigation. The value is pure JSON.
window.COURSE = {
  "phases": [
    {
      "id": "1",
      "slug": "phase-1-rl-prerequisites",
      "short": "RL fundamentals",
      "title": "RL Prerequisites",
      "desc": "Everything you need to read and build <code>phase-1-gym-environment.md</code> with no prior reinforcement-learning background: the agent/environment loop, MDPs, Bellman equations, and the Gymnasium API.",
      "assumes": [],
      "pages": [
        {
          "n": "00",
          "file": "00-overview.html",
          "title": "Overview",
          "group": "start"
        },
        {
          "n": "01",
          "file": "01-rl-fundamentals.html",
          "title": "RL fundamentals",
          "group": "concepts",
          "blurb": "Agent/environment loop, reward hypothesis, episodes",
          "why": "The vocabulary everything else is built from",
          "lab": {
            "id": "p1-01",
            "title": "Be the agent",
            "format": "notebook",
            "minutes": 15
          }
        },
        {
          "n": "02",
          "file": "02-markov-decision-processes.html",
          "title": "Markov decision processes",
          "group": "concepts",
          "blurb": "The MDP tuple (S, A, P, R, γ), the Markov property, policies, return — with a fully worked numeric race example",
          "why": "Phase 1 is the specification of an MDP — the formal language the plan is written in",
          "lab": {
            "id": "p1-02",
            "title": "Returns and one lap by hand",
            "format": "paper",
            "minutes": 15
          }
        },
        {
          "n": "03",
          "file": "03-value-functions-bellman.html",
          "title": "Value functions & Bellman",
          "group": "concepts",
          "blurb": "State/action-value functions, the Bellman equation derived step by step, and the reward-centring proof worked in full",
          "why": "Explains exactly why the reward design (γ=1, no zeroing on SC laps, the −5,000 problem) is written the way it is",
          "lab": {
            "id": "p1-03",
            "title": "Bellman backups",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "04",
          "file": "04-gymnasium-api.html",
          "title": "The Gymnasium API",
          "group": "concepts",
          "blurb": "The Env contract: spaces, reset(), step(), action masking, check_env — plus a complete, runnable toy environment",
          "why": "The literal API f1_strategy_env.py must implement",
          "lab": {
            "id": "p1-04",
            "title": "The Gymnasium contract",
            "format": "pytest",
            "minutes": 20
          }
        },
        {
          "n": "05",
          "file": "05-building-the-environment.html",
          "title": "Building the environment",
          "group": "capstone",
          "blurb": "A sequence of small, runnable toy Gymnasium environments, each adding one real-world complication, building up in your own code toward the shape of the real environment",
          "why": "Understanding by building, not by reading someone else's finished file",
          "lab": {
            "id": "p1-cap",
            "title": "Toy race environment",
            "format": "pytest",
            "minutes": 90
          }
        },
        {
          "n": "06",
          "file": "06-this-project-as-mdp.html",
          "title": "This project, formalized",
          "group": "project",
          "blurb": "State/action/reward/transition grounded in the actual plan, with a lap time computed by hand and a full step() trace",
          "why": "Bridges the general theory above to the specific file you are about to write",
          "lab": {
            "id": "p1-06",
            "title": "Trace a step yourself",
            "format": "quiz",
            "minutes": 10
          }
        },
        {
          "n": "07",
          "file": "07-code-walkthrough.html",
          "title": "Code walkthrough",
          "group": "project",
          "blurb": "A reading guide to dynamics.py and f1_strategy_env.py — what to look for and why, not a copy of the code itself",
          "why": "Line-level understanding before implementation",
          "lab": {
            "id": "p1-07",
            "title": "What each test defends",
            "format": "quiz",
            "minutes": 10
          }
        }
      ]
    },
    {
      "id": "3.5",
      "slug": "phase-3.5-dp-oracle-prerequisites",
      "short": "DP oracle",
      "title": "DP Oracle Prerequisites",
      "desc": "Everything you need to build the exact optimality oracle in <code>phase-3.5-dp-oracle.md</code>: planning vs. learning, backward induction, stochastic transitions, and Markov chains.",
      "assumes": [
        "1"
      ],
      "pages": [
        {
          "n": "00",
          "file": "00-overview.html",
          "title": "Overview",
          "group": "start"
        },
        {
          "n": "01",
          "file": "01-planning-vs-learning.html",
          "title": "Planning vs. learning",
          "group": "concepts",
          "blurb": "What makes an MDP exactly solvable, and why that's a size argument, not a magic trick",
          "why": "Frames why this phase looks nothing like Phases 4/5, and why that's the point",
          "lab": {
            "id": "p35-01",
            "title": "What makes exact solving possible",
            "format": "widget",
            "minutes": 10
          }
        },
        {
          "n": "02",
          "file": "02-backward-induction.html",
          "title": "Backward induction",
          "group": "concepts",
          "blurb": "The finite-horizon Bellman recursion, derived step by step, with a fully worked numeric race example",
          "why": "The exact algorithm dp_oracle.py implements",
          "lab": {
            "id": "p35-02",
            "title": "Backward induction, two ways",
            "format": "pytest",
            "minutes": 20
          }
        },
        {
          "n": "03",
          "file": "03-stochastic-transitions.html",
          "title": "Expectations over randomness",
          "group": "concepts",
          "blurb": "Computing E[V(s')] when the next state is random — the safety-car hazard term, and why compute_lap_time(noise=0) is the exact expectation, not an approximation",
          "why": "The one genuinely new piece of math the oracle needs beyond page 3's Bellman equation",
          "lab": {
            "id": "p35-03",
            "title": "Expectations over a risk",
            "format": "pytest",
            "minutes": 20
          }
        },
        {
          "n": "04",
          "file": "04-markov-chains.html",
          "title": "Markov chains",
          "group": "concepts",
          "blurb": "Transition matrices, fitting one from data by counting, sampling from a fitted chain — with a fully worked numeric weather example",
          "why": "What Oracle B's weather model is, precisely, and why it's \"exactly achievable\" while Oracle A is only a bound",
          "lab": {
            "id": "p35-04",
            "title": "Fit a chain, sample a chain",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "05",
          "file": "05-build-a-toy-solver.html",
          "title": "Build a toy DP solver",
          "group": "capstone",
          "blurb": "A sequence of small, runnable backward-induction solvers, each adding one complication a plain toy ignores",
          "why": "Understanding by building, not by reading someone else's finished solver",
          "lab": {
            "id": "p35-cap",
            "title": "Toy race solver",
            "format": "pytest",
            "minutes": 90
          }
        },
        {
          "n": "06",
          "file": "06-this-project-as-dp.html",
          "title": "This project, formalized",
          "group": "project",
          "blurb": "The real DPState, the state-space size arithmetic, and the Oracle A / Oracle B distinction grounded in this project's actual design",
          "why": "Bridges the general theory above to the specific files you are about to write",
          "lab": {
            "id": "p35-06",
            "title": "Size it, prune it, name the oracle",
            "format": "quiz",
            "minutes": 10
          }
        },
        {
          "n": "07",
          "file": "07-code-walkthrough.html",
          "title": "Code walkthrough",
          "group": "project",
          "blurb": "A reading guide to dp_oracle.py, weather_markov.py, and run_dp_oracle.py — what to look for and why",
          "why": "Line-level understanding before implementation",
          "lab": {
            "id": "p35-07",
            "title": "What each test defends",
            "format": "quiz",
            "minutes": 10
          }
        }
      ]
    },
    {
      "id": "4",
      "slug": "phase-4-q-learning-prerequisites",
      "short": "Q-learning",
      "title": "Q-Learning Prerequisites",
      "desc": "Everything you need to build tabular Q-learning and SARSA in <code>phase-4-q-learning-sarsa.md</code>: the update rule derived from the Bellman equation, epsilon-greedy exploration, and state discretization.",
      "assumes": [
        "1",
        "3.5"
      ],
      "pages": [
        {
          "n": "00",
          "file": "00-overview.html",
          "title": "Overview",
          "group": "start"
        },
        {
          "n": "01",
          "file": "01-from-equation-to-update-rule.html",
          "title": "From equation to update rule",
          "group": "concepts",
          "blurb": "Why Q-learning can't solve the Bellman equation the way DP did, and the TD-error idea that replaces solving with nudging",
          "why": "Frames every update rule in the rest of this set as one instance of the same idea",
          "lab": {
            "id": "p4-01",
            "title": "A little at a time",
            "format": "widget",
            "minutes": 10
          }
        },
        {
          "n": "02",
          "file": "02-q-learning-derived.html",
          "title": "Q-learning, derived & hand-run",
          "group": "concepts",
          "blurb": "The off-policy TD-control update, traced term by term, hand-run on a 3-state toy table",
          "why": "The exact update QLearningAgent.update() implements",
          "lab": {
            "id": "p4-02",
            "title": "The Q-learning update, two ways",
            "format": "pytest",
            "minutes": 15
          }
        },
        {
          "n": "03",
          "file": "03-epsilon-greedy-exploration.html",
          "title": "Exploration: ε-greedy",
          "group": "concepts",
          "blurb": "Why a purely greedy agent gets stuck, the ε-greedy rule, linear decay arithmetic, and why masking must apply inside exploration",
          "why": "What select_action() actually does before it ever looks exploitative",
          "lab": {
            "id": "p4-03",
            "title": "Decay and masking",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "04",
          "file": "04-sarsa-on-policy.html",
          "title": "On- vs. off-policy: SARSA",
          "group": "concepts",
          "blurb": "SARSA's update contrasted term-by-term with Q-learning's, and a worked \"risky shortcut vs. safe route\" example where the two converge to different policies",
          "why": "Why the plan trains and compares both agents rather than picking one",
          "lab": {
            "id": "p4-04",
            "title": "SARSA on the cliff",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "05",
          "file": "05-state-discretization-tradeoff.html",
          "title": "State discretization",
          "group": "concepts",
          "blurb": "Why a table needs a finite key space, and the too-few-bins/too-many-bins tension in general terms",
          "why": "Sets up why the real binning scheme is a real design decision, not a formality",
          "lab": {
            "id": "p4-05",
            "title": "How many bins?",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "06",
          "file": "06-the-binning-bug.html",
          "title": "The binning bug",
          "group": "concepts",
          "blurb": "The real plan's tire_age binning worked through against Phase 3.5's own validated pit-window numbers, showing exactly how coarseness erases a decision no amount of training can recover",
          "why": "An audit finding recorded against the real plan — read before writing discretize_obs, not after",
          "lab": {
            "id": "p4-06",
            "title": "Which laps share a cell?",
            "format": "widget",
            "minutes": 10
          }
        },
        {
          "n": "07",
          "file": "07-build-it-yourself.html",
          "title": "Build it yourself",
          "group": "capstone",
          "blurb": "A toy Q-learning agent and a toy SARSA agent, built side by side and run on identical seeds, plus a deliberately reproduced on-policy leak bug",
          "why": "Understanding by building, not by reading someone else's finished agent",
          "lab": {
            "id": "p4-cap",
            "title": "Toy race learners",
            "format": "pytest",
            "minutes": 90
          }
        },
        {
          "n": "08",
          "file": "08-this-project-formalized.html",
          "title": "This project, formalized",
          "group": "project",
          "blurb": "The real discretize_obs, the reward-scale problem worked out numerically, curriculum learning, and two bugs recorded against the real plan",
          "why": "Bridges the general theory above to the specific files you are about to write",
          "lab": {
            "id": "p4-08",
            "title": "Decode, count, and measure the gap",
            "format": "quiz",
            "minutes": 10
          }
        },
        {
          "n": "09",
          "file": "09-code-walkthrough.html",
          "title": "Code walkthrough",
          "group": "project",
          "blurb": "A reading guide to q_learning_agent.py, train_tabular.py, and q_learning.yaml — what to look for and why",
          "why": "Line-level understanding before implementation",
          "lab": {
            "id": "p4-09",
            "title": "What the tests catch and miss",
            "format": "quiz",
            "minutes": 10
          }
        }
      ]
    },
    {
      "id": "5",
      "slug": "phase-5-dqn-prerequisites",
      "short": "DQN",
      "title": "DQN Prerequisites",
      "desc": "Everything you need to build the Dueling Double DQN agent with prioritized experience replay in <code>phase-5-dueling-double-dqn.md</code>: going from a table to a function approximator, target networks, experience replay, the dueling architecture, Double DQN, prioritized replay, and the reward-scale trap.",
      "assumes": [
        "1",
        "3.5",
        "4"
      ],
      "pages": [
        {
          "n": "00",
          "file": "00-overview.html",
          "title": "Overview",
          "group": "start"
        },
        {
          "n": "01",
          "file": "01-table-to-function.html",
          "title": "Table to function",
          "group": "concepts",
          "blurb": "Why tabular breaks even with better binning, and function approximation defined generally",
          "why": "Frames every technique in the rest of this set as a way to make one update rule work on a function instead of a table",
          "lab": {
            "id": "p5-01",
            "title": "One update, many states",
            "format": "notebook",
            "minutes": 15
          }
        },
        {
          "n": "02",
          "file": "02-neural-networks-primer.html",
          "title": "Neural networks primer",
          "group": "concepts",
          "blurb": "Forward pass, loss, backpropagation, gradient descent, Adam — scoped tightly to what the real network's training step does",
          "why": "The reader has not needed a neural network until this phase",
          "lab": {
            "id": "p5-02",
            "title": "The four steps, written out",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "03",
          "file": "03-target-network.html",
          "title": "The target network",
          "group": "concepts",
          "blurb": "Why training a network on its own moving target is unstable, and the fix — a slowly-tracking second copy",
          "why": "The exact mechanism behind target_net and the Polyak update",
          "lab": {
            "id": "p5-03",
            "title": "Chasing your own target",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "04",
          "file": "04-experience-replay.html",
          "title": "Experience replay",
          "group": "concepts",
          "blurb": "Why correlated, in-order training data is a second, separate instability, and the replay-buffer fix",
          "why": "The exact mechanism behind PrioritizedReplayBuffer's uniform-sampling baseline",
          "lab": {
            "id": "p5-04",
            "title": "A ring buffer, and what it does to a batch",
            "format": "pytest",
            "minutes": 15
          }
        },
        {
          "n": "05",
          "file": "05-dueling-architecture.html",
          "title": "The dueling architecture",
          "group": "concepts",
          "blurb": "Separating V(s) from A(s,a), the identifiability problem, and the mean-subtraction fix, derived",
          "why": "The exact shape of DuelingDQN's two heads",
          "lab": {
            "id": "p5-05",
            "title": "Two heads, one answer",
            "format": "pytest",
            "minutes": 15
          }
        },
        {
          "n": "06",
          "file": "06-double-dqn.html",
          "title": "Double DQN",
          "group": "concepts",
          "blurb": "Why a max over noisy estimates runs high, the online-chooses / target-scores fix, masking inside the choice, the terminal cut-off, and a full batch of targets worked by hand",
          "why": "The exact target computed in update(), line by line",
          "lab": {
            "id": "p5-06",
            "title": "Who chooses, who scores",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "07",
          "file": "07-prioritized-replay.html",
          "title": "Prioritized replay",
          "group": "concepts",
          "blurb": "Sampling by TD error, the α exponent, importance-sampling weights and β, and the sum tree walked through by hand",
          "why": "The exact mechanism behind PrioritizedReplayBuffer, and the bug recorded against it",
          "lab": {
            "id": "p5-07",
            "title": "A memory that ranks",
            "format": "pytest",
            "minutes": 25
          }
        },
        {
          "n": "08",
          "file": "08-reward-scale-trap.html",
          "title": "The reward-scale trap",
          "group": "concepts",
          "blurb": "Why outputs near −5,000 are reached slowly and silently: Huber loss, gradient clipping, Adam's step size and a target that starts at zero — and the reward-centring fix",
          "why": "The plan's own most likely reason this phase looks broken when it isn't",
          "lab": {
            "id": "p5-08",
            "title": "Speed limits",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "09",
          "file": "09-build-it-yourself.html",
          "title": "Build it yourself",
          "group": "capstone",
          "blurb": "A staged toy DQN in your own code: a bare network learner, then a target network and replay, a dueling head and Double DQN target, prioritized replay, and a planted bug",
          "why": "Understanding by building, not by reading someone else's finished file",
          "lab": {
            "id": "p5-cap",
            "title": "Toy race network learner",
            "format": "pytest",
            "minutes": 90
          }
        },
        {
          "n": "10",
          "file": "10-this-project-formalized.html",
          "title": "This project, formalized",
          "group": "project",
          "blurb": "The real network counted layer by layer, every hyperparameter turned into what it means over a 260,000-step run, and the issues recorded against the real plan",
          "why": "Bridges the general theory above to the specific files you are about to write",
          "lab": {
            "id": "p5-10",
            "title": "Redo the arithmetic",
            "format": "quiz",
            "minutes": 12
          }
        },
        {
          "n": "11",
          "file": "11-code-walkthrough.html",
          "title": "Code walkthrough",
          "group": "project",
          "blurb": "A reading guide to dqn_agent.py, train_dqn.py, and dqn.yaml — what to look for and why",
          "why": "Line-level understanding before implementation",
          "lab": {
            "id": "p5-11",
            "title": "What each test defends",
            "format": "quiz",
            "minutes": 10
          }
        }
      ]
    },
    {
      "id": "6",
      "slug": "phase-6-multi-car-prerequisites",
      "short": "Multi-car",
      "title": "Multi-Car Prerequisites",
      "desc": "Everything you need to build the multi-car environment and rule-based rivals in <code>phase-6-multi-car-rivals.md</code>: multi-agent MDPs, credit assignment, potential-based shaping, and overtaking/dirty-air modelling.",
      "assumes": [
        "1",
        "3.5",
        "4",
        "5"
      ],
      "pages": [
        {
          "n": "00",
          "file": "00-overview.html",
          "title": "Overview",
          "group": "start"
        },
        {
          "n": "01",
          "file": "01-multi-car-mdp.html",
          "title": "One car to N",
          "group": "concepts",
          "blurb": "What actually changes in the MDP when rivals are added — three new state features, rivals as fixed scripts",
          "why": "Frames every other page as a consequence of this one change",
          "lab": {
            "id": "p6-01",
            "title": "Three new numbers",
            "format": "paper",
            "minutes": 10
          }
        },
        {
          "n": "02",
          "file": "02-credit-assignment.html",
          "title": "Credit assignment",
          "group": "concepts",
          "blurb": "The credit-assignment problem, sparse vs. dense reward, the real plan's two proxy reward designs and their risks",
          "why": "Motivates why the real plan trains and compares three separate reward designs instead of picking one",
          "lab": {
            "id": "p6-02",
            "title": "Sparse, dense, and farmed",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "03",
          "file": "03-potential-based-shaping.html",
          "title": "Potential-based shaping",
          "group": "concepts",
          "blurb": "Ng, Harada & Russell (1999) — why F = γΦ(s′) − Φ(s) provably can't change the optimal policy, via return decomposition plus a worked example",
          "why": "The principled reward-shaping design the real plan claims to use for its third variant",
          "lab": {
            "id": "p6-03",
            "title": "A potential that cannot change the answer",
            "format": "pytest",
            "minutes": 20
          }
        },
        {
          "n": "04",
          "file": "04-overtaking-dirty-air.html",
          "title": "Overtaking & dirty air",
          "group": "concepts",
          "blurb": "The real linear dirty-air penalty and sigmoid overtake-probability formulas, worked against the plan's own calibration numbers",
          "why": "The exact math behind overtaking.py",
          "lab": {
            "id": "p6-04",
            "title": "How likely is the pass?",
            "format": "widget",
            "minutes": 15
          }
        },
        {
          "n": "05",
          "file": "05-position-and-blocking.html",
          "title": "Position vs. the undercut",
          "group": "concepts",
          "blurb": "The audit's central design-gap finding, and the one-line blocking fix that makes track position a real resource",
          "why": "Without this, Phase 6's most interesting goal — and all of Phase 8 — is unreachable, no matter how long training runs",
          "lab": {
            "id": "p6-05",
            "title": "Stuck behind",
            "format": "widget",
            "minutes": 15
          }
        },
        {
          "n": "06",
          "file": "06-bug-ledger.html",
          "title": "The bug ledger",
          "group": "concepts",
          "blurb": "The double-counted rival time, the dead overtake code, the reward that disagrees with the dynamics, the mislabeled shaping, and four smaller items — each taught as a reusable lesson",
          "why": "These bugs would each individually make a training run look like it worked when it didn't",
          "lab": {
            "id": "p6-06",
            "title": "The bug ledger",
            "format": "pytest",
            "minutes": 20
          }
        },
        {
          "n": "07",
          "file": "07-non-stationarity.html",
          "title": "Non-stationarity preview",
          "group": "concepts",
          "blurb": "Why a learning opponent breaks the fixed-environment assumption Phase 4/5's theory relies on, and why scripted rivals sidestep it entirely",
          "why": "Explains why this phase's rivals are deliberately not learning agents, and previews why Phase 8 is harder",
          "lab": {
            "id": "p6-07",
            "title": "A target that moves",
            "format": "notebook",
            "minutes": 15
          }
        },
        {
          "n": "08",
          "file": "08-build-it-yourself.html",
          "title": "Build it yourself",
          "group": "capstone",
          "blurb": "A staged toy multi-car race — reproduce the no-blocking failure, fix it, add overtaking, then compare reward designs on a scenario built to make ad-hoc shaping fail",
          "why": "Understanding by building the exact failure and fix yourself, not just reading about them",
          "lab": {
            "id": "p6-cap",
            "title": "Two-car duel race",
            "format": "pytest",
            "minutes": 90
          }
        },
        {
          "n": "09",
          "file": "09-this-project-formalized.html",
          "title": "This project, formalized",
          "group": "project",
          "blurb": "The real 19-dimensional observation, the three reward_type configs, the five fixed rival strategies, and the Definition-of-Done items that exist specifically because of pages 5–6",
          "why": "Bridges the general theory above to the specific files about to be written",
          "lab": {
            "id": "p6-09",
            "title": "Tag, compute, match",
            "format": "quiz",
            "minutes": 10
          }
        },
        {
          "n": "10",
          "file": "10-reading-the-plan.html",
          "title": "Reading the plan's code",
          "group": "project",
          "blurb": "A critical reading guide to the plan's pseudocode, including exactly where each audit finding lives and what its existing tests do and don't catch",
          "why": "Line-level understanding before a single line of src/env/f1_multi_env.py gets written",
          "lab": {
            "id": "p6-10",
            "title": "What the plan's tests can see",
            "format": "quiz",
            "minutes": 10
          }
        }
      ]
    },
    {
      "id": "8",
      "slug": "phase-8-self-play-prerequisites",
      "short": "Self-play",
      "title": "Self-Play Prerequisites",
      "desc": "Everything you need to build the multi-agent self-play training loop in <code>phase-8-self-play.md</code>: non-stationarity revisited, Nash equilibria and fictitious play, checkpoint pools, and the PettingZoo API.",
      "assumes": [
        "1",
        "3.5",
        "4",
        "5",
        "6"
      ],
      "pages": [
        {
          "n": "00",
          "file": "00-overview.html",
          "title": "Overview",
          "group": "start"
        },
        {
          "n": "01",
          "file": "01-non-stationarity-revisited.html",
          "title": "Non-stationarity, revisited",
          "group": "concepts",
          "blurb": "What breaks when the opponent learns too, and the three MARL training paradigms (independent learners, parameter sharing, CTDE)",
          "why": "Frames why self-play is a genuinely harder problem than Phase 6, not just \"Phase 6 with a smarter rival\"",
          "lab": {
            "id": "p8-01",
            "title": "When the opponent learns too",
            "format": "notebook",
            "minutes": 15
          }
        },
        {
          "n": "02",
          "file": "02-nash-and-fictitious-play.html",
          "title": "Nash & fictitious play",
          "group": "concepts",
          "blurb": "Nash equilibria, fictitious self-play, and matching pennies worked by hand: latest-only cycles, the running average converges",
          "why": "The theoretical target the checkpoint pool is a practical approximation of",
          "lab": {
            "id": "p8-02",
            "title": "Best responses, cycles, and fictitious play",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "03",
          "file": "03-checkpoint-pool.html",
          "title": "Checkpoint pool",
          "group": "concepts",
          "blurb": "Recency-biased opponent sampling, worked as a probability calculation, and the self-play evaluation trap",
          "why": "The exact mechanism behind CheckpointPool",
          "lab": {
            "id": "p8-03",
            "title": "The checkpoint pool",
            "format": "pytest",
            "minutes": 20
          }
        },
        {
          "n": "04",
          "file": "04-pettingzoo-apis.html",
          "title": "PettingZoo APIs",
          "group": "concepts",
          "blurb": "PettingZoo's AEC and Parallel APIs, both taught with a worked micro-example, and why F1 needs Parallel",
          "why": "The API F1PettingZooEnv is built on",
          "lab": {
            "id": "p8-04",
            "title": "AEC and Parallel",
            "format": "pytest",
            "minutes": 20
          }
        },
        {
          "n": "05",
          "file": "05-first-opponent-problem.html",
          "title": "The first opponent",
          "group": "concepts",
          "blurb": "The degenerate deterministic first-opponent bug, taught as a general lesson about disguised determinism",
          "why": "Early self-play trains against a broken opponent if this isn't fixed",
          "lab": {
            "id": "p8-05",
            "title": "The first opponent",
            "format": "notebook",
            "minutes": 15
          }
        },
        {
          "n": "06",
          "file": "06-blocking-model-dependency.html",
          "title": "The blocking dependency",
          "group": "concepts",
          "blurb": "The Phase 6 E4 dependency, restated where it becomes load-bearing, and why the fix must reach F1PettingZooEnv too",
          "why": "Without it, this phase's headline result is unreachable no matter how training goes",
          "lab": {
            "id": "p8-06",
            "title": "Where the undercut comes from",
            "format": "quiz",
            "minutes": 10
          }
        },
        {
          "n": "07",
          "file": "07-is-it-bimodal.html",
          "title": "Is it bimodal?",
          "group": "concepts",
          "blurb": "A permutation-test null baseline for the pit-timing histogram, stratified for causes both cars share, and what it cannot show",
          "why": "Makes \"emergent undercut\" a defensible claim, not an eyeballed one",
          "lab": {
            "id": "p8-07",
            "title": "Is it really a reaction?",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "08",
          "file": "08-build-it-yourself.html",
          "title": "Build it yourself",
          "group": "capstone",
          "blurb": "The pit-timing duel, solved exactly in seven stages: the payoff, best responses and the latest-only cycle, fictitious play, a pool of best responses, the plan's own pool rule, the pit-delta histogram, and the null test on it",
          "why": "Understanding by building the exact failure and fix yourself",
          "lab": {
            "id": "p8-cap",
            "title": "The pit-timing duel",
            "format": "pytest",
            "minutes": 90
          }
        },
        {
          "n": "09",
          "file": "09-this-project-formalized.html",
          "title": "This project, formalized",
          "group": "project",
          "blurb": "F1PettingZooEnv, CheckpointPool, and the independent-learner training loop's real parameters",
          "why": "Bridges the general theory above to the specific files about to be written",
          "lab": {
            "id": "p8-09",
            "title": "Parameters, pages, lines",
            "format": "quiz",
            "minutes": 10
          }
        },
        {
          "n": "10",
          "file": "10-reading-the-plan.html",
          "title": "Reading the plan's code",
          "group": "project",
          "blurb": "A critical reading guide to the plan's pseudocode, including exactly where each finding lives and what its tests do and don't catch",
          "why": "Line-level understanding before a single line of src/agents/self_play_trainer.py gets written",
          "lab": {
            "id": "p8-10",
            "title": "What catches what",
            "format": "quiz",
            "minutes": 10
          }
        }
      ]
    },
    {
      "id": "9",
      "slug": "phase-9-ppo-prerequisites",
      "short": "PPO",
      "title": "PPO Prerequisites",
      "desc": "Everything you need to build the MaskablePPO training and DQN-comparison work in <code>phase-9-ppo-sb3.md</code>: policy gradients, actor-critic and advantage, generalized advantage estimation, and PPO's clipped objective.",
      "assumes": [
        "1",
        "3.5",
        "4",
        "5",
        "6",
        "8"
      ],
      "pages": [
        {
          "n": "00",
          "file": "00-overview.html",
          "title": "Overview",
          "group": "start"
        },
        {
          "n": "01",
          "file": "01-policy-gradients-reinforce.html",
          "title": "Policy gradients: REINFORCE",
          "group": "concepts",
          "blurb": "The policy-gradient theorem, derived, and REINFORCE built on it, with a hand-worked softmax-gradient example",
          "why": "The foundation everything else in this phase sits on top of",
          "lab": {
            "id": "p9-01",
            "title": "The log-gradient trick",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "02",
          "file": "02-actor-critic-advantage.html",
          "title": "Actor-critic & advantage",
          "group": "concepts",
          "blurb": "Baselines, the critic, and A(s,a) = Q(s,a) − V(s), with a hand-worked variance comparison",
          "why": "Why raw REINFORCE is too noisy in practice, and what fixes it",
          "lab": {
            "id": "p9-02",
            "title": "What a baseline buys",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "03",
          "file": "03-generalized-advantage-estimation.html",
          "title": "Generalized advantage estimation",
          "group": "concepts",
          "blurb": "The bias-variance dial between 1-step and Monte Carlo advantage estimates, worked numerically at three λ values",
          "why": "What SB3's MaskablePPO actually computes, silently, via a config key the real plan never sets",
          "lab": {
            "id": "p9-03",
            "title": "GAE, backwards",
            "format": "pytest",
            "minutes": 20
          }
        },
        {
          "n": "04",
          "file": "04-ppo-clipped-objective.html",
          "title": "PPO's clipped objective",
          "group": "concepts",
          "blurb": "The probability ratio, the surrogate objective, and the clip, worked through both signs of advantage",
          "why": "The exact mechanism clip_range: 0.2 and n_epochs: 10 in the real config rely on",
          "lab": {
            "id": "p9-04",
            "title": "Where the clip binds",
            "format": "widget",
            "minutes": 15
          }
        },
        {
          "n": "05",
          "file": "05-build-vs-buy.html",
          "title": "Why build vs. buy",
          "group": "concepts",
          "blurb": "Which pieces of PPO fail loudly vs. quietly when implemented slightly wrong, and the general engineering heuristic this illustrates",
          "why": "The README's \"PPO vs DQN: Build vs Library\" section, and the project's portfolio-framing point",
          "lab": {
            "id": "p9-05",
            "title": "Loud and quiet",
            "format": "pytest",
            "minutes": 20
          }
        },
        {
          "n": "06",
          "file": "06-stable-baselines3-api.html",
          "title": "Stable-Baselines3's API",
          "group": "concepts",
          "blurb": "VecEnv, the rollout/update loop behind .learn(), and MaskablePPO's masked action distribution, taught generically",
          "why": "The API sb3_wrapper.py and ppo_agent.py are direct instantiations of",
          "lab": {
            "id": "p9-06",
            "title": "The library, from the outside",
            "format": "notebook",
            "minutes": 20
          }
        },
        {
          "n": "07",
          "file": "07-pickling-and-subprocvecenv.html",
          "title": "Lambdas, processes & the guard",
          "group": "concepts",
          "blurb": "Pickling and process-start methods, then what the audit's lambda claim gets wrong: SB3 uses cloudpickle, and the real Windows trap is a missing __main__ guard",
          "why": "Where J1's fix really belongs, and why DummyVecEnv is the better choice here",
          "lab": {
            "id": "p9-07",
            "title": "Test the claim",
            "format": "pytest",
            "minutes": 20
          }
        },
        {
          "n": "08",
          "file": "08-unfair-comparison.html",
          "title": "The unfair comparison",
          "group": "concepts",
          "blurb": "The ~7.7× training-budget mismatch between the real plan's DQN and PPO configs, and two genuine fixes",
          "why": "Without this fix, any DQN-vs-PPO result the phase produces is uninterpretable",
          "lab": {
            "id": "p9-08",
            "title": "Matched budgets",
            "format": "notebook",
            "minutes": 15
          }
        },
        {
          "n": "09",
          "file": "09-build-it-yourself.html",
          "title": "Build it yourself",
          "group": "capstone",
          "blurb": "Seven stages on the toy race: a masked table policy, REINFORCE, GAE and a critic, a destructive update, the clip, a small PPO, and ten epochs per batch",
          "why": "Understanding by building the exact mechanism and the exact failure yourself",
          "lab": {
            "id": "p9-cap",
            "title": "Policy gradient on the toy race",
            "format": "pytest",
            "minutes": 90
          }
        },
        {
          "n": "10",
          "file": "10-this-project-formalized.html",
          "title": "This project, formalized",
          "group": "project",
          "blurb": "sb3_wrapper.py, ppo_agent.py, and configs/ppo.yaml's real parameters mapped onto pages 01–08",
          "why": "Bridges the general theory above to the specific files about to be written",
          "lab": {
            "id": "p9-10",
            "title": "Keys, pages, numbers",
            "format": "quiz",
            "minutes": 10
          }
        },
        {
          "n": "11",
          "file": "11-reading-the-plan.html",
          "title": "Reading the plan's code",
          "group": "project",
          "blurb": "A critical reading guide to the plan's pseudocode, including exactly where each fix belongs and what the Definition of Done does and doesn't catch",
          "why": "Line-level understanding before a single line of src/agents/ppo_agent.py gets written",
          "lab": {
            "id": "p9-11",
            "title": "What catches what",
            "format": "quiz",
            "minutes": 10
          }
        }
      ]
    }
  ]
};
