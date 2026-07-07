# F1 Pit & Tire Strategy RL Agent — Build Plan & Learning Roadmap

*Working title: **Stratex** (change it to whatever you like — this is just so the doc has a name to refer to).*

## How to use this document

Every phase below has three parts:
- **Concepts you need** — the exact RL ideas required for that phase, explained just deep enough to build with, plus a time-boxed pointer to go deeper.
- **What you'll build** — the concrete engineering deliverable.
- **Definition of done** — how you know the phase actually worked, not just "ran without crashing."

You learn each concept immediately before the phase that needs it, then implement it while it's fresh. Nowhere in this plan should you be reading theory for more than a few hours before writing code that uses it.

The dashboard is not a separate final phase — it starts in Phase 2, right after the simulator exists, and grows with every subsequent phase. This matches what you asked for.

**Rough total effort:** Phases 0–7 (the complete, demo-able project) run roughly 22–36 focused days spread over however many weeks suits you. Phases 8–9 are open-ended stretch goals on top of that. Treat every estimate below as a rough dial, not a deadline — the point of learning-while-building is that Phases 4 and 5 (your first real RL algorithms) will take as long as they take.

---

## System architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│   FastF1 data    │────▶│  Calibration      │────▶│  Simulator (Gym    │
│  (real races)    │     │  layer            │     │  environment)      │
│  laps, tyres,    │     │  tyre-deg curves, │     │  MDP: state/action/│
│  weather, SC     │     │  SC rates, pit    │     │  reward/transition │
│  events          │     │  loss, scenario   │     │                    │
└─────────────────┘     │  templates        │     └─────────┬──────────┘
                         └──────────────────┘               │
                                                             ▼
                                                 ┌───────────────────────┐
                                                 │       Agents          │
                                                 │  baseline (rule-based)│
                                                 │  Q-learning / SARSA   │
                                                 │  DQN                  │
                                                 │  (stretch: PPO, MARL) │
                                                 └───────────┬───────────┘
                                                             │
                         ┌───────────────────────────────────┘
                         ▼
              ┌────────────────────┐        ┌────────────────────┐
              │  FastAPI backend   │◀──────▶│  React dashboard   │
              │  serves race       │        │  race replay, agent │
              │  replays + agent   │        │  reasoning panel,   │
              │  decisions         │        │  agent comparison   │
              └────────────────────┘        └────────────────────┘
