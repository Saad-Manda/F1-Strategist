"""Check the N0 mapping independently of the future generated course UI."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import hashlib
import re
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_course import audit, preservation_errors
from course import lesson_navigation, reading_url, resolve_context
from build_reading_sections import integrate_sections, outputs as section_outputs


def data():
    site = ROOT / 'site'
    return (json.loads((site / 'assets/course-registry.json').read_text(encoding='utf-8')),
            json.loads((site / 'labs/assets/lab-registry.json').read_text(encoding='utf-8')))


def test_all_lessons_readings_and_project_checkpoints_are_mapped():
    course, labs = data()
    assert audit(course, labs) == []
    assert preservation_errors() == []


def test_missing_lesson_and_unclassified_reading_are_rejected():
    course, labs = data()
    course['lessons'].pop()
    course['resources'][0]['category'] = ''
    errors = audit(course, labs)
    assert any('exactly one lesson' in e for e in errors)
    assert any('classification' in e for e in errors)


def test_reversed_dependency_and_wrong_phase_are_rejected():
    course, labs = data()
    course['lessons'][0], course['lessons'][1] = course['lessons'][1], course['lessons'][0]
    course['lessons'][0]['module'] = 'policy-gradients'
    errors = audit(course, labs)
    assert any('prerequisite order' in e for e in errors)
    assert any('wrong project phase' in e for e in errors)


def test_external_reading_and_unknown_bridge_are_rejected():
    course, labs = data()
    course['resources'][0]['route'] = '../private.html'
    course['modules'][0]['projectCheckpoint']['required'].append('missing')
    errors = audit(course, labs)
    assert any('invalid reading route' in e for e in errors)
    assert any('unknown project bridge' in e for e in errors)


def test_phase_handoffs_precede_next_learning_module():
    course, _ = data()
    first = lesson_navigation(course, 'p1-loop')
    assert first['previous'] is None
    assert first['afterLesson'] == 'lessons/p1-state.html'
    end = lesson_navigation(course, 'p1-values')
    assert end['moduleEnd']
    assert end['afterLesson'] == 'modules/foundations.html#project-checkpoint'
    assert end['nextProjectStage']['phase'] == '2'
    assert end['nextProjectStage']['module'] is None
    multi = lesson_navigation(course, 'p6-opponent')
    assert multi['nextProjectStage']['phase'] == '7'
    last = lesson_navigation(course, 'p9-ppo')
    assert last['next'] is None and last['nextProjectStage'] is None
    assert last['afterLesson'] == 'modules/policy-gradients.html#project-checkpoint'


def test_shared_mdp_page_has_distinct_state_and_return_assignments():
    course, _ = data()
    by_id = {l['id']: l for l in course['lessons']}
    resources = {r['id']: r for r in course['resources']}
    state = resources[by_id['p1-state']['required'][0]]
    returns = resources[by_id['p1-return']['required'][0]]
    assert state['route'] == returns['route']
    assert state['anchor'] != returns['anchor']
    assert state['through'] == 'The Markov property'
    assert returns['heading'] == 'Return and the discount factor'
    assert reading_url(returns, 'p1-return').endswith('#' + returns['anchor'])
    assert '?lesson=p1-return&step=theory#' in reading_url(returns, 'p1-return')


def test_context_accepts_only_resources_belonging_to_the_selected_lesson_or_checkpoint():
    course, _ = data()
    route = 'phase-1-rl-prerequisites/02-markov-decision-processes.html'
    for key in ('p1-state', 'p1-return'):
        assert resolve_context(course, route, lesson_id=key, step='theory')['return'] == f'lessons/{key}.html'
    assert resolve_context(course, route, lesson_id='p9-ppo', step='theory') is None
    assert resolve_context(course, route, lesson_id='p1-state', step='browser') is None
    assert resolve_context(course, '../secret.html', lesson_id='p1-state', step='theory') is None
    assert resolve_context(course, route, lesson_id='unknown', step='theory') is None
    assert resolve_context(course, route, lesson_id='p1-state', step='unknown') is None
    bridge = 'phase-1-rl-prerequisites/07-code-walkthrough.html'
    assert resolve_context(course, bridge, module_id='foundations')['kind'] == 'checkpoint'
    assert resolve_context(course, bridge, module_id='policy-gradients') is None
    assert resolve_context(course, bridge, module_id='foundations', lesson_id='p1-state', step='theory') is None


@pytest.mark.parametrize('fault,expected', [
    ('duplicate_lesson', 'Duplicate lesson'), ('duplicate_module', 'Duplicate module'),
    ('bad_anchor', 'section anchor'), ('backward_range', 'section range'),
    ('wrong_bridge_phase', 'own phase'), ('duplicate_check', 'duplicate project transfer'),
    ('unknown_step', 'navigation step'), ('missing_project_stage', 'Project-stage order'),
    ('unsafe_route', 'Invalid generated'), ('bad_required_type', 'list of reading IDs'),
])
def test_invalid_course_contracts_are_rejected(fault, expected):
    course, labs = data()
    section = next(r for r in course['resources'] if r['kind'] == 'section')
    if fault == 'duplicate_lesson':
        course['lessons'].append(deepcopy(course['lessons'][0]))
    elif fault == 'duplicate_module':
        course['modules'].append(deepcopy(course['modules'][0]))
    elif fault == 'bad_anchor':
        section['anchor'] = 'missing-anchor'
        section['id'] = section['route'] + '#missing-anchor'
    elif fault == 'backward_range':
        returns = next(r for r in course['resources'] if r.get('heading') == 'Return and the discount factor')
        returns['through'] = 'The formal tuple'
    elif fault == 'wrong_bridge_phase':
        course['modules'][0]['projectCheckpoint']['required'].append(course['modules'][-1]['projectCheckpoint']['required'][0])
    elif fault == 'duplicate_check':
        checks = course['modules'][0]['projectCheckpoint']['checks']
        checks.append(deepcopy(checks[0]))
    elif fault == 'unknown_step':
        course['navigationContract']['steps'].append('guess')
    elif fault == 'missing_project_stage':
        course['projectStages'].pop(3)
    elif fault == 'unsafe_route':
        course['modules'][0]['route'] = '../private.html'
    elif fault == 'bad_required_type':
        course['lessons'][0]['required'] = 1
    assert any(expected in e for e in audit(course, labs))


def test_anchors_preserve_existing_reading_bytes_apart_from_attributes_and_line_endings():
    baseline = json.loads((ROOT / 'tests/reading-baseline.json').read_text(encoding='utf-8'))
    for route, expected in baseline.items():
        # N3 replaces index guidance; retained topics have separate preservation
        # checks. Undo only shell changes on the seven generated neural chapters.
        from build_neural_readings import PAGES
        if route.endswith('/index.html'):
            continue
        # N2's only reading edits are navigation IDs; undo them to compare to N0.
        source = (ROOT / 'site' / route).read_text(encoding='utf-8')
        from build_navigation import strip_navigation
        source = strip_navigation(source)
        if route.startswith('phase-5-dqn-prerequisites/') and route.split('/')[-1] in PAGES:
            nav = (ROOT / 'tests/neural-navigation-baseline.html').read_text(encoding='utf-8')
            source = re.sub(r'  <nav\b.*?</nav>', lambda _: nav, source, count=1, flags=re.S)
            source = re.sub(r'<link rel="stylesheet" href="../assets/course.css(?:\?[^\"]+)?"><script type="module" src="../assets/course-navigation.js(?:\?[^\"]+)?"></script>', '', source)
            source = source.replace('class="course-reference"', 'class="shell"').replace('Phase 5 topic reference', 'Phase 5 roadmap')
        original = re.sub(r'(<h2) id="course-[a-z0-9-]+"', r'\1', source)
        hashes = {hashlib.sha256(text.encode('utf-8')).hexdigest()
                  for text in (original, original.replace('\n', '\r\n'))}
        assert expected in hashes, route
    course, _ = data()
    for path, source in section_outputs().items():
        assert integrate_sections(path, source, course) == source
        assert path.read_text(encoding='utf-8') == source


def test_project_mapping_keeps_non_rl_stages_and_ppo_independent_of_self_play():
    course, labs = data()
    assert audit(course, labs) == []
    # Module/lesson routes are metadata during N2; only reading and lab targets
    # must exist before N3 generates the presentation pages.
    assert {m['phase'] for m in course['modules']} == {'1', '3.5', '4', '5', '6', '8', '9'}
    assert {s['phase'] for s in course['projectStages'] if s['module'] is None} == {'0', '0.5', '2', '3', '7'}
    reinforce = next(l for l in course['lessons'] if l['id'] == 'p9-reinforce')
    assert not any(key.startswith('p8-') for key in reinforce['prerequisites'])
