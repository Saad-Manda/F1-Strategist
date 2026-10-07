"""R0 curriculum artifacts only; never changes the published site or learner data."""
import argparse
from collections import Counter
import hashlib
from html import unescape
import json
import re

from paths import ROOT, SITE

DEST = ROOT / 'curriculum'

# Explicit source-page dispositions. Lists mean split the source's substance across
# these purposes, not duplicate its body or carry completion to all destinations.
PAGE_TARGETS = {
    '1': [
        'p1-loop p1-return p4-explore p35-markov', 'p1-state p1-return p1-values',
        'p1-values @reward-units', 'p1-loop', '@race-dynamics @environment-contract @reward-units',
        '@environment-contract @race-dynamics @reward-units', '@environment-verification', 'glossary', 'module'],
    '3.5': [
        'p35-backward', 'p35-backward +value-iteration', 'p35-stochastic @oracle-model',
        'p35-markov @oracle-bound', 'p35-backward p35-stochastic',
        '@oracle-model @oracle-bound @oracle-verification', '@oracle-verification', 'glossary', 'module'],
    '4': [
        'p4-td', 'p4-td', 'p4-explore', 'p4-sarsa', 'p4-bins', 'p4-bins @tabular-contract',
        'p4-sarsa', '@tabular-contract @tabular-training', '@tabular-training', 'glossary', 'module'],
    '5': [
        'p5-network', 'p5-network +adam-moments', 'p5-stability', 'p5-stability',
        'p5-double-dueling', 'p5-double-dueling', 'p5-per', '@dqn-reward-scale',
        'p5-network p5-stability p5-double-dueling p5-per', '@dqn-integration @dqn-reward-scale',
        '@dqn-evidence', 'glossary', 'module'],
    '6': [
        'p6-credit @multi-car-dynamics', 'p6-credit', 'p6-shaping', '@multi-car-dynamics',
        'p6-opponent @multi-car-dynamics', '@multi-car-bugs', 'p6-opponent',
        'p6-opponent p6-shaping @multi-car-checks', '@multi-car-dynamics @multi-car-checks',
        '@multi-car-checks', 'glossary', 'module'],
    '8': [
        'p6-opponent p8-game', 'p8-game', 'p8-pool', 'p8-audit', 'p8-pool @self-play-mechanics',
        '@self-play-mechanics', 'p8-audit @self-play-evidence',
        'p8-game p8-pool p8-audit @self-play-mechanics', '@self-play-integration',
        '@self-play-evidence', 'glossary', 'module'],
    '9': [
        'p9-probability p9-reinforce', 'p9-advantage', 'p9-gae', 'p9-ppo', '@library-choice',
        '@vector-library', '@workers', '@fair-budget', 'p9-reinforce p9-advantage p9-ppo @workers',
        '@ppo-integration @vector-library @workers', '@ppo-integration', 'glossary', 'module'],
}