```

Everything in this system runs comfortably on a laptop CPU; the RTX 4050 is a bonus, not a requirement. The state and action spaces here are small (a handful of features, 4–6 discrete actions), so even the DQN phase trains in minutes, not hours. The compute-constraint conversation we had earlier basically doesn't bite for this project — that's part of why it was a good pick.

---

## The core design: your MDP

This is the intellectual heart of the project — designing this well matters more than any single algorithm choice.

**State (observation).** Only include what actually affects future dynamics — this is the Markov property in practice, and it's worth being disciplined about it:
- `laps_remaining`
- `tire_compound` (SOFT / MEDIUM / HARD, later + INTER / WET)
- `tire_age` (laps since last pit)
- `weather_regime` (dry / damp / wet, or a continuous rain intensity)
- `track_temp`
- `safety_car_active` (bool)
- `compounds_used_so_far` (needed to track the real FIA rule: a dry race requires using at least two different dry compounds — a nice authentic constraint to encode)

Notice `cumulative_race_time_so_far` is **not** in the state. It has no effect on what happens next lap — future lap time depends on tire age, compound, and weather, not on how much time has already elapsed. Leaving it out isn't an oversight; it's the state being a *sufficient statistic* for the dynamics. That distinction is worth understanding early — it's the practical meaning of "Markov."

**Action (discrete, one decision per lap):** `stay out` / `pit → soft` / `pit → medium` / `pit → hard` / `pit → intermediate` / `pit → wet`.

**Reward (v1, single agent, Phases 1–5):** `-lap_time_this_lap` every step, where the pit-lap's `lap_time` already includes the real pit-lane time loss. Summed over an episode, this literally equals `-total_race_time` — the dense, per-step reward *is* the true objective, not a proxy for it. This is the cleanest version of a reward function you'll get in this whole project; savor it, because Phase 6 (rivals) forces a harder tradeoff.

**Transition dynamics:**
`lap_time = base_pace(circuit) + tyre_degradation(compound, tyre_age) + fuel_effect(laps_remaining) + weather_penalty(regime) + noise`

**A key design trick for realism without reinventing weather/incident modeling:** rather than hand-building a full stochastic weather/safety-car model from scratch, treat entire historical races as **scenario templates**. Phase 0 extracts real weather traces and real safety-car timing from actual races via FastF1; each simulated episode samples one of these real traces as the "exogenous" backdrop (things outside the strategist's control), while tyre degradation and the agent's choices are what actually varies. This keeps randomness genuinely grounded in history instead of invented, and it's much less work than building a full weather Markov chain from scratch. You can add a parametric model later if you want more scenario variety than your historical sample provides.

**Sequencing tip (this is itself an RL concept — curriculum learning):** build the simulator to support full complexity (weather, safety cars, all compounds) from day one, but for your *first* training runs in Phase 4, restrict the scenario library to dry, no-safety-car races. Get a clean signal that Q-learning works at all before layering stochastic complexity back in. Training agents on an easy version of a task before the full version is a real, recognized technique, not just "start simple" generic advice.

---

## Repo structure

```
stratex/
├── data/
│   ├── raw/                 # FastF1 cache
│   └── processed/           # calibration params, scenario templates (JSON/parquet)
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_calibration.ipynb
│   └── 03_agent_comparison.ipynb
├── src/
│   ├── data/fetch.py         # FastF1 wrappers + caching
│   ├── data/calibrate.py     # tyre-deg curve fitting, SC-rate estimation
│   ├── env/f1_strategy_env.py
│   ├── env/dynamics.py       # lap-time model
│   ├── agents/baseline_agent.py
│   ├── agents/q_learning_agent.py
│   ├── agents/dqn_agent.py
│   ├── agents/ppo_agent.py   # stretch
│   └── evaluation/evaluate.py
├── backend/main.py            # FastAPI
├── frontend/src/               # React
├── configs/                    # circuit configs, agent hyperparams (YAML)
├── tests/
│   ├── test_env.py
│   └── test_agents.py
├── requirements.txt
└── README.md
```

---

## Phase 0 — Data foundation & calibration

**What you'll build:** Pull 2–4 seasons of race data for a handful of circuits via FastF1 (free, no API key, full coverage from 2018 onward). Pull `laps` (with `Compound`, `TyreLife`, `Stint`, `PitInTime`/`PitOutTime`), `weather_data`, and `track_status`/race-control messages for safety cars. Use FastF1's built-in `pick_quicklaps()` to filter out in/out-laps and safety-car laps before fitting anything. Fit lap-time-vs-tyre-age curves per compound per circuit; compute empirical safety-car rate per circuit; extract real weather traces as your scenario templates; measure real pit-lane time loss per circuit.

Start with 1–2 circuits and one season to get the whole pipeline working end-to-end fast, then widen. Let the actual data tell you which circuits are interesting (high vs. low degradation, frequent vs. rare safety cars) rather than assuming.

**Concepts you need:** None yet — this is pure data engineering. Save your first RL reading for Phase 1.

**Definition of done:** a `calibration_params.json`/parquet per circuit with degradation curves, SC rate, pit loss, and a library of at least ~10 scenario templates; an EDA notebook with the degradation and SC-rate plots.

*(One line for your eventual README: FastF1 is an unofficial, community-built library, not an official FIA/F1 data product — standard practice in this space, worth a passing disclaimer.)*

---

## Phase 1 — Build the simulator (environment)

**Concepts you need:**
- **MDP (Markov Decision Process):** state, action, reward, transition, discount factor `γ`. A race, lap by lap, is a natural MDP — what matters for the next decision is the current situation, not the full history of how you got there.
- **Policy, episode, return:** a policy maps states to actions; an episode is one race start-to-finish; return is the (discounted) sum of rewards over the episode.
- **Gymnasium API conventions:** `reset()` returns `(observation, info)`, `step(action)` returns `(observation, reward, terminated, truncated, info)`. This is the industry-standard interface (maintained by the Farama Foundation), and using it correctly is worth doing even though it's "just" software convention — it signals you know the ecosystem.

*Resource, time-boxed to ~2–3 hours:* Sutton & Barto, *Reinforcement Learning: An Introduction* (free PDF), chapters 1 and 3. Or David Silver's UCL RL course, lectures 1–2 (free on YouTube). Enough to write the environment correctly — no need for anything past this yet.

**What you'll build:** `F1StrategyEnv(gym.Env)` implementing the MDP above.

```python
import gymnasium as gym
from gymnasium import spaces

