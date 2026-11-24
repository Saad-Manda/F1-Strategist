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
          "title": "Case brief",
          "group": "start",
          "blurb": "Call one race on the Pit Wall, then open Case 1: the 5,000-second head start",
          "why": "Phase 1 builds the race every later agent learns in"
        },
        {
          "n": "01",
          "file": "01-rl-fundamentals.html",
          "title": "RL fundamentals",
          "group": "concepts",
          "blurb": "The agent–environment loop, the reward hypothesis, episodes, and why the safety car is drawn fresh",
          "why": "One lap's reward can point the wrong way: the vocabulary for why",
          "lab": {
            "id": "p1-01",
            "title": "Be the agent",
            "format": "notebook",
            "minutes": 15
          },
          "call": "p1-01"
        },
        {
          "n": "02",
          "file": "02-markov-decision-processes.html",
          "title": "Markov decision processes",
          "group": "concepts",
          "blurb": "The MDP tuple read off the Pit Wall, the Markov property, return and γ = 1, masking, one real lap priced by hand",
          "why": "Phase 1 is the specification of an MDP, the language the plan is written in",
          "lab": {
            "id": "p1-02",
            "title": "Returns and one lap by hand",
            "format": "paper",
            "minutes": 15
          },
          "call": "p1-02"
        },
        {
          "n": "03",
          "file": "03-value-functions-bellman.html",
          "title": "Value functions & Bellman",
          "group": "concepts",
          "blurb": "Value as the reward still to come, the Bellman equation with real numbers, and reward centring proved",
          "why": "The −5,000 head start, and the one-constant fix that changes no call",
          "lab": {
            "id": "p1-03",
            "title": "Bellman backups",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p1-03"
        },
        {
          "n": "04",
          "file": "04-gymnasium-api.html",
          "title": "The Gymnasium API",
          "group": "concepts",
          "blurb": "reset(), step(), spaces, check_env, and three ways to handle an illegal call",
          "why": "The API f1_strategy_env.py must implement",
          "lab": {
            "id": "p1-04",
            "title": "The Gymnasium contract",
            "format": "pytest",
            "minutes": 20
          },
          "call": "p1-04"
        },
        {
          "n": "05",
          "file": "05-building-the-environment.html",
          "title": "Building the environment",
          "group": "capstone",
          "blurb": "Build the Pit Wall's race in ten stages, one complication at a time, under names of your own",
          "why": "Understanding by building, not by reading someone else's finished file",
          "lab": {
            "id": "p1-cap",
            "title": "Toy race environment",
            "format": "pytest",
            "minutes": 90
          },
          "call": "p1-05"
        },
        {
          "n": "06",
          "file": "06-back-to-the-plan.html",
          "title": "Back to the plan",
          "group": "project",
          "blurb": "The real state, mask, dynamics.py and tests against what you built, and the verdict on Case 1",
          "why": "Bridges the theory to the files you are about to write, and closes the case",
          "lab": {
            "id": "p1-06",
            "title": "Trace a step, and what each test defends",
            "format": "quiz",
            "minutes": 20
          },
          "call": "p1-06"
        }
      ],
      "case": {
        "title": "The 5,000-second head start",
        "question": "Why does the learner start out 5,000 seconds wrong, and can you fix it without changing a pit stop?"
      }
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
          "title": "Case brief",
          "group": "start",
          "blurb": "Beat the oracle on race #257, then open Case 2: how did you beat the optimal strategy?",
          "why": "Phase 3.5 builds the ruler every later agent is measured against"
        },
        {
          "n": "01",
          "file": "01-planning-vs-learning.html",
          "title": "Planning vs. learning",
          "group": "concepts",
          "blurb": "Where the oracle's calls come from without a race played, and why exact solving is a size argument",
          "why": "Frames why this phase looks nothing like Phases 4 and 5",
          "lab": {
            "id": "p35-01",
            "title": "What makes exact solving possible",
            "format": "widget",
            "minutes": 10
          },
          "call": "p35-01"
        },
        {
          "n": "02",
          "file": "02-backward-induction.html",
          "title": "Backward induction",
          "group": "concepts",
          "blurb": "Why the oracle starts at the flag: the finite-horizon recursion, worked by hand on a 4-lap race",
          "why": "The algorithm dp_oracle.py implements",
          "lab": {
            "id": "p35-02",
            "title": "Backward induction, two ways",
            "format": "pytest",
            "minutes": 20
          },
          "call": "p35-02"
        },
        {
          "n": "03",
          "file": "03-stochastic-transitions.html",
          "title": "Expectations over randomness",
          "group": "concepts",
          "blurb": "What 'best on average' means with a safety car in the race, and how your time splits into expectation, calls and luck",
          "why": "The one new piece of maths the oracle needs; the case's maths closes here",
          "lab": {
            "id": "p35-03",
            "title": "Expectations over a risk",
            "format": "pytest",
            "minutes": 20
          },
          "call": "p35-03"
        },
        {
          "n": "04",
          "file": "04-markov-chains.html",
          "title": "Markov chains",
          "group": "concepts",
          "blurb": "Weather as a Markov chain, fitted by counting, and the oracle that knows the weather in advance",
          "why": "What Oracle B's weather model is, and why Oracle A is a bound no agent can reach",
          "lab": {
            "id": "p35-04",
            "title": "Fit a chain, sample a chain",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p35-04"
        },
        {
          "n": "05",
          "file": "05-build-a-toy-solver.html",
          "title": "Build a toy DP solver",
          "group": "capstone",
          "blurb": "You build the solver the Pit Wall runs, in five checked stages",
          "why": "Understanding by building, not by reading someone else's finished solver",
          "lab": {
            "id": "p35-cap",
            "title": "Toy race solver",
            "format": "pytest",
            "minutes": 90
          },
          "call": "p35-05"
        },
        {
          "n": "06",
          "file": "06-back-to-the-plan.html",
          "title": "Back to the plan",
          "group": "project",
          "blurb": "The real DPState, the two oracles, how agents are scored against them, the tests, and the verdict on Case 2",
          "why": "Bridges the theory to the files you are about to write, and closes the case",
          "lab": {
            "id": "p35-06",
            "title": "Size it, name the oracle, and what each test defends",
            "format": "quiz",
            "minutes": 25
          },
          "call": "p35-06"
        }
      ],
      "case": {
        "title": "Beating the oracle",
        "question": "You just beat the optimal strategy. How, and what should you conclude when an agent does?"
      }
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
      "case": {
        "title": "The learner that can't see the window",
        "question": "Trained for 20,000 races, the coarse learner still stops on lap 1. Why can't more training fix it, and what should the plan change?"
      },
      "pages": [
        {
          "n": "00",
          "file": "00-overview.html",
          "title": "Case brief",
          "group": "start",
          "blurb": "Train two learners side by side on the Pit Wall, then open Case 3: why does the coarse one still stop on lap 1?",
          "why": "Phase 4 builds the first agents that learn the race from experience"
        },
        {
          "n": "01",
          "file": "01-from-equation-to-update-rule.html",
          "title": "From equation to update rule",
          "group": "concepts",
          "blurb": "Why a learner can't sum over next states as the oracle did, and the TD idea: nudge each estimate toward one lap's sample",
          "why": "Frames every update rule in the rest of this set as one instance of the same idea",
          "lab": {
            "id": "p4-01",
            "title": "A little at a time",
            "format": "widget",
            "minutes": 10
          },
          "call": "p4-01"
        },
        {
          "n": "02",
          "file": "02-q-learning-derived.html",
          "title": "Q-learning, derived & hand-run",
          "group": "concepts",
          "blurb": "The off-policy target, a 3-state toy hand-run, and the update filling in a policy on the toy race",
          "why": "The exact update QLearningAgent.update() implements",
          "lab": {
            "id": "p4-02",
            "title": "The Q-learning update, two ways",
            "format": "pytest",
            "minutes": 15
          },
          "call": "p4-02"
        },
        {
          "n": "03",
          "file": "03-epsilon-greedy-exploration.html",
          "title": "Exploration: ε-greedy",
          "group": "concepts",
          "blurb": "Why greedy alone gets stuck, ε-greedy with masking, the plan's decay arithmetic, and what exploring does for each learner",
          "why": "What select_action() actually does before it ever looks exploitative",
          "lab": {
            "id": "p4-03",
            "title": "Decay and masking",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p4-03"
        },
        {
          "n": "04",
          "file": "04-sarsa-on-policy.html",
          "title": "On- vs. off-policy: SARSA",
          "group": "concepts",
          "blurb": "SARSA's one-term change, a push-or-pit toy where the two learners part ways, and why the plan trains both",
          "why": "Why the plan trains and compares both agents rather than picking one",
          "lab": {
            "id": "p4-04",
            "title": "SARSA on the cliff",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p4-04"
        },
        {
          "n": "05",
          "file": "05-state-discretization-tradeoff.html",
          "title": "State discretization",
          "group": "concepts",
          "blurb": "Why a table needs bins, too few against too many, and the plan's 172,800-cell budget",
          "why": "Sets up why the real binning scheme is a real design decision, not a formality",
          "lab": {
            "id": "p4-05",
            "title": "How many bins?",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p4-05"
        },
        {
          "n": "06",
          "file": "06-the-binning-bug.html",
          "title": "The binning bug",
          "group": "concepts",
          "blurb": "What the coarse table can't tell apart, why it learns worse than its own ceiling, and which bins do the damage. The case's maths closes here",
          "why": "An audit finding recorded against the real plan — read before writing discretize_obs, not after",
          "lab": {
            "id": "p4-06",
            "title": "Which laps share a cell?",
            "format": "widget",
            "minutes": 10
          },
          "call": "p4-06"
        },
        {
          "n": "07",
          "file": "07-build-it-yourself.html",
          "title": "Build it yourself",
          "group": "capstone",
          "blurb": "You build an off-policy and an on-policy learner in six checked stages and score them against the exact optimum",
          "why": "Understanding by building, not by reading someone else's finished agent",
          "lab": {
            "id": "p4-cap",
            "title": "Toy race learners",
            "format": "pytest",
            "minutes": 90
          },
          "call": "p4-07"
        },
        {
          "n": "08",
          "file": "08-back-to-the-plan.html",
          "title": "Back to the plan",
          "group": "project",
          "blurb": "The real key, the reward scale, the training loop, the tests, and the verdict on Case 3",
          "why": "Bridges the theory to the files you are about to write, and closes the case",
          "lab": {
            "id": "p4-08",
            "title": "Decode, count, and what the tests catch",
            "format": "quiz",
            "minutes": 25
          },
          "call": "p4-08"
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
          "title": "Case brief",
          "group": "start",
          "blurb": "Watch a trained DQN's evaluation on the Pit Wall, then open Case 4: why does a champion make stops its own network rates worse?",
          "why": "Phase 5 replaces the table with a neural network"
        },
        {
          "n": "01",
          "file": "01-table-to-function.html",
          "title": "Table to function",
          "group": "concepts",
          "blurb": "Why a table can't keep up as dimensions are added, function approximation, and what carries over from Phase 4",
          "why": "Frames every technique in this set as a way to make one update rule work on a function instead of a table",
          "lab": {
            "id": "p5-01",
            "title": "One update, many states",
            "format": "notebook",
            "minutes": 15
          },
          "call": "p5-01"
        },
        {
          "n": "02",
          "file": "02-neural-networks-primer.html",
          "title": "Neural networks primer",
          "group": "concepts",
          "blurb": "A layer, a forward pass by hand, loss, one gradient by the chain rule, and the update beside Phase 4's",
          "why": "The reader has not needed a neural network until this phase",
          "lab": {
            "id": "p5-02",
            "title": "The four steps, written out",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p5-02"
        },
        {
          "n": "03",
          "file": "03-target-network.html",
          "title": "The target network",
          "group": "concepts",
          "blurb": "Why a network chasing its own target is unstable, the slow second copy, and how slow τ = 0.005 is",
          "why": "The mechanism behind target_net and the Polyak update",
          "lab": {
            "id": "p5-03",
            "title": "Chasing your own target",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p5-03"
        },
        {
          "n": "04",
          "file": "04-experience-replay.html",
          "title": "Experience replay",
          "group": "concepts",
          "blurb": "Why in-order laps destabilize training, the ring-buffer fix, and what the champion's memory was fed",
          "why": "The uniform-sampling baseline PrioritizedReplayBuffer builds on",
          "lab": {
            "id": "p5-04",
            "title": "A ring buffer, and what it does to a batch",
            "format": "pytest",
            "minutes": 15
          },
          "call": "p5-04"
        },
        {
          "n": "05",
          "file": "05-dueling-architecture.html",
          "title": "The dueling architecture",
          "group": "concepts",
          "blurb": "V and A, the identifiability problem, the mean-subtraction fix, and how sure the champion is",
          "why": "The shape of DuelingDQN's two heads",
          "lab": {
            "id": "p5-05",
            "title": "Two heads, one answer",
            "format": "pytest",
            "minutes": 15
          },
          "call": "p5-05"
        },
        {
          "n": "06",
          "file": "06-double-dqn.html",
          "title": "Double DQN",
          "group": "concepts",
          "blurb": "Maximization bias worked by hand, the decoupled target, masking and the cut-off, and the prime suspect",
          "why": "The three lines that make the agent Double DQN",
          "lab": {
            "id": "p5-06",
            "title": "Who chooses, who scores",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p5-06"
        },
        {
          "n": "07",
          "file": "07-prioritized-replay.html",
          "title": "Prioritized replay",
          "group": "concepts",
          "blurb": "Sampling by TD error, the α and β arithmetic, the sum tree, and a bug no reward curve shows",
          "why": "What PrioritizedReplayBuffer does and where its recorded bug sits",
          "lab": {
            "id": "p5-07",
            "title": "A memory that ranks",
            "format": "pytest",
            "minutes": 25
          },
          "call": "p5-07"
        },
        {
          "n": "08",
          "file": "08-reward-scale-trap.html",
          "title": "The reward-scale trap",
          "group": "concepts",
          "blurb": "Why stable training hides a scale problem, the four speed limits, and the centring fix",
          "why": "The likeliest reason Phase 5 looks broken when it isn't",
          "lab": {
            "id": "p5-08",
            "title": "Speed limits",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p5-08"
        },
        {
          "n": "09",
          "file": "09-build-it-yourself.html",
          "title": "Build it yourself",
          "group": "capstone",
          "blurb": "Build the champion's learner in seven checked stages, then switch ε off and close the case's maths",
          "why": "Understanding by building, not by reading someone else's finished file",
          "lab": {
            "id": "p5-cap",
            "title": "Toy race network learner",
            "format": "pytest",
            "minutes": 90
          },
          "call": "p5-09"
        },
        {
          "n": "10",
          "file": "10-back-to-the-plan.html",
          "title": "Back to the plan",
          "group": "project",
          "blurb": "The real network, its settings, the issues on record, the tests, and the verdict on Case 4",
          "why": "Bridges the theory to the files you are about to write, and closes the case",
          "lab": {
            "id": "p5-10",
            "title": "Redo the arithmetic, and what the tests catch",
            "format": "quiz",
            "minutes": 25
          },
          "call": "p5-10"
        }
      ],
      "case": {
        "title": "The champion who keeps pitting",
        "question": "A DQN within 0.28 s of the optimum is reported 1.94 s off, making pit stops its own network rates worse. Why, and what should the plan change?"
      }
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
          "title": "Case brief",
          "group": "start",
          "blurb": "Race a rival on the Pit Wall, then open Case 5: why does stopping before the rival never gain anything?",
          "why": "Phase 6 puts other cars on the track"
        },
        {
          "n": "01",
          "file": "01-multi-car-mdp.html",
          "title": "One car to N",
          "group": "concepts",
          "blurb": "What changes when rivals are added: three new state features, a 19-wide network, and rivals as fixed scripts",
          "why": "Frames every other page as a consequence of this one change",
          "lab": {
            "id": "p6-01",
            "title": "Three new numbers",
            "format": "paper",
            "minutes": 10
          },
          "call": "p6-01"
        },
        {
          "n": "02",
          "file": "02-credit-assignment.html",
          "title": "Credit assignment",
          "group": "concepts",
          "blurb": "Sparse and dense rewards, credit assignment, the plan's two stand-ins, and whether a place bonus makes the rival matter",
          "why": "Why the plan trains and compares three reward designs",
          "lab": {
            "id": "p6-02",
            "title": "Sparse, dense, and farmed",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p6-02"
        },
        {
          "n": "03",
          "file": "03-potential-based-shaping.html",
          "title": "Potential-based shaping",
          "group": "concepts",
          "blurb": "Why F = γΦ(s′) − Φ(s) can't change the best policy, a worked chain, and the zero every ending needs",
          "why": "The principled design the plan's third reward claims to be",
          "lab": {
            "id": "p6-03",
            "title": "A potential that cannot change the answer",
            "format": "pytest",
            "minutes": 20
          },
          "call": "p6-03"
        },
        {
          "n": "04",
          "file": "04-overtaking-dirty-air.html",
          "title": "Overtaking & dirty air",
          "group": "concepts",
          "blurb": "The dirty-air line and the pass sigmoid, checked against the plan's own numbers, and a faster car the wake keeps behind",
          "why": "The formulas behind overtaking.py",
          "lab": {
            "id": "p6-04",
            "title": "How likely is the pass?",
            "format": "widget",
            "minutes": 15
          },
          "call": "p6-04"
        },
        {
          "n": "05",
          "file": "05-position-and-blocking.html",
          "title": "Position vs. the undercut",
          "group": "concepts",
          "blurb": "Why sorting by time kills the undercut, the one-line blocking fix, and the undercut window it opens",
          "why": "Without it, Phase 6's most interesting goal and all of Phase 8 are out of reach",
          "lab": {
            "id": "p6-05",
            "title": "Stuck behind",
            "format": "widget",
            "minutes": 15
          },
          "call": "p6-05"
        },
        {
          "n": "06",
          "file": "06-bug-ledger.html",
          "title": "The bug ledger",
          "group": "concepts",
          "blurb": "The double-counted rival, the overwritten pass, the wake left out of the lap time, the mislabelled shaping, and four smaller items",
          "why": "Each one would make a training run look like it worked when it didn't",
          "lab": {
            "id": "p6-06",
            "title": "The bug ledger",
            "format": "pytest",
            "minutes": 20
          },
          "call": "p6-06"
        },
        {
          "n": "07",
          "file": "07-non-stationarity.html",
          "title": "Non-stationarity preview",
          "group": "concepts",
          "blurb": "Why a learning opponent breaks the fixed-environment assumption, and why a rival's choice has to reach your lap times first",
          "why": "Why this phase's rivals are scripts, and why Phase 8 is harder",
          "lab": {
            "id": "p6-07",
            "title": "A target that moves",
            "format": "notebook",
            "minutes": 15
          },
          "call": "p6-07"
        },
        {
          "n": "08",
          "file": "08-build-it-yourself.html",
          "title": "Build it yourself",
          "group": "capstone",
          "blurb": "Build a toy blocking race, add passing and shaped rewards, then the two-car capstone that draws the undercut window",
          "why": "Understanding by building the exact failure and fix yourself, not just reading about them",
          "lab": {
            "id": "p6-cap",
            "title": "Two-car duel race",
            "format": "pytest",
            "minutes": 90
          },
          "call": "p6-08"
        },
        {
          "n": "09",
          "file": "09-back-to-the-plan.html",
          "title": "Back to the plan",
          "group": "project",
          "blurb": "The real state, rewards and rivals, where each fault lives, what the plan's tests can see, and the verdict on Case 5",
          "why": "Bridges the theory to the files you are about to write, and closes the case",
          "lab": {
            "id": "p6-09",
            "title": "Tag, compute, and what the tests can see",
            "format": "quiz",
            "minutes": 20
          },
          "call": "p6-09"
        }
      ],
      "case": {
        "title": "The undercut that doesn't exist",
        "question": "In the plan's race, stopping before a rival never gains anything: the best stop is the same whatever lap the rival stops on. Why, and what should the plan change?"
      }
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
          "title": "Case brief",
          "group": "start",
          "blurb": "Run the plan's pool sampler, then open Case 6: why does the self-play run die at episode zero?",
          "why": "Phase 8 makes the opponent learn too"
        },
        {
          "n": "01",
          "file": "01-non-stationarity-revisited.html",
          "title": "Non-stationarity, revisited",
          "group": "concepts",
          "blurb": "What breaks when the opponent learns too, latest-only self-play chasing its own tail on the duel, and the three training paradigms",
          "why": "Why self-play is a harder problem than Phase 6, not Phase 6 with a smarter rival",
          "lab": {
            "id": "p8-01",
            "title": "When the opponent learns too",
            "format": "notebook",
            "minutes": 15
          },
          "call": "p8-01"
        },
        {
          "n": "02",
          "file": "02-nash-and-fictitious-play.html",
          "title": "Nash & fictitious play",
          "group": "concepts",
          "blurb": "Nash equilibria, fictitious play, matching pennies worked round by round, and the duel's mixed equilibrium",
          "why": "The target the checkpoint pool approximates",
          "lab": {
            "id": "p8-02",
            "title": "Best responses, cycles, and fictitious play",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p8-02"
        },
        {
          "n": "03",
          "file": "03-checkpoint-pool.html",
          "title": "Checkpoint pool",
          "group": "concepts",
          "blurb": "The recency rule as a probability calculation, the empty slice at n = 1, what the rule costs on the duel, and the evaluation trap",
          "why": "The mechanism behind CheckpointPool, and the first half of the case",
          "lab": {
            "id": "p8-03",
            "title": "The checkpoint pool",
            "format": "pytest",
            "minutes": 20
          },
          "call": "p8-03"
        },
        {
          "n": "04",
          "file": "04-pettingzoo-apis.html",
          "title": "PettingZoo APIs",
          "group": "concepts",
          "blurb": "PettingZoo's AEC and Parallel APIs, each with a worked micro-example, and why F1 needs Parallel",
          "why": "The API F1PettingZooEnv is built on",
          "lab": {
            "id": "p8-04",
            "title": "AEC and Parallel",
            "format": "pytest",
            "minutes": 20
          },
          "call": "p8-04"
        },
        {
          "n": "05",
          "file": "05-first-opponent-problem.html",
          "title": "The first opponent",
          "group": "concepts",
          "blurb": "Why a greedy untrained network is a fixed script, not a random opponent, and what to seed the pool with",
          "why": "Early self-play trains against one quirk unless the seed is fixed",
          "lab": {
            "id": "p8-05",
            "title": "The first opponent",
            "format": "notebook",
            "minutes": 15
          },
          "call": "p8-05"
        },
        {
          "n": "06",
          "file": "06-blocking-model-dependency.html",
          "title": "The blocking dependency",
          "group": "concepts",
          "blurb": "Phase 6's blocking finding where it decides this phase's result, and why the rule has to reach F1PettingZooEnv",
          "why": "Without it, the headline histogram can't show an undercut however training goes",
          "lab": {
            "id": "p8-06",
            "title": "Where the undercut comes from",
            "format": "quiz",
            "minutes": 10
          },
          "call": "p8-06"
        },
        {
          "n": "07",
          "file": "07-is-it-bimodal.html",
          "title": "Is it bimodal?",
          "group": "concepts",
          "blurb": "A permutation-test null for the pit-delta histogram, stratified for causes both cars share, and what it cannot show",
          "why": "Makes \"emergent undercut\" a defensible claim, not an eyeballed one",
          "lab": {
            "id": "p8-07",
            "title": "Is it really a reaction?",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p8-07"
        },
        {
          "n": "08",
          "file": "08-build-it-yourself.html",
          "title": "Build it yourself",
          "group": "capstone",
          "blurb": "The pit-timing duel solved exactly in seven stages, from the payoff to the null test on your own result",
          "why": "Understanding by building the exact failure and fix yourself",
          "lab": {
            "id": "p8-cap",
            "title": "The pit-timing duel",
            "format": "pytest",
            "minutes": 90
          },
          "call": "p8-08"
        },
        {
          "n": "09",
          "file": "09-back-to-the-plan.html",
          "title": "Back to the plan",
          "group": "project",
          "blurb": "The env, the loop and the pool's parameters, a reading order, what the checklist catches, and the verdict on Case 6",
          "why": "Bridges the theory to the files you are about to write, and closes the case",
          "lab": {
            "id": "p8-09",
            "title": "Parameters, lines, and what catches what",
            "format": "quiz",
            "minutes": 20
          },
          "call": "p8-09"
        }
      ],
      "case": {
        "title": "The run that dies at episode zero",
        "question": "The plan's self-play run crashes before its first checkpoint, and its headline histogram could not show an undercut even if it lived. Why, and what should the plan change?"
      }
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
          "title": "Case brief",
          "group": "start",
          "blurb": "Watch MaskablePPO train on the plan's reward in the Training room, then open Case 7: why does it learn nothing?",
          "why": "Phase 9 learns the policy itself, through a library"
        },
        {
          "n": "01",
          "file": "01-policy-gradients-reinforce.html",
          "title": "Policy gradients: REINFORCE",
          "group": "concepts",
          "blurb": "The policy gradient theorem, REINFORCE worked by hand, and what a raw reward does to every push",
          "why": "The first algorithm of the family PPO belongs to",
          "lab": {
            "id": "p9-01",
            "title": "The log-gradient trick",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p9-01"
        },
        {
          "n": "02",
          "file": "02-actor-critic-advantage.html",
          "title": "Actor-critic & advantage",
          "group": "concepts",
          "blurb": "Baselines, the critic and the advantage, and a baseline that arrives after the policy has stopped exploring",
          "why": "Why PPO carries a critic at all",
          "lab": {
            "id": "p9-02",
            "title": "What a baseline buys",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p9-02"
        },
        {
          "n": "03",
          "file": "03-generalized-advantage-estimation.html",
          "title": "Generalized advantage estimation",
          "group": "concepts",
          "blurb": "GAE-λ as a dial between one-step and whole-race advantages, the missing gae_lambda key, and a PPO that learns from the raw reward",
          "why": "The advantage Stable-Baselines3 computes",
          "lab": {
            "id": "p9-03",
            "title": "GAE, backwards",
            "format": "pytest",
            "minutes": 20
          },
          "call": "p9-03"
        },
        {
          "n": "04",
          "file": "04-ppo-clipped-objective.html",
          "title": "PPO's clipped objective",
          "group": "concepts",
          "blurb": "The probability ratio and the clip, worked in both signs, ten passes per batch, and why the clip isn't the brake in the case",
          "why": "The trick that makes reusing a batch safe",
          "lab": {
            "id": "p9-04",
            "title": "Where the clip binds",
            "format": "widget",
            "minutes": 15
          },
          "call": "p9-04"
        },
        {
          "n": "05",
          "file": "05-build-vs-buy.html",
          "title": "Why build vs. buy",
          "group": "concepts",
          "blurb": "Loud failures and quiet ones, PPO's quiet details, and what buying an algorithm doesn't buy",
          "why": "The plan's build-vs-buy argument, and its limit",
          "lab": {
            "id": "p9-05",
            "title": "Loud and quiet",
            "format": "pytest",
            "minutes": 20
          },
          "call": "p9-05"
        },
        {
          "n": "06",
          "file": "06-stable-baselines3-api.html",
          "title": "Stable-Baselines3's API",
          "group": "concepts",
          "blurb": "VecEnvs, the rollout arithmetic, .learn(), .predict() and the mask, and the critic's fixed pace that cracks the case",
          "why": "The API the plan calls, and where J3 lives",
          "lab": {
            "id": "p9-06",
            "title": "The library, from the outside",
            "format": "notebook",
            "minutes": 20
          },
          "call": "p9-06"
        },
        {
          "n": "07",
          "file": "07-pickling-and-subprocvecenv.html",
          "title": "Lambdas, processes & the guard",
          "group": "concepts",
          "blurb": "Lambdas across a process boundary, what actually breaks under spawn, the __main__ guard, and DummyVecEnv",
          "why": "An audit finding tested, corrected, and settled for this environment",
          "lab": {
            "id": "p9-07",
            "title": "Test the claim",
            "format": "pytest",
            "minutes": 20
          },
          "call": "p9-07"
        },
        {
          "n": "08",
          "file": "08-unfair-comparison.html",
          "title": "The unfair comparison",
          "group": "concepts",
          "blurb": "Same timesteps is not same experience: the 7.7× budget gap, two principled fixes, and what the comparison would say about the case",
          "why": "Without it, the DQN-vs-PPO result mixes the algorithm with the budget",
          "lab": {
            "id": "p9-08",
            "title": "Matched budgets",
            "format": "notebook",
            "minutes": 15
          },
          "call": "p9-08"
        },
        {
          "n": "09",
          "file": "09-build-it-yourself.html",
          "title": "Build it yourself",
          "group": "capstone",
          "blurb": "A policy-gradient learner on the toy race in seven checked stages, from a masked table policy to PPO at ten passes per batch",
          "why": "Understanding by building the exact mechanism and the exact failure yourself",
          "lab": {
            "id": "p9-cap",
            "title": "Policy gradient on the toy race",
            "format": "pytest",
            "minutes": 90
          },
          "call": "p9-09"
        },
        {
          "n": "10",
          "file": "10-back-to-the-plan.html",
          "title": "Back to the plan",
          "group": "project",
          "blurb": "The wrapper, the agent and the config, a reading order, what the checklist catches, and the verdict on Case 7",
          "why": "Bridges the theory to the files you are about to write, and closes the case",
          "lab": {
            "id": "p9-10",
            "title": "Keys, lines, and what catches what",
            "format": "quiz",
            "minutes": 20
          },
          "call": "p9-10"
        }
      ],
      "case": {
        "title": "The learner that learns nothing",
        "question": "MaskablePPO, a well-tested library, trained on the plan's reward ends on the plan that never chooses to stop, on every seed. Why, and what should the plan change?"
      }
    }
  ]
};