# Reviewed cross-document moves that would be missed by retaining page boundaries.
SECTION_TARGETS = [
    ('1', 'The agent–environment loop', 'p1-loop/agent-environment-loop @environment-contract'),
    ('1', 'The reward hypothesis', 'p1-return/reward-return @reward-units'),
    ('1', 'Episodes, and episodic vs. continuing tasks', 'p1-loop/episode-endings p1-return/horizons'),
    ('1', 'Exploration vs. exploitation', 'p4-explore/greedy-discovery @tabular-training'),
    ('1', 'Why stochasticity is sampled fresh, not replayed', 'p35-markov/sampling-not-foresight @race-dynamics'),
    ('1', 'The formal tuple', 'p1-state/mdp-model'),
    ('1', 'The Markov property', 'p1-state/markov-property'),
    ('1', 'Policies', 'p1-values/policies-legal-actions'),
    ('1', 'Return and the discount factor', 'p1-return/discounting'),
    ('1', 'Action masking', 'p1-values/policies-legal-actions @environment-contract'),
    ('1', 'Worked example: one lap, two possible actions', '@race-dynamics @reward-units'),
    ('1', 'Why this matters for reward scale', '@reward-units @dqn-reward-scale'),
    ('1', 'The centring proof, worked with numbers', 'p1-return/return-calculation @reward-units'),
    ('3.5', 'Where the probabilities come from: a hazard-rate model', 'p35-stochastic/weighted-backups @oracle-model'),
    ('3.5', 'Why compute_lap_time(noise=0) is exact, not approximate', '@oracle-model'),
    ('5', 'Adam, named but not derived', 'p5-network/optimizer-update +adam-moments'),
    ('5', 'Tensor bridge: implement one update', 'p5-network/vectors-shapes p5-network/optimizer-update'),
    ('8', 'Selected-agent cleanup', 'p8-audit/agent-lifecycle'),
    ('9', 'Action-independent baselines preserve the expected score gradient', 'p9-advantage/baseline-proof'),
    ('9', 'Clipping limits an incentive, not the actual probability ratio', 'p9-ppo/surrogate-limits'),
    ('1', 'State-value function, V', 'p1-values/state-action-values'),
    ('1', 'Action-value function, Q', 'p1-values/state-action-values'),
    ('1', 'The Bellman equations', 'p1-values/bellman-backup p1-values/evaluation-optimality'),
    ('1', 'Deriving it, step by step', 'p1-values/bellman-backup'),
    ('1', "Why γ = 1 doesn't break the Bellman equation here", 'p1-return/horizons p1-values/bellman-backup'),
    ('1', 'The Env class and its two core methods', 'p1-loop/one-step p1-loop/episode-endings'),
    ('1', 'Spaces: describing what observations and actions look like', 'p1-loop/spaces-and-contract'),
    ('1', 'A standard example: GridWorld, built piece by piece', 'p1-loop/spaces-and-contract'),
    ('1', 'check_env: validating the contract', 'p1-loop/spaces-and-contract'),
    ('1', 'Action masking in Gymnasium', '@environment-contract'),
    ('1', 'render_mode and rendering', 'p1-loop/spaces-and-contract'),
    ('3.5', 'Two ways to solve an MDP', 'p35-backward/planning-learning'),
    ('3.5', 'Why "exact" is possible here at all', 'p35-backward/finite-model'),
    ('3.5', "What planning buys that learning can't", 'p35-backward/verify-solver'),
    ('3.5', 'Starting from a Bellman equation you already have', 'p35-backward/backward-induction'),
    ('3.5', 'The horizon breaks the circularity', 'p35-backward/finite-model p35-backward/backward-induction'),
    ('3.5', 'Worked example: when does pitting actually pay off?', 'p35-backward/backward-induction'),
    ('3.5', 'Why a one-step-ahead ("greedy") policy would have missed this', 'p35-backward/backward-induction'),
    ('3.5', 'Backward induction vs. value iteration — a note for the resource map', '+value-iteration'),
    ('3.5', "What changes when the next state isn't certain", 'p35-stochastic/weighted-backups'),
    ('3.5', "Worked example: how much does the risk of a safety car change today's decision?", 'p35-stochastic/rare-outcomes'),
    ('3.5', 'The pit-under-safety-car discount, and why it belongs in the transition, not the reward', 'p35-stochastic/weighted-backups @oracle-model'),
    ('3.5', 'The transition matrix', 'p35-markov/transition-matrix'),
    ('3.5', 'Fitting a chain from data: count, then normalize', 'p35-markov/transition-matrix'),
    ('3.5', 'Worked example: fitting a 3×3 matrix from three toy races', 'p35-markov/transition-matrix'),
    ('3.5', 'Sampling a trace from a fitted chain', 'p35-markov/sampling-not-foresight'),
    ('3.5', 'Why this is what makes Oracle B "achievable" and Oracle A only a "bound"', '@oracle-bound'),
    ('4', "The equation hasn't changed", 'p4-td/sampled-learning'),
    ('4', 'The temporal-difference idea', 'p4-td/td-error'),
    ('4', 'TD error, defined once, used by every algorithm in this set', 'p4-td/td-error'),
    ('4', 'Bootstrapping: learning from a guess about a guess', 'p4-td/sampled-learning'),
    ('4', 'The full update', 'p4-td/q-learning'),
    ('4', 'Why max_a\': this is what "off-policy" means', 'p4-td/q-learning p4-sarsa/policy-targets'),
    ('4', 'Learning rate and discount, in their learning-specific role', 'p4-td/q-learning'),
    ('4', 'Worked example: a 3-state toy, hand-run for four steps', 'p4-td/q-learning'),
    ('4', 'Convergence, stated but not proven', 'p4-td/q-learning'),
    ('4', 'Why greedy-only fails', 'p4-explore/greedy-discovery'),
    ('4', 'ε-greedy, defined', 'p4-explore/epsilon-probabilities'),
    ('4', "Linear decay, worked with the real plan's numbers", 'p4-explore/exploration-schedules'),
    ('4', 'Why masking has to apply inside exploration, not just at evaluation time', 'p4-explore/exploration-schedules'),
    ('4', "SARSA's update", 'p4-sarsa/sampled-sarsa'),
    ('4', 'On-policy, defined precisely', 'p4-sarsa/policy-targets'),
    ('4', 'Worked example: a risky push vs. a safe pit, hand-run side by side', 'p4-sarsa/sampled-sarsa p4-sarsa/algorithm-comparison'),
    ('4', 'Why tabular methods need a finite table', 'p4-bins/table-representation'),
    ('4', 'The tradeoff, stated generally', 'p4-bins/state-aliasing'),
    ('4', 'Worked arithmetic: how many states does a binning scheme actually produce?', 'p4-bins/table-representation'),
    ('4', 'The concrete numbers', 'p4-bins/state-aliasing @tabular-contract'),
    ('5', 'A layer as a function', 'p5-network/vectors-shapes p5-network/forward-loss'),
    ('5', 'Worked forward pass on a tiny network', 'p5-network/forward-loss'),
    ('5', 'Loss: how wrong is the prediction, as one number', 'p5-network/forward-loss @dqn-reward-scale'),
    ('5', 'Backpropagation, at the level this project needs', 'p5-network/gradients'),
    ('5', 'Gradient descent: the same nudge, computed automatically', 'p5-network/optimizer-update'),
    ('5', 'The naive idea', 'p5-stability/moving-targets'),
    ('5', "Why that's unstable", 'p5-stability/moving-targets'),
    ('5', 'The fix: a second, frozen-ish copy', 'p5-stability/target-detachment'),
    ('5', 'Keeping θ⁻ from going stale forever', 'p5-stability/target-detachment'),
    ('5', 'Worked arithmetic: how slow is "slowly"?', 'p5-stability/target-detachment'),
    ('5', 'Snapshot storage and detachment are separate', 'p5-stability/target-detachment'),
    ('5', 'A minimal replay buffer', 'p5-stability/replay'),
    ('5', 'Value/advantage decomposition', 'p5-double-dueling/dueling-values'),
    ('5', 'The identifiability problem', 'p5-double-dueling/dueling-centering'),
    ('5', "The fix: pin the advantage stream's mean to zero", 'p5-double-dueling/dueling-centering'),
    ('5', 'Architecture: two heads on a shared trunk', 'p5-double-dueling/dueling-values @dqn-integration'),
    ('6', 'The credit-assignment problem', 'p6-credit/credit-examples'),
    ('6', 'Dense proxies, and their own failure mode', 'p6-credit/credit-examples'),
    ('6', 'Ad-hoc shaping can change the answer', 'p6-shaping/base-bonuses'),
    ('6', 'The theorem', 'p6-shaping/shaping-conditions'),
    ('6', 'Why, without the full proof', 'p6-shaping/telescoping'),
    ('6', 'One hand-worked example', 'p6-shaping/potential-differences'),
    ('6', 'The assumption everything through Phase 5 relies on', 'p6-opponent/opponent-transitions'),
    ('6', 'How multiple learning agents break it', 'p6-opponent/missing-changing'),
    ('6', "Why Phase 6's fixed-script rivals sidestep this cleanly", 'p6-opponent/opponent-evaluation'),
    ('8', 'Nash equilibrium', 'p8-game/mixed-equilibrium'),
    ('8', 'Best responses and empirical opponent mixtures', 'p8-game/best-response p8-game/robustness'),
    ('8', 'The full rock-paper-scissors witness', 'p8-game/payoff-matrices'),
    ('8', "Why \"average the strategies\" needs a stand-in for a DQN", 'p8-pool/independent-snapshots p8-game/robustness'),
    ('8', "The real plan's sampling rule", 'p8-pool/pool-sampling'),
    ('8', 'AEC — Agent Environment Cycle', 'p8-audit/agent-lifecycle'),
    ('8', 'Parallel', 'p8-audit/agent-lifecycle'),
    ('8', 'Why Parallel is convenient for joint decisions', 'p8-audit/agent-lifecycle'),
    ('8', 'The shared API surface both build on', 'p8-audit/agent-lifecycle'),
    ('8', 'A concrete null baseline: shuffle the pairing', 'p8-audit/fair-pairings'),
    ('9', 'A different objective', 'p9-reinforce/gradient-intuition'),
    ('9', 'The policy gradient theorem', 'p9-reinforce/score-function'),
    ('9', 'REINFORCE', 'p9-reinforce/sampled-update'),
    ('9', 'A hand-worked example: the softmax gradient', 'p9-probability/score-gradient p9-reinforce/reinforce-example'),
    ('9', 'The natural baseline: the state-value function', 'p9-advantage/value-baselines'),
    ('9', 'The advantage function', 'p9-advantage/actor-critic'),
    ('9', 'A hand-worked comparison: advantage vs. raw return', 'p9-advantage/value-baselines'),
    ('9', 'Two extremes, already familiar', 'p9-gae/td-residuals'),
    ('9', 'GAE-λ: the interpolation', 'p9-gae/lambda-sum'),
    ('9', 'The probability ratio', 'p9-ppo/likelihood-ratios'),
    ('9', "The surrogate objective, and why it's dangerous unclipped", 'p9-ppo/old-current p9-ppo/clipping-branches'),
    ('9', 'The clip', 'p9-ppo/clipping-branches'),
]