class F1StrategyEnv(gym.Env):
    """One episode = one simulated race at a given circuit."""

    def __init__(self, circuit_config: dict, scenario_library: list):
        super().__init__()
        self.action_space = spaces.Discrete(6)  # stay out + 5 pit choices
        self.observation_space = spaces.Box(low=..., high=..., shape=(N_FEATURES,))

    def reset(self, seed=None, options=None):
        # sample a scenario template, reset tyre/lap state
        ...
        return observation, info

    def step(self, action):
        # apply pit decision, advance one lap via dynamics.py, compute reward
        ...
        return observation, reward, terminated, truncated, info
```

Test it first with a random policy and a fixed "always pit on lap 20" policy — not to learn anything yet, just to sanity-check the dynamics look realistic (lap times in a believable range, tyre age resets on pit, degradation curves match Phase 0's calibration).

**Definition of done:** environment registered with Gymnasium, passes manual sanity checks, and has at least 3 `pytest` tests (e.g., tyre age resets on pit, reward sign is correct, episode terminates at the right lap).

---

## Phase 2 — Dashboard scaffold (walking skeleton)

This is where the dashboard starts — right after the simulator exists, not at the end.

**Concepts you need:** none new.

**What you'll build:** A minimal FastAPI backend with one endpoint (`GET /race/{circuit}/{seed}` returning a lap-by-lap replay of *any* policy playing through the simulator) and a minimal React frontend that animates that replay: a lap-time trace, tyre-compound color coding, pit-stop markers. Feed it the random/fixed policies from Phase 1 for now — there's no "real" agent yet, and that's fine. The point is the full-stack skeleton exists early, so every later phase just extends it instead of bolting on a UI at the end.

**Definition of done:** you can open the dashboard locally and watch a full simulated race play out, lap by lap, for a policy that isn't learned yet.

---

## Phase 3 — Rule-based baseline strategist

**Concepts you need:** none new — this is F1 domain logic, not RL.

**What you'll build:** A reactive baseline (e.g., "pit when the tyre-age-adjusted pace delta crosses a threshold," or simple fixed one-stop/two-stop plans) to compare every future RL agent against. Wire it into the Phase 2 dashboard so you can watch it race.

**Definition of done:** baseline agent produces sensible, explainable strategies across your scenario library; its race-time distribution (run across many seeds) is recorded as your benchmark to beat.

---

## Phase 4 — Tabular Q-learning agent (+ SARSA)

This is the heaviest theory chunk in the whole project — budget real time for it, everything downstream builds on it.

**Concepts you need:**
- **Q-values / action-value function `Q(s,a)`:** expected return from taking action `a` in state `s`, then acting well afterward.
- **Bellman optimality equation:** `Q*(s,a) = E[r + γ · max_a' Q*(s',a')]` — the optimal value of an action equals the immediate reward plus the discounted value of playing optimally from whatever comes next.
- **Temporal-difference learning — the Q-learning update:**
  `Q(s,a) ← Q(s,a) + α [ r + γ·max_a' Q(s',a') − Q(s,a) ]`
  The bracketed term is the "TD error." This lets the agent learn from every single step rather than waiting for the episode to end (unlike Monte Carlo methods).
- **Epsilon-greedy exploration:** with probability `ε`, act randomly; otherwise act greedily on current Q-estimates. Needed because the agent has to actually try "pit early" or "risk one more lap" to find out if it's good — usually `ε` decays over training (explore a lot early, exploit more later).
- **State discretization:** tabular Q-learning needs a finite table, so continuous-ish features (tyre age, laps remaining) get binned. Too coarse loses important distinctions; too fine and the table explodes — this tension is exactly what motivates Phase 5.
- **Learning rate `α` and discount `γ`:** `α` controls how much new experience overwrites old estimates; `γ` controls how much future reward matters. Because a pit decision now can pay off 15 laps later, you want `γ` close to 1 (try 0.95–0.99).
- **On-policy vs. off-policy (Q-learning vs. SARSA):** Q-learning is off-policy — it bootstraps off the *best possible* next action regardless of what was actually taken while exploring. SARSA is on-policy — it bootstraps off the action actually taken. Implementing both and comparing them on the same races is the fastest way to feel the difference, especially in a risky, safety-car-prone environment where Q-learning's "optimistic" assumption about future play can behave differently from SARSA's more cautious, exploration-aware one.

*Resource, time-boxed to ~4–6 hours:* Sutton & Barto chapter 6 (Temporal-Difference Learning) is the single most important chapter for this whole project. David Silver lectures 4–5 cover the same ground.

**What you'll build:** `q_learning_agent.py` and `sarsa_agent.py`, trained on the dry/no-SC scenario subset first (see the curriculum-learning note above), then the full scenario library. Starting point: `α=0.1`, `γ=0.97`, `ε` decaying from 1.0 to 0.05 over the first half of training, a few thousand simulated episodes (cheap — these aren't real-time physics sims).

