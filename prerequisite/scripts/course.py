"""Canonical course validation and derived navigation, independent of presentation."""
from collections import Counter
from html import unescape
import json
import re
from urllib.parse import urlencode
from paths import SITE

CATEGORIES = {'Core theory', 'Topic overview', 'Glossary', 'Project application', 'Deeper reading'}
STEPS = ('theory', 'browser', 'python')


def load_course():
    return json.loads((SITE / 'assets/course-registry.json').read_text(encoding='utf-8'))


def heading_text(source):
    return ' '.join(unescape(re.sub(r'<[^>]+>', '', source)).split())


def heading_records(source):
    return [{'level': int(match[1]), 'text': heading_text(match[3]),
             'id': (re.search(r'\bid\s*=\s*[\"\']([^\"\']+)', match[2]) or [None, None])[1]}
            for match in re.finditer(r'<h([1-6])\b([^>]*)>(.*?)</h\1>', source, re.S | re.I)]


def safe_route(route):
    return (isinstance(route, str) and bool(re.fullmatch(r'[a-z0-9][a-z0-9/._-]*\.html', route))
            and all(part not in {'', '.', '..'} for part in route.split('/')))


def validate_course(course, labs, site=SITE):
    errors = []
    if not isinstance(course, dict) or course.get('schemaVersion') != 1:
        return ['Unsupported course schema.']
    groups = {}
    for name in ('modules', 'lessons', 'resources', 'projectStages'):
        records = course.get(name)
        if not isinstance(records, list) or not records or not all(isinstance(r, dict) for r in records):
            errors.append(f'{name}: expected a nonempty list of records.')
            groups[name] = []
        else:
            groups[name] = records
    modules, lessons, resources, stages = (groups[k] for k in ('modules', 'lessons', 'resources', 'projectStages'))
    for name, records in [('module', modules), ('lesson', lessons), ('reading', resources)]:
        ids = [r.get('id') for r in records]
        if any(not isinstance(key, str) or not key for key in ids):
            errors.append(f'Invalid {name} IDs.')
        if len(ids) != len(set(key for key in ids if isinstance(key, str))):
            errors.append(f'Duplicate {name} IDs.')
    module_map = {m['id']: m for m in modules if isinstance(m.get('id'), str)}
    resource_map = {r['id']: r for r in resources if isinstance(r.get('id'), str)}
    lab_map = {l['id']: l for l in labs['labs']}
    phase_map = {p['id']: p for p in labs['phases']}
    order = {l['id']: i for i, l in enumerate(lessons) if isinstance(l.get('id'), str)}
    if set(order) != set(lab_map) or len(lessons) != len(lab_map):
        errors.append('Every delivered lab must map to exactly one lesson.')
    if Counter(m.get('phase') for m in modules) != Counter(phase_map.keys()):
        errors.append('Modules must retain all original project-phase mappings exactly once.')
    if [m.get('number') for m in modules] != list(range(1, len(modules) + 1)):
        errors.append('Module numbers must follow their display order.')
    generated_routes = [m.get('route') for m in modules] + [l.get('route') for l in lessons]
    if any(not safe_route(route) for route in generated_routes):
        errors.append('Invalid generated course route.')
    if len([x for x in generated_routes if isinstance(x, str)]) != len(set(x for x in generated_routes if isinstance(x, str))):
        errors.append('Duplicate generated course routes.')
    page_resources = [r for r in resources if r.get('kind') == 'page']
    actual_pages = {p.relative_to(site).as_posix() for phase in labs['phases']
                    for p in (site / phase['readingDirectory']).glob('*.html')}
    if Counter(r.get('route') for r in page_resources) != Counter(actual_pages):
        errors.append('Reading inventory is incomplete or contains an unknown/duplicate page.')
    sources = {}
    for resource in resources:
        key = resource.get('id', '?')
        route = resource.get('route')
        if resource.get('category') not in CATEGORIES or not resource.get('title'):
            errors.append(f'{key}: reading needs a title and valid classification.')
        if resource.get('kind') not in {'page', 'section'}:
            errors.append(f'{key}: invalid reading kind.')
        if not safe_route(route) or not (site / route).is_file():
            errors.append(f'{key}: invalid reading route.')
            continue
        phase = phase_map.get(resource.get('phase'))
        if not phase or route.split('/')[0] != phase['readingDirectory']:
            errors.append(f'{key}: reading has the wrong project phase.')
        if resource.get('kind') == 'page' and key != route:
            errors.append(f'{key}: page reading ID must equal its stable route.')
        if resource.get('kind') == 'section':
            anchor = resource.get('anchor')
            if (not isinstance(anchor, str) or not re.fullmatch(r'[a-z][a-z0-9-]*', anchor)
                    or key != f'{route}#{anchor}' or route not in resource_map):
                errors.append(f'{key}: invalid section identity.')
            source = sources.setdefault(route, (site / route).read_text(encoding='utf-8'))
            matches = [h for h in heading_records(source) if h['text'] == resource.get('heading') and h['level'] == 2]
            if len(matches) != 1 or matches[0]['id'] != anchor:
                errors.append(f'{key}: missing or ambiguous reading section anchor.')
            if not resource.get('instruction'):
                errors.append(f'{key}: section needs a reading boundary instruction.')
            if resource.get('through'):
                records = [h for h in heading_records(source) if h['level'] == 2]
                starts = [i for i, h in enumerate(records) if h['text'] == resource.get('heading')]
                ends = [i for i, h in enumerate(records) if h['text'] == resource['through']]
                if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
                    errors.append(f'{key}: invalid reading section range.')
    previous_module_index = -1
    module_order = {m.get('id'): i for i, m in enumerate(modules) if isinstance(m.get('id'), str)}
    for lesson in lessons:
        key = lesson.get('id', '?')
        module = module_map.get(lesson.get('module'))
        if not module:
            errors.append(f'{key}: unknown module.')
        else:
            index = module_order[module['id']]
            if index < previous_module_index:
                errors.append('Lessons must be grouped in module display order.')
            previous_module_index = index
        if lesson.get('route') != f'lessons/{key}.html':
            errors.append(f'{key}: unstable lesson-guide route.')
        for field in ('required', 'optional'):
            ids = lesson.get(field)
            if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
                errors.append(f'{key}: {field} must be a list of reading IDs.')
                continue
            if field == 'required' and not ids:
                errors.append(f'{key}: no explicit required theory.')
            if len(ids) != len(set(ids)):
                errors.append(f'{key}: duplicate reading assignment.')
            for resource_id in ids:
                if resource_id not in resource_map:
                    errors.append(f'{key}: unknown reading {resource_id}.')
        required = lesson.get('required', [])
        optional = lesson.get('optional', [])
        required = [x for x in required if isinstance(x, str)] if isinstance(required, list) else []
        optional = [x for x in optional if isinstance(x, str)] if isinstance(optional, list) else []
        if set(required) & set(optional):
            errors.append(f'{key}: reading cannot be both required and optional.')
        lab = lab_map.get(key)
        if lab:
            if lesson.get('lab') != f'labs/{lab["route"]}' or not (site / f'labs/{lab["route"]}').is_file():
                errors.append(f'{key}: lab route changed or missing.')
            if module and module.get('phase') != lab['phase']:
                errors.append(f'{key}: lesson belongs to the wrong project phase.')
            for dependency in lab['prerequisites']:
                if dependency not in order or order[dependency] >= order.get(key, -1):
                    errors.append(f'{key}: prerequisite order invalid: {dependency}.')
            if lesson.get('prerequisites') != lab['prerequisites']:
                errors.append(f'{key}: course prerequisites differ from the lab graph.')
    for module in modules:
        key = module.get('id', '?')
        if module.get('route') != f'modules/{key}.html':
            errors.append(f'{key}: unstable module route.')
        expected = [l['id'] for l in lessons if l.get('module') == key and 'id' in l]
        if not expected or module.get('lessons') != expected:
            errors.append(f'{key}: module lesson list does not match the default sequence.')
        checkpoint = module.get('projectCheckpoint')
        if not isinstance(checkpoint, dict):
            errors.append(f'{key}: missing project implementation checkpoint.')
            continue
        phase = phase_map.get(module.get('phase'))
        if not phase or checkpoint.get('plan') != phase['plan']:
            errors.append(f'{key}: checkpoint refers to the wrong project plan.')
        if not isinstance(checkpoint.get('checks'), list) or not checkpoint['checks']:
            errors.append(f'{key}: missing project transfer checklist.')
        else:
            checks = checkpoint['checks']
            if not all(isinstance(c, dict) and isinstance(c.get('id'), str) and c['id']
                       and isinstance(c.get('text'), str) and c['text'] for c in checks):
                errors.append(f'{key}: project transfer checks need stable IDs and labels.')
            elif len({c['id'] for c in checks}) != len(checks):
                errors.append(f'{key}: duplicate project transfer check IDs.')
        if checkpoint.get('route') != module.get('route', '') + '#project-checkpoint':
            errors.append(f'{key}: invalid project checkpoint route.')
        bridge = checkpoint.get('required', [])
        if not isinstance(bridge, list) or not bridge:
            errors.append(f'{key}: missing required project bridge readings.')
            continue
        for resource_id in bridge:
            resource = resource_map.get(resource_id)
            if not resource:
                errors.append(f'{key}: unknown project bridge reading.')
            elif resource.get('phase') != module.get('phase') or resource.get('kind') != 'page':
                errors.append(f'{key}: project bridge must use its own phase reading pages.')
    contract = course.get('navigationContract', {})
    if (contract.get('steps') != list(STEPS) or contract.get('contextParameters') != ['lesson', 'step']
            or contract.get('checkpointContextParameter') != 'module'
            or [contract.get(x) for x in ('home', 'roadmap', 'library')] != ['index.html', 'roadmap.html', 'library.html']):
        errors.append('Invalid navigation step/entry-point contract.')
    expected_stages = ['0', '0.5', '1', '2', '3', '3.5', '4', '5', '6', '7', '8', '9']
    if [s.get('phase') for s in stages] != expected_stages:
        errors.append('Project-stage order is incomplete or invalid.')
    for stage in stages:
        expected_module = next((m['id'] for m in modules if m.get('phase') == stage.get('phase')), None)
        if stage.get('module') != expected_module:
            errors.append(f'{stage.get("phase")}: project stage has the wrong learning module.')
        if not stage.get('title') or not stage.get('guidance'):
            errors.append(f'{stage.get("phase")}: project stage needs explicit handoff guidance.')
    return errors


