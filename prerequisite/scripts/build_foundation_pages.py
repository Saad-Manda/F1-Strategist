"""Render the six M2 static lessons; no build or Python runtime is needed on hosting."""
import argparse
from html import escape
from build_catalog import LABS, SITE, load_registry, title_for

CONTENT = {
 'p1-state': {
  'question': 'Can identical observations hide different futures?',
  'challenge': 'A switch has mode 0 or 1. FLIP toggles the mode for reward 0. CLAIM ends the task: reward +1 in mode 1, otherwise -1. The broken encoder reports observation 0 in both modes. Starting in mode 0, compare CLAIM with FLIP, CLAIM. Can an agent choose reliably from that observation alone?',
  'choices': ['Both histories must produce the same CLAIM reward.', 'The same broken observation can precede different rewards.', 'The entire action history must always be stored as state.'],
  'experiment': '''<div class="input-row"><label>Initial hidden mode<select id="initial-mode"><option value="0">0</option><option value="1">1</option></select></label><label>Observation encoder<select id="encoder"><option value="broken">Broken: always 0</option><option value="fixed">Repaired: mode</option></select></label><label>Reset seed<input id="switch-seed" type="number" min="0" max="4294967295" value="7"></label></div><div class="button-row"><button id="flip">Step FLIP</button><button id="claim">Step CLAIM</button><button id="seeded-switch">Seeded reset (uniform mode)</button></div><p id="switch-status" role="status"></p><div class="table-wrap"><table><caption>Mode is exposed for investigation; a deployed agent sees only its observation.</caption><thead><tr><th>Step</th><th>Action</th><th>Mode before</th><th>Observation before</th><th>Reward</th><th>Observation after</th><th>Terminated</th></tr></thead><tbody id="switch-trace"></tbody></table></div>''',
  'investigate': 'Reset and CLAIM. Reset again, FLIP, then CLAIM. Switch to the repaired encoder and repeat. A fresh reset starts a new history. Record why the broken observation aliases two different states.',
  'theory': '''<p>A Markov state contains the information needed to determine the distribution of the next state and reward, given an action. An observation may omit some of that information. Here mode is sufficient; a constant observation is not. With a uniform unknown initial mode, an observation-only CLAIM policy has expected reward 0. A known initial mode plus remembered FLIPs can reconstruct mode, but the constant observation alone cannot.</p><p>You do not need to retain an entire history when a compact sufficient summary exists. If a task ends after an intrinsic finite horizon, remaining steps may also matter: encode <code>(mode, remaining)</code>. An external collection cap does not turn remaining collection time into task state.</p>''',
  'task': 'Implement encode_state(mode, remaining=None). Return mode for the continuing switch, or the tuple (mode, remaining) for an intrinsic finite-horizon variant. Reject invalid modes and negative/non-integer horizons. The supplied world uses the encoder in each transition trace.',
  'hints': ['Compare reward distributions for CLAIM at the two hidden modes.', 'The encoder should preserve mode. Extra history is unnecessary once mode is known.', 'Return mode, or (mode, remaining) when remaining is supplied; validate before encoding.'],
  'solution': 'CLAIM from mode 0 gives -1; FLIP then CLAIM gives +1. Both CLAIM decisions see 0 under the broken encoder. Encoding mode separates them, and including remaining time separates finite-horizon decisions that share a mode.',
  'reflect': 'Give the two histories that disprove sufficiency of the broken observation. Explain when remaining time belongs in state. For your project, identify a variable whose omission would change future reward or transition distributions.',
 },
 'p1-return': {
  'question': 'Which rewards belong in a return?',
  'challenge': 'An episode produces rewards [2, -1, 4] and then truly terminates. A broken function discounts every reward once and adds them. Predict G₀ with γ = 0.5. Then inspect how the time index changes each weight.',
  'choices': ['G₀ = 2.5, using weights 1, 0.5, 0.25.', 'G₀ = 2.5, using one common weight 0.5.', 'G₀ = 5, because discount never affects a finished episode.'],
  'experiment': '''<div class="input-row"><label>Discount γ<input id="gamma" type="range" min="0" max="1" step="0.05" value="0.5"></label><label>Return start t<select id="return-start"><option value="0">0</option><option value="1">1</option><option value="2">2</option></select></label></div><p id="return-total" role="status"></p><div class="table-wrap"><table><caption>Forward weighted sum for the selected starting time</caption><thead><tr><th>Reward index</th><th>Reward</th><th>Weight γ^(index−t)</th><th>Contribution</th></tr></thead><tbody id="return-weights"></tbody></table></div><button id="reverse-step">Reveal next reverse accumulation</button><ol id="reverse-trace"></ol>''',
  'investigate': 'At γ = 0.5 the two candidate formulas accidentally agree for G₀. Reveal the reverse accumulation to inspect G₁ and G₂, then try γ = 0 and 1. A single matching number is weak evidence for correct code.',
  'theory': '''<p><code>G_t = r_t + γ r_(t+1) + γ² r_(t+2) + …</code>. Here r_t means the reward on transition t (some texts call it R_(t+1)). Immediate reward has weight 1. Reverse accumulation implements <code>G_t = r_t + γ G_(t+1)</code>, starting with a zero tail after true termination.</p><p>γ = 0 keeps the immediate reward; γ = 1 sums this finite episode. At a nonterminal truncation, a learning target may need a continuation estimate: the zero tail here applies to a genuinely completed trajectory. Return is realised along a trajectory; value is its expectation before outcomes are known.</p>''',
  'task': 'Implement returns(rewards, gamma), returning a list with G_t at every index. Handle an empty trajectory, negative rewards, and γ endpoints. Reject nonfinite rewards and discounts outside [0,1]. The broken version uses a common discount instead of powers.',
  'hints': ['The immediate reward must survive at γ = 0.', 'Work backward; the tail after the last transition is zero.', 'Initialize tail = 0, then tail = reward + gamma * tail for rewards in reverse order. Reverse the collected output.'],
  'solution': 'For γ = 0.5, G₂ = 4, G₁ = -1 + 0.5 × 4 = 1, and G₀ = 2 + 0.5 × 1 = 2.5. The full results are [2,-1,4] at γ = 0 and [5,3,4] at γ = 1. The broken formula can match G₀ while still getting other returns wrong.',
  'reflect': 'Explain why the immediate reward has weight 1, why the reverse recurrence equals the forward sum, and when a zero tail is justified. In your project, distinguish a step reward from the objective accumulated over an episode.',
 },
 'p1-values': {
  'question': 'Is a policy value the best action value?',
  'challenge': 'In state A, DIRECT ends with reward 3. VIA gives reward 1 and moves to B; B has only FINISH, which ends with reward 4. For γ = 1, a policy chooses DIRECT and VIA equally. What is Vπ(A)? A stored value 99 belongs to an illegal action.',
  'choices': ['Vπ(A) = 4; V*(A) = 5.', 'Vπ(A) = 5 because every policy takes its best action.', 'Vπ(A) = 99 because the largest stored value always wins.'],
  'experiment': '''<p class="model-path">A ─DIRECT/+3→ terminal<br>A ─VIA/+1→ B ─FINISH/+4→ terminal</p><div class="input-row"><label>Discount γ<input id="gamma" type="range" min="0" max="1" step="0.05" value="1"></label><label>Policy probability of VIA<input id="policy-p" type="range" min="0" max="1" step="0.05" value="0.5"></label></div><div class="table-wrap"><table><caption>Bellman backup: action returns and policy contributions</caption><thead><tr><th>Action</th><th>Legal?</th><th>Immediate reward</th><th>Discounted continuation</th><th>Q</th><th>Policy probability</th><th>Contribution</th></tr></thead><tbody id="value-table"></tbody></table></div><p id="value-summary" role="status"></p>''',
  'investigate': 'Compare γ = 1 and 0.5. Move the policy slider from 0 to 1. Which quantity changes when the policy changes? Does the illegal 99 ever enter either backup?',
  'theory': '''<p><code>Qπ(s,a) = E[r + γ Vπ(s′)]</code>, with continuation zero at termination. <code>Vπ(s) = Σ_a π(a|s) Qπ(s,a)</code> evaluates a particular policy. Optimality instead uses <code>V*(s) = max_(legal a) Q*(s,a)</code>.</p><p>B has one action so its value is 4. DIRECT has Q = 3; VIA has Q = 1 + γ × 4. This world has no downstream policy choice, so Qπ and Q* coincide here; they generally need not. Illegal actions are excluded before maximizing, and a policy assigns them zero probability. Do not silently renormalize an invalid policy.</p>''',
  'task': 'Implement backup(action_values, policy, legal) returning (policy_value, optimal_value). Validate a nonempty legal set and a normalized nonnegative policy with zero mass on illegal actions. Implement branch_values(gamma, via_probability) using the one-step backup at B. Keep the stored illegal 99 in the table to test masking.',
  'hints': ['Evaluate a policy by its action probabilities, not its best action.', 'The VIA continuation is γ times the value of B; DIRECT has no continuation.', 'Use a weighted sum for Vπ and a maximum over legal entries for V*. Reject policy mass on illegal actions.'],
  'solution': 'At γ = 1, Q(DIRECT)=3 and Q(VIA)=5, so a uniform policy has value 4 and the optimal policy has value 5. At γ = 0.5 both Q values are 3. Illegal 99 contributes to neither the expectation nor the maximum.',
  'reflect': 'Explain the difference between policy evaluation and optimization, with both numerical cases. Identify an illegal action in your project and explain how it should be excluded from a value backup.',
 },
 'p35-backward': {
  'question': 'What changes when only one decision remains?',
  'challenge': 'Use the same branch world: DIRECT earns 3 and terminates; VIA earns 1 then moves to B, whose FINISH earns 4 and terminates. With γ = 1, choose from A when you have two transitions remaining, then when only one remains. This horizon is part of the task.',
  'choices': ['Two steps: VIA; one step: DIRECT.', 'VIA is best at every horizon because B is worth 4.', 'A has value 5 even with zero steps remaining.'],
  'experiment': '''<div class="input-row"><label>Remaining transitions H<input id="horizon" type="number" min="0" max="10" step="1" value="2"></label><label>Discount γ<input id="gamma" type="range" min="0" max="1" step="0.05" value="1"></label></div><button id="backup-step">Reveal next horizon row</button><div class="table-wrap"><table><caption>Start with V₀ = 0; each row reads only the previous horizon</caption><thead><tr><th>Remaining</th><th>V(B)</th><th>Q(A,DIRECT)</th><th>Q(A,VIA)</th><th>V(A)</th><th>Best action</th></tr></thead><tbody id="backward-table"></tbody></table></div><p id="backward-summary" role="status"></p>''',
  'investigate': 'Reveal the rows from zero upward. Compare H = 1 and H = 2, then lower γ. The horizon-zero row has no action and no terminal-tail value. Reset or changing parameters restarts the row reveal.',
  'theory': '''<p>Finite-horizon planning uses <code>V₀(s)=0</code> and <code>V_h(s)=max_a E[r + γ V_(h−1)(s′)]</code>. Terminal successors contribute zero. The index h is remaining transitions, not a loop iteration you can ignore.</p><p>At h = 1, VIA earns only 1 because there is no remaining transition for FINISH. At h = 2 its value is 1 + γ × 4. Reaching the intrinsic horizon ends this task, so state is (location, remaining). Backward induction solves a known model; later model-free labs learn from sampled experience.</p>''',
  'task': 'Implement solve(horizon, gamma) returning rows from h = 0 through H, each with A, B, T values and an A action (None at zero). Use the supplied transition model and the previous row. The independent checker enumerates complete allowed action paths rather than calling your solver as its oracle.',
  'hints': ['The terminal state and horizon-zero states have value zero.', 'At h = 1 use V₀(B), not the eventual value 4.', 'For each legal action sum immediate reward plus γ times the previous-row successor value, then choose the maximum.'],
  'solution': 'V₀(A)=V₀(B)=0. V₁(A)=max(3,1)=3 and V₁(B)=4. V₂(A)=max(3,1+4)=5 at γ=1, so VIA wins. At h=1, DIRECT wins. T remains zero at every horizon.',
  'reflect': 'Explain why the solver reads the preceding horizon row and why the best action can change with remaining time. Relate this to the role of a known-model oracle when comparing a learned agent with exact planning.',
 },
 'p35-stochastic': {
  'question': 'Does the most likely outcome define an action’s value?',
  'challenge': 'SAFE terminates with reward 2. RISKY terminates with reward 10 on WIN and -2 on LOSS. WIN has probability p = 0.25. A broken backup uses only the most likely outcome. Predict the true action values before varying p.',
  'choices': ['RISKY has expected value 1; SAFE has value 2.', 'RISKY has value -2 because LOSS is most likely.', 'RISKY has value 10 because its best outcome is WIN.'],
  'experiment': '''<div class="input-row"><label>WIN probability p<input id="win-p" type="range" min="0" max="1" step="0.01" value="0.25"></label></div><button id="tie-p">Set exact tie p = 1/3</button><div class="table-wrap"><table><caption>All outcomes contribute, including less likely ones</caption><thead><tr><th>Outcome</th><th>Probability</th><th>Reward</th><th>Weighted contribution</th></tr></thead><tbody id="lottery-table"></tbody></table></div><p id="lottery-summary" role="status"></p><div class="input-row"><label>Custom WIN probability<input id="custom-win" type="number" step="0.1" value="0.25"></label><label>Custom LOSS probability<input id="custom-loss" type="number" step="0.1" value="0.75"></label><button id="check-row">Validate custom row</button></div><p id="row-status" role="status"></p>''',
  'investigate': 'Compare p = 0.25, 0.5, and the exact tie button. Enter probabilities summing to 0.8, then a negative probability. Explain why rejecting those rows is better than silently changing the model.',
  'theory': '''<p>A stochastic Bellman backup sums <code>Σ_(s′,r) P(s′,r|s,a)[r + γ V(s′)]</code>. It is an expectation over all outcomes, not the reward of the modal or best outcome. Here all outcomes terminate, so there is no continuation and γ has no effect.</p><p>RISKY has value <code>10p − 2(1−p) = 12p−2</code>; SAFE has value 2. They tie at p = 1/3. Transition probabilities must be finite, nonnegative, and sum to one. Individual samples can disagree with the expectation; a single lucky run does not prove optimality.</p>''',
  'task': 'Implement expected_value(outcomes), where outcomes is a nonempty list of (probability, reward) pairs. Reject negative/nonfinite probabilities, nonfinite rewards, and probability sums outside an explicit 1e-10 tolerance of one. Do not silently normalize rows. The broken version chooses the largest-probability reward.',
  'hints': ['Write a contribution for WIN and for LOSS separately.', 'Validate the probability row before computing its value.', 'Return sum(probability * reward for each outcome); neither max probability nor max reward implements expectation.'],
  'solution': 'At p=0.25, 0.25×10 + 0.75×(-2) = 1, so SAFE wins. At p=0.5 the risky value is 4. At p=1/3 it is 2, a tie. Invalid probability rows are errors rather than new silently normalized models.',
  'reflect': 'Explain why modal, optimistic, and expected backups give different answers. For a project oracle, state when an expected optimum and a future-knowing optimum measure different things.',
 },
 'p35-markov': {
  'question': 'Can a forecast equal knowing the future?',
  'challenge': 'Weather is DRY or WET. From DRY, next-step probabilities are [0.8,0.2]; from WET they are [0.3,0.7]. Starting DRY, predict the probability of DRY two transitions later. A broken sampler picks the most likely state every time.',
  'choices': ['P(DRY after two) = 0.70; a one-step decision from DRY can earn at most 0.8 in expectation.', 'P(DRY after two) = 0.64 because only DRY→DRY→DRY counts.', 'A policy can score 1 on every prediction because the model probabilities are known.'],
  'experiment': '''<div class="input-row"><label>Initial weather<select id="weather-start"><option value="0">DRY</option><option value="1">WET</option></select></label><label>Seed<input id="weather-seed" type="number" min="0" max="4294967295" step="1" value="7"></label><label>Collection cap<input id="weather-cap" type="number" min="1" max="100" step="1" value="10"></label></div><div class="button-row"><button id="weather-step">Step distribution + sample</button><button id="weather-many">Run to collection cap</button></div><p id="weather-summary" role="status"></p><div class="table-wrap"><table><caption>Exact probabilities from the initial state; one seeded sample path alongside them</caption><thead><tr><th>Step</th><th>P(DRY)</th><th>P(WET)</th><th>Sample</th><th>Sample DRY fraction so far</th><th>Truncated?</th></tr></thead><tbody id="weather-table"></tbody></table></div><p id="foresight-summary"></p>''',
  'investigate': 'Take two steps starting DRY. Reset with the same seed to reproduce the sampled path, then change seeds or run to a longer cap. Compare a finite sample frequency with the exact marginal distribution. The chain is continuing: the cap is truncation, not weather termination.',
  'theory': '''<p>A Markov chain has transition matrix P with a normalized row per current state. A row distribution evolves as <code>d_(t+1)=d_t P</code>. From DRY after two steps, DRY probability is <code>0.8×0.8 + 0.2×0.3 = 0.70</code>. The stationary distribution here is [0.6,0.4]; it satisfies dP=d. A short sampled path need not match exact marginals or long-run proportions.</p><p>For a separate one-step prediction task, choose NONE (predict DRY) or UMBRELLA (predict WET) before the next weather is drawn. Reward is 1 for a match, otherwise 0, and that task terminates. The attainable expected best score from DRY is 0.8, from WET 0.7. A future-knowing chooser scores 1; knowing the transition model does not provide that information. This is the difference between an expected optimum and a perfect-foresight bound.</p>''',
  'task': 'Implement advance(distribution, matrix), sample_next(state, rng, matrix), and decision_values(state, matrix). The RNG supplies random() in [0,1). Validate all probability rows and shapes. decision_values returns expected scores for NONE and UMBRELLA. Check distribution arithmetic and categorical samples using the supplied seeded checks.',
  'hints': ['Two paths end DRY after two steps: DRY→DRY→DRY and DRY→WET→DRY.', 'Sampling needs a random draw and cumulative probability intervals. It must not always choose argmax.', 'For a row distribution, sum distribution[i] * matrix[i][j] into column j. Prediction action scores equal the current transition row; foresight uses information unavailable before the draw.'],
  'solution': 'Two-step DRY probability is 0.64+0.06=0.70. [0.6,0.4] is stationary because its next DRY probability is 0.48+0.12=0.60. A cumulative categorical sampler reproduces a seeded trace and approximates row probabilities over many independent draws. The prediction values from DRY are {NONE:0.8, UMBRELLA:0.2}; the foresight score 1 is unattainable in expectation before observing the next weather.',
  'reflect': 'Explain row versus column multiplication, why samples vary, and why perfect foresight is only a bound. Describe how you would keep an evaluation oracle from observing randomness unavailable to your agent.',
 },
}