**Definition of done:** learning curve trending upward and plateauing; trained agent beats the Phase 3 baseline's mean race time across multiple seeds (not one lucky run); Q-learning vs. SARSA comparison plotted; agent's decisions visible in the dashboard.

---

## Phase 5 — DQN (deep RL / function approximation)

**Concepts you need:**
- **Why tabular breaks — the curse of dimensionality:** every extra state feature multiplies the table size; once you add rival information (Phase 6), a table becomes sparse and slow to learn from.
- **Function approximation:** replace the table with a neural network `Q(s,a; θ)` that generalizes across similar states it hasn't exactly seen before.
- **Experience replay buffer:** store past `(s,a,r,s')` transitions and train on randomly sampled mini-batches instead of only the most recent one. Breaks the correlation between consecutive (very similar) laps, which would otherwise destabilize neural-network training, and reuses data for better sample efficiency.
- **Target network:** keep a second, slowly-updated copy of the network to compute the TD target, instead of chasing a constantly-moving target with the same network being updated. Update it every few hundred/thousand steps (or a slow "Polyak" soft update).
- **DQN loss:** mean-squared error between the network's `Q(s,a)` prediction and the TD target — the same idea as the tabular update, just via gradient descent on network weights instead of overwriting a table cell.

*Resource, time-boxed to ~3–4 hours:* the original DQN paper (Mnih et al., 2015, "Human-level control through deep reinforcement learning") is short and readable. OpenAI's "Spinning Up in Deep RL" intro sections are a good practical companion. A lot of the rest of your DQN understanding will come from watching a training run fail to converge and figuring out why — that's normal, not a sign you're doing it wrong.

**What you'll build:** `dqn_agent.py` in PyTorch — small MLP (2 hidden layers, ~128 units is plenty here), replay buffer ~50–100k transitions, batch size 64, learning rate 1e-3 to 1e-4, target update every 500–1000 steps. This trains in minutes given how small your state/action space is.

**Definition of done:** three-way comparison plot (baseline vs. Q-learning vs. DQN) across multiple seeds; DQN at least matches tabular Q-learning's performance (it may not beat it yet on this simple a problem — that's a legitimate and interesting finding to write up, not a failure).

---

## Phase 6 — Multi-car environment + rule-based rivals