CORRECTIONS = {
    ('1', 'The reward hypothesis'): 'State a modeling hypothesis and scalar-objective limitations rather than an established equivalence for every possible goal.',
    ('1', 'Why stochasticity is sampled fresh, not replayed'): 'Retain fresh-sampling and memorization warnings; distinguish environment overfitting from reward hacking.',
    ('1', 'The centring proof, worked with numbers'): 'Retain the numerical proof and explicitly state fixed-horizon assumptions and variable-length counterexamples.',
    ('5', "The fix: pin the advantage stream's mean to zero"): 'Retain the numbers and identifiability proof but replace the mid-example correction with one coherent mean-centered calculation.',
}


def plain(value):
    separated = re.sub(r'</(?:p|li|dt|dd|tr|td|th|div|section|pre|h[1-6])>|<br\s*/?>', ' ', value)
    return ' '.join(unescape(re.sub(r'<[^>]+>', '', separated)).split())


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def outline(course, labs):
    modules, lessons, readings = [], [], []
    old_modules = {m['id']: m for m in course['modules']}
    lab_map = {l['id']: l for l in labs['labs']}
    module = lesson = None
    for raw in (DEST / 'sequence.txt').read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('['):
            key = line[1:-1]
            old = old_modules[key]
            module = dict(id=key, title=old['title'], phase=old['phase'], lessons=[], applications=[])
            modules.append(module)
            continue
        key, title, goal = [s.strip() for s in line.split('|')]
        if key.startswith('@'):
            slug = key[1:]
            record = dict(id=f"{module['id']}/{slug}", title=title, role='application',
                          module=module['id'], lesson=None, route=f"applications/{module['id']}/{slug}.html",
                          goal=goal, minutes=8)
            module['applications'].append(record['id'])
        elif re.fullmatch(r'p\d+[a-z]*-[a-z-]+', key):
            lesson = dict(id=key, title=title, module=module['id'], prerequisites=goal.split(), readings=[], practice=None)
            if key in lab_map:
                lab = lab_map[key]
                lesson['practice'] = dict(labId=key, route='labs/' + lab['route'])
            lessons.append(lesson)
            module['lessons'].append(key)
            continue
        else:
            role = 'further-depth' if key.startswith('+') else 'core'
            slug = key.lstrip('+')
            record = dict(id=f"{lesson['id']}/{slug}", title=title, role=role, module=module['id'],
                          lesson=lesson['id'], route=f"readings/{lesson['id']}/{slug}.html", goal=goal, minutes=6)
            lesson['readings'].append(record['id'])
        record['source'] = f"content/{record['route']}"
        readings.append(record)
    by_id = {r['id']: r for r in readings}
    lesson_map = {l['id']: l for l in lessons}
    for lesson in lessons:
        previous = [next(r for r in reversed(lesson_map[p]['readings']) if by_id[r]['role'] == 'core')
                    for p in lesson['prerequisites']]
        for key in lesson['readings']:
            record = by_id[key]
            record['requires'] = list(previous)
            record['teaches'] = [key]
            if record['role'] == 'core':
                previous = [key]
    for module in modules:
        previous = [next(r for r in reversed(lesson_map[p]['readings']) if by_id[r]['role'] == 'core')
                    for p in module['lessons']]
        for key in module['applications']:
            by_id[key]['requires'] = list(previous)
            by_id[key]['teaches'] = [key]
            previous = [key]
    # Project comparisons use prior application concepts; the PPO algorithm itself
    # still has no DQN-extension or self-play prerequisite.
    by_id['policy-gradients/fair-budget']['requires'].extend(
        ['tabular-learning/tabular-training', 'neural-value-learning/dqn-evidence'])
    by_id['policy-gradients/ppo-integration']['requires'].append('planning/oracle-bound')
    return dict(artifactVersion=1, milestone='R0', runtimeSchema=False, modules=modules,
                lessons=lessons, readings=readings, projectStages=course['projectStages'])