def page(lab, content=None, experiment_module='foundations.js', milestone='m2'):
    c = CONTENT[lab['id']] if content is None else content
    key = lab['id']
    reading = next(p['readingDirectory'] for p in load_registry()['phases'] if p['id'] == lab['phase'])
    radios = ''.join(f'<label class="choice"><input type="radio" name="prediction" value="option-{i}" data-feedback="Prediction recorded. Compare the relevant rows and explain which evidence supports or contradicts it.">{escape(text)}</label>' for i, text in enumerate(c['choices']))
    hints = ''.join(f'<p data-hint hidden><strong>Hint {i+1}:</strong> {escape(text)}</p>' for i, text in enumerate(c['hints']))
    refs = ' · '.join(f'<a href="../../{escape(ref)}">{escape(title_for(SITE / ref))}</a>' for ref in lab['references'])
    deps = ' · '.join(f'<a href="../index.html#{p}">{p}</a>' for p in lab['prerequisites'])
    source = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{escape(lab['objective'])}"><title>{escape(lab['title'])} — RL Labs</title>
<link rel="stylesheet" href="../../assets/style.css"><link rel="stylesheet" href="../assets/labs.css?v={milestone}">
<script type="module" src="../assets/lab-shell.js"></script><script type="module" src="../assets/experiments/{experiment_module}"></script></head>
<body data-lab-id="{key}"><a class="skip-link" href="#main">Skip to lab</a><div class="shell">
<nav class="sidebar" aria-label="Lab navigation"><a class="brand" href="../index.html"><span class="kicker">RL Labs · Phase {lab['phase']}</span><span class="title">{escape(lab['title'])}</span></a>
<ul class="nav-list"><li><a href="../index.html">← Curriculum</a></li><li><a href="#challenge">1 · Predict</a></li><li><a href="#experiment">2 · Investigate</a></li><li><a href="#theory">3 · Understand</a></li><li><a href="#implement">4 · Implement</a></li><li><a href="#reflect">5 · Explain</a></li></ul><div class="sidebar-foot">About {lab['minutes']} minutes.<br>{c.get('dependencyLabel', 'Python standard library only.')}</div></nav>
<main id="main"><div class="doc"><p class="eyebrow">{key} · {'Debugging lab' if lab['mode']=='debug' else 'Guided build'}</p><h1>{c['question']}</h1><p class="dek">{escape(lab['objective'])}</p>
<div class="catalog-summary"><span>Live browser calculation</span><span>Local Python practice</span><span id="lab-progress" role="status">Not started</span></div><p>Before this lab: {deps}.</p>
<noscript><p>JavaScript enables the experiment and saved progress. Reading and Python downloads remain available.</p></noscript>
<section id="challenge" class="phase-section"><h2>1. Make a prediction</h2><p>{c['challenge']}</p><div id="learning-controls" hidden><form id="prediction-form" class="lab-panel"><fieldset><legend>Which result do you expect?</legend>{radios}</fieldset><button type="submit">Record my prediction</button><p id="prediction-feedback" role="status" aria-live="polite"></p></form></div></section>
<section id="experiment" class="phase-section"><h2>2. Investigate the evidence</h2><p class="experiment-label">{c.get('experimentLabel', 'Calculated live in JavaScript · no training run or Python execution in this page')}</p><div id="experiment-controls" class="lab-panel" hidden>{c['experiment']}<button id="reset-experiment">Reset experiment</button><p id="experiment-error" role="alert"></p></div><p>{c['investigate']}</p></section>
<section id="theory" class="phase-section"><h2>3. Connect the evidence to the concept</h2>{c['theory']}<p>Read alongside: {refs}.</p></section>
<section id="implement" class="phase-section"><h2>4. Implement locally</h2><p><a class="start-lab" href="../downloads/{key}.zip" download>Download the Python exercise pack</a></p><p>{c.get('pythonLabel', 'Python 3.10+, standard library only.')} Extract the pack and open a terminal inside <code>{key}</code>. {c['task']}</p>
{c.get('setup', '')}<pre><code>python broken.py
python checks.py --candidate broken.py
python starter.py
python checks.py --candidate starter.py</code></pre>{c.get('localExtra', '')}<p>The broken candidate runs but fails checks; the untouched starter reports “Exercise incomplete.” Fix a copy of broken.py or complete the TODOs in starter.py. <a href="../downloads/{key}/README.md">Pack README and function contracts</a>. Checks compare observable behaviour and fixed examples, not your code’s text.</p>
<div id="help-controls" class="lab-panel" hidden><h3>Help, when you want it</h3><button id="next-hint">Request hint 1 of 3</button>{hints}<button id="reveal-solution" aria-controls="solution" aria-expanded="false">Request explained solution</button></div>
<div id="solution" class="lab-panel" hidden><h3>Explained solution</h3><p>{c['solution']}</p><p><a href="../downloads/{key}/solution.py" download>Download reference solution.py</a>. Try another parameter or test case before considering the concept learned.</p></div><noscript><details><summary>Request reference solution</summary><a href="../downloads/{key}/solution.py" download>Download solution.py</a></details></noscript></section>
<section id="reflect" class="phase-section"><h2>5. Explain and transfer</h2><p>{c['reflect']}</p><div id="reflection-controls" class="lab-panel" hidden><label for="explanation">Your explanation<textarea id="explanation" rows="5" maxlength="6000"></textarea></label><label class="choice"><input id="verified" type="checkbox">My local implementation passes checks.py and I compared its results with the browser.</label><button id="complete-lab">Mark lab complete</button><p id="completion-feedback" role="status" aria-live="polite"></p></div></section>
<section id="progress-tools" class="phase-section" hidden><h2>Your progress</h2><p id="saved-status" role="status"></p><div class="button-row"><button id="export-progress">Export progress</button><label class="file-input" for="import-progress">Import progress (replaces saved progress)<input id="import-progress" type="file" accept=".json,application/json"></label></div><details><summary>Reset this lab’s learning progress</summary><p>Clears this lab only. Experiment Reset keeps your prediction, explanation, and requested help.</p><button id="reset-progress">Clear this lab’s progress</button></details></section>
<p class="catalog-footer"><a href="../index.html#phase-{lab['phase']}">Back to curriculum</a> · <a href="../../{reading}/index.html">Phase {lab['phase']} reading</a></p></div></main></div></body></html>
'''


    from build_navigation import integrate_navigation
    return integrate_navigation(LABS / lab['route'], source)


def outputs():
    return {LABS / lab['route']: page(lab) for lab in load_registry()['labs'] if lab['id'] in CONTENT}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    for path, content in outputs().items():
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        elif not path.exists() or path.read_text(encoding='utf-8') != content:
            raise SystemExit(f'Stale lesson: {path.name}. Run build_foundation_pages.py --write.')
    print('Six M2 lesson pages ' + ('generated.' if args.write else 'are current.'))


if __name__ == '__main__':
    main()