**Concepts you need:**
- **Reward shaping & the credit-assignment problem:** once the goal becomes "finish as high as possible relative to rivals" instead of "minimize your own time," the natural reward (final position) is sparse — it's only known at the flag, after hundreds of decisions. Dense proxies (e.g., per-lap change in gap-to-rival) are easier to learn from but risk the agent optimizing the proxy instead of the real goal — e.g., an agent rewarded for closing gaps might push tyres too hard early for a short-term gain that costs it a podium later. This is the classic reward-shaping tradeoff, and it's worth deliberately trying 2–3 reward designs here and comparing, rather than reading extensively about it.
- **Potential-based shaping (good to know, optional to implement):** Ng, Harada & Russell (1999) showed that shaping reward as the *difference* of a potential function between consecutive states provably doesn't change the optimal policy — only how fast you find it. Worth knowing as the "principled" version of shaping, versus ad-hoc shaping that can silently change what's optimal.
- **Non-stationarity (preview for Phase 8):** once rivals are more than fixed scripts, the environment "changes" as they adapt too, breaking the standard fixed-environment assumption most RL theory relies on. Fixed-policy rivals (this phase) sidestep that entirely — which is exactly why this is the sensible step before real multi-agent learning.

**What you'll build:** extend the environment to N cars. Add `gap_to_car_ahead`, `gap_to_car_behind`, `position` to the state. Add a simple overtaking model (if your pace is meaningfully faster than the car ahead for several consecutive laps, allow a probabilistic pass; otherwise apply a small "dirty air" pace penalty for following closely — a real, well-known F1 effect). Retrain DQN in this richer environment with your redesigned reward.

**Definition of done:** DQN agent trained against N rule-based rivals; dashboard shows a full multi-car race with positions; a short write-up comparing your 2–3 reward designs and what each one actually optimized for in practice.

---

## Phase 7 — Dashboard polish + historical comparison

**Concepts you need:** none new — this is a product/engineering phase.

**What you'll build:** polish the dashboard into something demo-ready: full multi-car replay, a "what the agent was thinking" panel showing the state features and Q-values at each decision point (genuine interpretability — a recruiter can see *why* it chose to pit, not just that it did), and a headline feature: pick a real historical Grand Prix, let your best agent "re-strategize" it, and show the counterfactual finish next to what actually happened.

**Definition of done:** a shareable, screenshot/GIF-worthy dashboard; this is also the point to write the README properly (see Portfolio Framing below).

---

## Phase 8 (stretch) — Multi-agent self-play

**Concepts you need:**
- **Multi-agent RL & non-stationarity:** with multiple simultaneously-learning agents, each one's effective "environment" includes the others' evolving behavior, which breaks the stationarity assumption behind single-agent convergence results. In practice, treating each car as an "independent learner" (each running its own DQN, ignoring the theoretical issue) often still works reasonably well — a known, pragmatic simplification worth naming as such.
- **Self-play:** train against past or currently-evolving versions of your own policy (or a pool of them) instead of only fixed scripts, so the agent has to keep improving against improving competition.
- **PettingZoo:** the Farama Foundation's standard multi-agent extension of the Gymnasium API — the natural library if you want to formalize this properly instead of hand-rolling a multi-agent loop.

**What you'll build:** multiple learning DQN agents racing each other, ideally with a pool of past checkpoints as opponents rather than only the live-training version.

**Definition of done:** genuinely open-ended here — if you get emergent strategic behavior you didn't explicitly program (e.g., undercut/overcut patterns arising naturally), that's a strong, distinctive interview story on its own.

---

## Phase 9 (stretch) — PPO via Stable-Baselines3

**Concepts you need:**
- **Policy gradient methods:** instead of learning Q-values and acting greedily w.r.t. them, directly parameterize and optimize the policy itself, nudging it toward actions that led to better-than-expected returns.
- **Actor-critic:** a "critic" estimates a value function to reduce noise in the learning signal; an "actor" is the policy being improved using the critic's feedback.
- **Advantage function:** `A(s,a) = Q(s,a) − V(s)` — how much better an action was than average for that state. Using advantage instead of raw return significantly reduces gradient noise.
- **PPO's clipped surrogate objective:** the trick that makes PPO popular — it explicitly limits how far a policy update can move probabilities away from the pre-update policy, avoiding the large destructive updates that plagued earlier policy-gradient methods.

*Resource, time-boxed to ~2–3 hours:* Sutton & Barto chapter 13 for the foundation; OpenAI Spinning Up's dedicated PPO page (concise, with pseudocode) for the algorithm itself.