def resolve(tokens, curriculum, module_id):
    result = []
    for token in tokens.split():
        if token == 'module':
            result.append(f'module:{module_id}')
        elif token == 'glossary':
            result.append(f'glossary:{module_id}')
        else:
            candidates = [r['id'] for r in curriculum['readings'] if
                          (token.startswith('@') and r['role'] == 'application' and r['id'].endswith('/' + token[1:])) or
                          (token.startswith('+') and r['role'] == 'further-depth' and r['id'].endswith('/' + token[1:])) or
                          r['id'] == token or r['lesson'] == token]
            if not candidates:
                raise ValueError(f'Unknown coverage destination: {token}')
            result.extend(candidates)
    return list(dict.fromkeys(result))


def inventory(course, curriculum):
    records = []
    modules = {m['phase']: m['id'] for m in curriculum['modules']}
    for resource in course['resources']:
        if resource['kind'] != 'page':
            continue
        route = resource['route']
        source = (SITE / route).read_text(encoding='utf-8')
        # Strip shared course UI, then retain the educational document from h1.
        source = re.sub(r'<!-- Course attachment.*?<!-- /Course attachment -->', '', source, flags=re.S)
        start = source.index('<h1')
        source = source[start:]
        # Old per-document navigation is migration input, not educational substance.
        source = re.split(r'<(?:div|nav)\b[^>]*class="[^"]*(?:page-nav|pagenav|nav-links|pager)', source, maxsplit=1)[0]
        phase = resource['phase']
        module_id = modules[phase]
        basename = route.rsplit('/', 1)[-1]
        index = -1 if basename == 'index.html' else int(basename[:2]) - 1
        default = PAGE_TARGETS[phase][index]
        boundaries = list(re.finditer(r'<h([12])\b[^>]*>(.*?)</h\1>', source, re.S))
        for number, match in enumerate(boundaries):
            end = boundaries[number + 1].start() if number + 1 < len(boundaries) else len(source)
            fragment = source[match.start():end]
            heading = plain(match[2])
            targets = next((target for p, h, target in SECTION_TARGETS if p == phase and h == heading), default)
            identity = f'{route}::section-{number + 1}'
            blocks = []
            for b in re.finditer(r'<(pre|p|table|dl|ul|ol)\b[^>]*>.*?</\1>|<div\b[^>]*class="[^"]*(?:math|equation)[^"]*"[^>]*>.*?</div>', fragment, re.S):
                html = b[0]
                tag = b[1] or 'equation'
                blocks.append(dict(kind={'pre': 'code', 'table': 'table', 'dl': 'glossary',
                                         'ul': 'list', 'ol': 'list'}.get(tag, tag), text=plain(html), sourceHtml=html))
            records.append(dict(id=identity, route=route, heading=heading,
                                legacyResourceIds=[r['id'] for r in course['resources'] if r['route'] == route and
                                                   (r['kind'] == 'page' or r.get('heading') == heading)],
                                sourceHtml=fragment, text=plain(fragment), sha256=digest(fragment),
                                subheadings=[plain(h) for h in re.findall(r'<h[3-6]\b[^>]*>(.*?)</h[3-6]>', fragment, re.S)],
                                glossaryTerms=[plain(h) for h in re.findall(r'<dt\b[^>]*>(.*?)</dt>', fragment, re.S)],
                                blocks=blocks, destinations=resolve(targets, curriculum, module_id),
                                disposition='replace-index' if basename == 'index.html' else
                                'retain-and-correct' if (phase, heading) in CORRECTIONS else 'retain-and-rewrite',
                                rationale=CORRECTIONS[(phase, heading)] if (phase, heading) in CORRECTIONS else
                                'Consolidate glossary definitions into the new glossary and recap links.' if default == 'glossary' else
                                'Replace source-order navigation with a module overview; retain its motivation and project handoff.' if basename == 'index.html' else
                                'Retain examples, equations, code and cautions in the named teaching purposes; separate general theory from project details.'))
    return dict(artifactVersion=1, sections=records)