def reading_url(resource, lesson_id=None):
    query = '?' + urlencode({'lesson': lesson_id, 'step': 'theory'}) if lesson_id else ''
    fragment = '#' + resource['anchor'] if resource.get('kind') == 'section' else ''
    return resource['route'] + query + fragment


def lesson_navigation(course, lesson_id):
    lessons = course['lessons']
    index = next(i for i, lesson in enumerate(lessons) if lesson['id'] == lesson_id)
    lesson = lessons[index]
    module = next(m for m in course['modules'] if m['id'] == lesson['module'])
    resources = {r['id']: r for r in course['resources']}
    stages = course['projectStages']
    stage_index = next(i for i, stage in enumerate(stages) if stage['phase'] == module['phase'])
    module_end = lesson['id'] == module['lessons'][-1]
    return {'lesson': lesson, 'module': module,
            'previous': lessons[index - 1] if index else None,
            'next': lessons[index + 1] if index + 1 < len(lessons) else None,
            'moduleEnd': module_end,
            'afterLesson': module['route'] + '#project-checkpoint' if module_end else lessons[index + 1]['route'],
            'nextProjectStage': stages[stage_index + 1] if stage_index + 1 < len(stages) else None,
            'checkpoint': module['route'] + '#project-checkpoint',
            'readings': [reading_url(resources[key], lesson_id) for key in lesson['required']],
            'browser': lesson['lab'] + '?' + urlencode({'lesson': lesson_id, 'step': 'browser'}) + '#challenge',
            'python': lesson['lab'] + '?' + urlencode({'lesson': lesson_id, 'step': 'python'}) + '#implement'}


def checkpoint_reading_url(resource, module_id):
    return resource['route'] + '?' + urlencode({'module': module_id})


def resolve_context(course, route, *, lesson_id=None, step=None, module_id=None):
    """Reject arbitrary return URLs and context unrelated to the visited page."""
    resources = {r['id']: r for r in course['resources']}
    if not safe_route(route):
        return None
    if module_id is not None:
        if lesson_id is not None or step is not None:
            return None
        module = next((m for m in course['modules'] if m['id'] == module_id), None)
        if module and any(resources[key]['route'] == route for key in module['projectCheckpoint']['required']):
            return {'kind': 'checkpoint', 'module': module, 'return': module['projectCheckpoint']['route']}
        return None
    lesson = next((l for l in course['lessons'] if l['id'] == lesson_id), None)
    if not lesson or step not in STEPS:
        return None
    if step == 'theory':
        allowed = any(resources[key]['route'] == route for key in lesson['required'] + lesson['optional'])
    else:
        allowed = route == lesson['lab']
    return {'kind': 'lesson', 'lesson': lesson, 'step': step, 'return': lesson['route']} if allowed else None