**What you'll build:** train PPO via `stable-baselines3` (currently at v2.9.0, PyTorch-based, actively maintained, requires Python 3.10+) rather than implementing PPO from scratch — PPO has enough finicky implementation detail that even experienced practitioners default to a trusted library here. Knowing *when* to build from scratch versus when to reach for a battle-tested library is itself a good engineering judgment call to make explicit in your README.

**Definition of done:** PPO agent compared against your DQN agent on the same multi-car benchmark.

---

## Engineering practices checklist

- Config-driven design: circuit calibration and agent hyperparameters in YAML, not hardcoded.
- Type hints and docstrings throughout `src/`.
- Seed everything (numpy, torch, env) — RL is notoriously run-to-run variable; never trust a single seed's result.
- `pytest` coverage for the environment (tyre-age resets, reward sign, termination conditions) and a regression test that a trained agent beats a random policy.
- Log training curves (TensorBoard is fine; Weights & Biases free tier is a nice, recruiter-legible touch if you want it).
- A `requirements.txt`/`pyproject.toml` with pinned versions.
- Optional flourish: GitHub Actions running `pytest` on push.

## Evaluation methodology

Because the environment is stochastic (weather, safety cars), always evaluate over many episodes/seeds, never a single race. For fair head-to-head comparisons, use **paired seeds** — run the baseline and the RL agent on the *identical* sequence of scenario draws, so differences reflect the strategy, not random luck in which scenarios got sampled. Report mean and variance of race time (and, from Phase 6 on, finishing position), not just a single best run.

## Common pitfalls

1. **A rising learning curve isn't proof of anything by itself.** The #1 RL debugging trap is the agent exploiting a flaw in your reward function rather than learning good strategy. Always manually inspect a handful of full episode traces before trusting a curve.
2. **Unseeded runs make comparisons meaningless.** Always compare across multiple fixed seeds.
3. **Epsilon decaying too fast** locks the agent into whatever mediocre strategy it found early, with no more exploration left to find better pit windows.
4. **Reward/state scale mismatches hit DQN harder than tabular Q-learning** — neural nets are sensitive to input and reward scaling; normalize state features.
5. **A strategy that "wins" in simulation but ignores the two-compound rule isn't a valid F1 strategy** — worth flagging explicitly in evaluation, not just optimizing raw simulated time.

## Portfolio / interview framing

What makes this defensible in an interview, beyond "I built an RL project":
- You designed the MDP yourself — state, action, and reward — rather than plugging into a pre-built Gym environment. That's a higher-signal skill than implementing an algorithm against a given environment.
- The simulator is calibrated against real telemetry, not invented numbers.
- You can explain *why* each algorithmic step was necessary (tabular → DQN motivated by the curse of dimensionality; on-policy vs. off-policy trade-offs; reward-shaping risk) rather than jumping straight to the fanciest available tool.
- Evaluation is statistically honest (multiple seeds, paired comparisons), not a cherry-picked run.
- The dashboard shows actual Q-values/reasoning, not a black box — a real interpretability angle.
- You know when to build from scratch (Q-learning, DQN) versus when to lean on a trusted library (PPO via SB3), and can explain that choice.

Invest real effort in the README: state the problem, show the architecture diagram, embed a learning-curve plot and a results table, and briefly narrate the design decisions above. For a lot of recruiters, the README *is* the project.

## Resource map (quick index)

| Concept | Resource | When |
|---|---|---|
| MDPs, policies, returns | Sutton & Barto ch. 1, 3 / Silver lectures 1–2 | Before Phase 1 |
| Gymnasium API | Farama docs | Phase 1 |
| Q-learning, SARSA, TD learning | Sutton & Barto ch. 6 / Silver lectures 4–5 | Phase 4 |
| DQN, replay buffer, target networks | Mnih et al. 2015 (DQN paper) / Spinning Up intro | Phase 5 |
| Reward shaping | Ng, Harada & Russell 1999 | Phase 6 |
| Multi-agent RL, self-play | PettingZoo docs | Phase 8 |
| Policy gradients, PPO | Sutton & Barto ch. 13 / Spinning Up PPO page | Phase 9 |

---

**Suggested first step:** pick 1–2 circuits and a season to start Phase 0 with, and write the FastF1 ingestion script.