def validate(curriculum, coverage, labs):
    readings = curriculum['readings']
    ids = {r['id'] for r in readings}
    if len(ids) != len(readings) or len({r['route'] for r in readings}) != len(readings):
        raise ValueError('Duplicate reading ID or route')
    practice = [l['practice']['labId'] for l in curriculum['lessons'] if l['practice']]
    if Counter(practice) != Counter(l['id'] for l in labs['labs']):
        raise ValueError('Every existing lab needs exactly one practice destination')
    taught = set()
    for reading in readings:
        if not set(reading['requires']) <= taught:
            raise ValueError(f"Unmet concepts before {reading['id']}: {set(reading['requires']) - taught}")
        if reading['role'] != 'further-depth':
            taught.update(reading['teaches'])
        if not reading['goal'] or not reading['source']:
            raise ValueError('Missing teaching purpose or source')
    for section in coverage['sections']:
        if not section['destinations']:
            raise ValueError(f"Unmapped source section: {section['id']}")
        if any(d not in ids and not d.startswith(('module:', 'glossary:')) for d in section['destinations']):
            raise ValueError('Unknown coverage target')


def outputs():
    if load(SITE / 'assets/course-registry.json').get('schemaVersion') == 2:
        curriculum=load(DEST/'outline.json');coverage=load(DEST/'coverage-map.json')
        snapshot=load(DEST/'legacy-v1-identities.json')
        validate(curriculum,coverage,snapshot['labs'])
        for section in coverage['sections']:
            if digest(section['sourceHtml']) != section['sha256']:
                raise ValueError('Frozen source section hash changed: '+section['id'])
        return {DEST/name:(DEST/name).read_text(encoding='utf-8') for name in
                ('outline.json','coverage-map.json','legacy-v1-identities.json','legacy-routes.json','OUTLINE.md')}
    course = load(SITE / 'assets/course-registry.json')
    labs = load(SITE / 'labs/assets/lab-registry.json')
    curriculum = outline(course, labs)
    coverage = inventory(course, curriculum)
    validate(curriculum, coverage, labs)
    routes = []
    # R0 is a frozen pre-removal baseline. Later authored routes are not legacy.
    frozen_routes = DEST / 'legacy-routes.json'
    paths = [SITE / item['route'] for item in load(frozen_routes)] if frozen_routes.exists() else sorted(SITE.rglob('*.html'))
    for path in paths:
        route = path.relative_to(SITE).as_posix()
        resources = [r['id'] for r in course['resources'] if r['route'] == route]
        routes.append(dict(route=route, resourceIds=resources,
                           disposition='relocate-after-coverage-verification' if resources else 'retain-or-rebuild-navigation',
                           sha256=digest(path.read_text(encoding='utf-8'))))
    snapshot = dict(artifactVersion=1, course=course, labs=labs,
                    storage=dict(courseKey='rl-course:v1', labKey='rl-labs:v1', courseVersion=1, labVersion=1,
                                 combinedFormat='rl-course-progress', combinedVersion=1,
                                 courseFields=['version', 'readings', 'browser', 'checks', 'resume'],
                                 labFields=['attempts', 'prediction', 'explanation', 'status', 'hints', 'solution', 'verified'],
                                 resumeKinds=['lesson', 'checkpoint'], lessonSteps=['theory', 'browser', 'python']),
                    runtimeHashes={p: digest((SITE / p).read_text(encoding='utf-8')) for p in
                                   ['assets/course-progress.js', 'assets/course-context.js', 'labs/assets/storage.js']},
                    readingEquivalenceApproved=False)
    artifacts = {'outline.json': curriculum, 'coverage-map.json': coverage,
                 'legacy-v1-identities.json': snapshot, 'legacy-routes.json': routes}
    result = {DEST / name: json.dumps(data, ensure_ascii=False, indent=2) + '\n' for name, data in artifacts.items()}
    report = ['# R0 teaching sequence', '',
              'Generated from `sequence.txt`. These are planned purposes, not published reading bodies.', '',
              'Reading IDs name concept clusters. `requires`/`teaches` in `outline.json` form the reading-level prerequisite graph.',
              'Core readings never depend on further-depth pages. Practice follows the final core reading.', '']
    by_id = {r['id']: r for r in curriculum['readings']}
    lessons = {l['id']: l for l in curriculum['lessons']}
    for number, module in enumerate(curriculum['modules'], 1):
        report.extend([f"## {number} · {module['title']} (project phase {module['phase']})", ''])
        for position, lesson_id in enumerate(module['lessons'], 1):
            lesson = lessons[lesson_id]
            report.extend([f"### {number}.{position} · {lesson['title']} (`{lesson_id}`)", '',
                           'Prerequisite lessons: ' + (', '.join(lesson['prerequisites']) or 'basic Python only') + '.', '',
                           'Practice: ' + (f"`{lesson['practice']['labId']}` → `{lesson['practice']['route']}`; existing Python pack follows."
                                          if lesson['practice'] else 'Theory only; continue to the next lesson without a browser/Python requirement.'), ''])
            for key in lesson['readings']:
                reading = by_id[key]
                report.extend([f"- **{reading['title']}** ({reading['role']}, about {reading['minutes']} minutes) · `{reading['route']}`",
                               f"  {reading['goal']}"])
            report.append('')
        report.extend(['### Module application and project preparation', ''])
        for key in module['applications']:
            reading = by_id[key]
            report.extend([f"- **{reading['title']}** (application, about {reading['minutes']} minutes) · `{reading['route']}`",
                           f"  {reading['goal']}"])
        report.append('')
    report.extend(['## Coverage and identity baseline', '',
                   f"Inventoried {len(course['resources'])} legacy resource identities, "
                   f"{sum(r['kind'] == 'page' for r in course['resources'])} source pages including phase indexes, "
                   f"{len(coverage['sections'])} sections and {len(routes)} HTML routes.", '',
                   f"The outline has {len(curriculum['lessons'])} teaching lessons, {len(curriculum['readings'])} planned pages "
                   f"and {len(labs['labs'])} uniquely mapped browser/Python practice anchors. "
                   'The glossary is a separate consolidated reference; its final entry layout is deferred to authoring.', '',
                   'See `coverage-map.json` for complete section text/HTML, subheadings, glossary terms, code/table/list blocks and dispositions. '
                   'See `legacy-v1-identities.json` and `legacy-routes.json` for pre-removal identity inputs. '
                   'No reading completion equivalence is approved by this inventory.', ''])
    result[DEST / 'OUTLINE.md'] = '\n'.join(report)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Capture the current legacy baseline and regenerate R0 artifacts')
    args = parser.parse_args()
    generated = outputs()
    stale = []
    for path, source in generated.items():
        if args.write:
            path.write_text(source, encoding='utf-8')
        elif not path.is_file() or path.read_text(encoding='utf-8') != source:
            stale.append(path.name)
    if stale:
        raise SystemExit('R0 artifacts differ from current sources: ' + ', '.join(stale))
    print('R0 coverage, concept ordering, unique routes and all practice destinations verified.')


if __name__ == '__main__':
    main()
