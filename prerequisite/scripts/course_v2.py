"""Version 2 course contract. Metadata can be checked before bodies are authored."""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from paths import ROOT

ID = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*')
READING_ID = re.compile(r'[a-z][a-z0-9-]*/[a-z][a-z0-9-]*')


def canonical_route(kind, key):
    pattern = READING_ID if kind in {'reading', 'application'} else ID
    if not isinstance(key, str) or not pattern.fullmatch(key):
        raise ValueError('Invalid semantic identity')
    prefix = {'reading': 'readings', 'application': 'applications', 'lesson': 'lessons', 'module': 'modules'}[kind]
    return f'{prefix}/{key}.html'


def load_course_v2():
    return json.loads((ROOT / 'content/course-registry.json').read_text(encoding='utf-8'))


class FragmentParser(HTMLParser):
    """Reject full legacy documents, scripts and dangling/duplicate heading anchors."""
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
    FORBIDDEN = {'html', 'head', 'body', 'main', 'nav', 'aside', 'h1', 'script', 'style', 'iframe', 'base', 'meta', 'link'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.errors, self.stack, self.ids = [], [], set()
        self.words, self.paragraphs, self.headings = [], 0, 0

    def handle_decl(self, decl):
        self.errors.append('A body fragment must not contain a doctype.')

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in self.FORBIDDEN:
            self.errors.append(f'Body fragment contains forbidden shell/active tag: {tag}.')
        if any(k.startswith('on') for k in attrs) or any(
                re.match(r'\s*(?:javascript|data):', attrs.get(k, ''), re.I) for k in ('href', 'src')):
            self.errors.append('Body fragment contains active attributes.')
        identity = attrs.get('id')
        if identity is not None:
            if not ID.fullmatch(identity) or identity in self.ids:
                self.errors.append('Invalid or duplicate fragment anchor.')
            self.ids.add(identity)
        if tag not in self.VOID:
            self.stack.append(tag)
        self.paragraphs += tag == 'p'
        self.headings += tag in {'h2', 'h3', 'h4', 'h5', 'h6'}

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f'Unbalanced fragment closing tag: {tag}.')
        else:
            self.stack.pop()

    def handle_data(self, data):
        self.words.extend(data.split())


def validate_fragment(source):
    parser = FragmentParser()
    parser.feed(source)
    parser.close()
    errors = parser.errors[:]
    if parser.stack:
        errors.append('Unclosed fragment tags.')
    if not parser.paragraphs or not parser.headings or len(parser.words) < 40:
        errors.append('Reading source needs explanatory paragraphs and headings; placeholders are not authored readings.')
    return errors


def validate_course_v2(course, labs, *, source_root=ROOT, allow_planned=False, check_sources=True):
    errors = []
    if not isinstance(course, dict) or course.get('schemaVersion') != 2:
        return ['Unsupported v2 course schema.']
    groups = {}
    for name in ('modules', 'lessons', 'readings', 'projectStages'):
        values = course.get(name)
        if not isinstance(values, list) or not values or any(not isinstance(v, dict) for v in values):
            return [f'{name}: expected nonempty records.']
        groups[name] = values
    modules, lessons, readings = (groups[n] for n in ('modules', 'lessons', 'readings'))
    maps = {}
    for name, values, pattern in [('module', modules, ID), ('lesson', lessons, ID), ('reading', readings, READING_ID)]:
        keys = [v.get('id') for v in values]
        if any(not isinstance(k, str) or not pattern.fullmatch(k) for k in keys):
            return [f'Invalid {name} identities.']
        if len(set(keys)) != len(keys):
            errors.append(f'Duplicate {name} IDs.')
        maps[name] = {v['id']: v for v in values}
    module_map, lesson_map, reading_map = (maps[n] for n in ('module', 'lesson', 'reading'))
    # Check ownership/value types before using untrusted metadata as dictionary keys.
    for module in modules:
        if any(not isinstance(module.get(k), str) for k in ('phase', 'route')):
            errors.append(f"{module['id']}: invalid module field types.")
    for lesson in lessons:
        mapping = lesson.get('practice')
        if any(not isinstance(lesson.get(k), str) for k in ('module', 'route')) or 'practice' not in lesson:
            errors.append(f"{lesson['id']}: invalid lesson field types.")
        if mapping is not None and (not isinstance(mapping, dict) or any(not isinstance(mapping.get(k), str) for k in ('labId', 'route'))):
            errors.append(f"{lesson['id']}: invalid practice field types.")
    for reading in readings:
        if (any(not isinstance(reading.get(k), str) for k in ('module', 'role', 'route', 'source', 'status'))
                or 'lesson' not in reading or (reading['lesson'] is not None and not isinstance(reading['lesson'], str))):
            errors.append(f"{reading['id']}: invalid reading ownership/field types.")
    if errors:
        return errors
    lab_map = {l['id']: l for l in labs['labs']}
    phase_ids = [p['id'] for p in labs['phases']]
    if Counter(m.get('phase') for m in modules) != Counter(phase_ids):
        errors.append('Module project-phase mappings are incomplete or duplicated.')
    routes = []
    membership, practice = [], []

    def id_list(record, field, known, *, nonempty=False):
        value = record.get(field)
        if (not isinstance(value, list) or any(not isinstance(k, str) or k not in known for k in value)
                or len(value) != len(set(k for k in value if isinstance(k, str))) or (nonempty and not value)):
            errors.append(f"{record['id']}: invalid {field} membership.")
            return []
        return value

    def route(record, kind):
        expected = canonical_route(kind, record['id'])
        if record.get('route') != expected:
            errors.append(f"{record['id']}: noncanonical route.")
        routes.append(record.get('route'))

    expected_lesson_order = []
    sequence = []
    for module in modules:
        route(module, 'module')
        if any(not isinstance(module.get(k), str) or not module[k].strip() for k in ('title', 'objective')):
            errors.append(f"{module['id']}: missing title/objective.")
        expected = [l['id'] for l in lessons if l.get('module') == module['id']]
        owned = id_list(module, 'lessons', lesson_map, nonempty=True)
        if owned != expected:
            errors.append(f"{module['id']}: malformed lesson ownership/order.")
        expected_lesson_order.extend(owned)
        for key in owned:
            lesson = lesson_map[key]
            core = id_list(lesson, 'required', reading_map, nonempty=True)
            optional = id_list(lesson, 'optional', reading_map)
            for reading_id in core + optional:
                reading = reading_map[reading_id]
                role = 'core' if reading_id in core else 'further-depth'
                if reading.get('module') != module['id'] or reading.get('lesson') != key or reading.get('role') != role:
                    errors.append(f'{reading_id}: malformed reading ownership/role.')
            membership.extend(core + optional)
            sequence.extend(core + optional)
        apps = id_list(module, 'applications', reading_map, nonempty=True)
        for key in apps:
            reading = reading_map[key]
            if reading.get('module') != module['id'] or reading.get('lesson') is not None or reading.get('role') != 'application':
                errors.append(f'{key}: malformed application ownership.')
        membership.extend(apps)
        sequence.extend(apps)
        checkpoint = module.get('projectCheckpoint')
        if not isinstance(checkpoint, dict):
            errors.append(f"{module['id']}: missing checkpoint.")
        else:
            checks = checkpoint.get('checks')
            if (not isinstance(checks, list) or not checks or any(not isinstance(c, dict) or
                    not isinstance(c.get('id'), str) or not ID.fullmatch(c['id']) or
                    not isinstance(c.get('text'), str) or not c['text'].strip() for c in checks)):
                errors.append(f"{module['id']}: invalid checkpoint checks.")
            elif len({c['id'] for c in checks}) != len(checks):
                errors.append(f"{module['id']}: duplicate checkpoint checks.")
            if checkpoint.get('route') != module['route'] + '#project-checkpoint' or checkpoint.get('required') != apps:
                errors.append(f"{module['id']}: invalid checkpoint route/application sequence.")
    if expected_lesson_order != [l['id'] for l in lessons]:
        errors.append('Lesson sequence disagrees with module membership.')
    if Counter(membership) != Counter(reading_map.keys()):
        errors.append('Each reading must belong to exactly one teaching sequence.')
    for lesson in lessons:
        route(lesson, 'lesson')
        if not isinstance(lesson.get('title'), str) or not lesson['title'].strip():
            errors.append(f"{lesson['id']}: missing title.")
        if lesson.get('module') not in module_map:
            errors.append(f"{lesson['id']}: unknown owning module.")
        prereqs = id_list(lesson, 'prerequisites', lesson_map)
        if any(lessons.index(lesson_map[p]) >= lessons.index(lesson) for p in prereqs):
            errors.append(f"{lesson['id']}: future/cyclic lesson prerequisite.")
        mapping = lesson.get('practice')
        if mapping is None:
            continue
        if not isinstance(mapping, dict) or mapping.get('labId') not in lab_map:
            errors.append(f"{lesson['id']}: invalid practice mapping.")
            continue
        lab = lab_map[mapping['labId']]
        practice.append(lab['id'])
        if mapping.get('route') != 'labs/' + lab['route'] or module_map.get(lesson.get('module'), {}).get('phase') != lab['phase']:
            errors.append(f"{lesson['id']}: changed lab route or wrong phase.")
    if Counter(practice) != Counter(lab_map.keys()):
        errors.append('Every delivered lab must have exactly one independent practice mapping.')
    taught = set()
    for key in sequence:
        reading = reading_map[key]
        requirements = id_list(reading, 'requires', reading_map)
        if not set(requirements) <= taught:
            errors.append(f'{key}: unmet/further-depth prerequisite concepts.')
        if reading.get('role') != 'further-depth':
            taught.add(key)
    for reading in readings:
        kind = 'application' if reading.get('role') == 'application' else 'reading'
        route(reading, kind)
        expected_source = 'content/' + canonical_route(kind, reading['id'])
        if reading.get('source') != expected_source:
            errors.append(f"{reading['id']}: noncanonical source or source traversal.")
            continue
        if reading.get('role') not in {'core', 'further-depth', 'application'} or reading.get('status') not in {'planned', 'authored'}:
            errors.append(f"{reading['id']}: invalid role/status.")
        if any(k in reading for k in ('kind', 'anchor', 'heading', 'through', 'instruction')):
            errors.append(f"{reading['id']}: legacy section-assignment fields are not v2 readings.")
        if reading.get('teaches') != [reading['id']]:
            errors.append(f"{reading['id']}: invalid taught concept cluster.")
        if any(not isinstance(reading.get(k), str) or not reading[k].strip() for k in ('title', 'goal')):
            errors.append(f"{reading['id']}: missing title/learning goal.")
        if type(reading.get('minutes')) is not int or not 1 <= reading['minutes'] <= 60:
            errors.append(f"{reading['id']}: invalid reading time.")
        if not check_sources:
            if not allow_planned and reading.get('status') != 'authored':
                errors.append(f"{reading['id']}: published reading is not authored.")
            continue
        path = Path(source_root) / expected_source
        if not path.resolve().is_relative_to(Path(source_root).resolve() / 'content'):
            errors.append(f"{reading['id']}: source escapes content root.")
            continue
        if reading.get('status') == 'planned' and allow_planned:
            if path.exists():
                errors.append(f"{reading['id']}: source exists but status is planned.")
            continue
        if reading.get('status') != 'authored' or not path.is_file():
            errors.append(f"{reading['id']}: reading source not authored/missing.")
        elif path.is_file():
            errors.extend(f"{reading['id']}: {e}" for e in validate_fragment(path.read_text(encoding='utf-8')))
    if len(routes) != len(set(r for r in routes if isinstance(r, str))):
        errors.append('Duplicate canonical routes.')
    if [s.get('phase') for s in groups['projectStages']] != ['0', '0.5', '1', '2', '3', '3.5', '4', '5', '6', '7', '8', '9']:
        errors.append('Missing project roadmap stages.')
    for stage in groups['projectStages']:
        if stage.get('module') != next((m['id'] for m in modules if m['phase'] == stage.get('phase')), None):
            errors.append('Invalid project-stage module mapping.')
    return errors


def reading_context(course, reading_id):
    reading = next((r for r in course['readings'] if r['id'] == reading_id), None)
    if reading is None:
        return None
    module = next(m for m in course['modules'] if m['id'] == reading['module'])
    lesson = next((l for l in course['lessons'] if l['id'] == reading['lesson']), None)
    sequence = module['applications'] if lesson is None else lesson['required'] if reading['role'] == 'core' else lesson['optional']
    index = sequence.index(reading_id)
    by_id = {r['id']: r for r in course['readings']}
    if index + 1 < len(sequence):
        after = by_id[sequence[index + 1]]['route']
        label = 'Continue to ' + by_id[sequence[index + 1]]['title']
    elif reading['role'] == 'application':
        after, label = module['projectCheckpoint']['route'], 'Continue to project checkpoint'
    elif reading['role'] == 'further-depth':
        after, label = lesson['route'], 'Return to lesson'
    elif lesson['practice']:
        after, label = lesson['practice']['route'] + f"?lesson={lesson['id']}&step=browser#challenge", 'Continue to Browser lab'
    else:
        local_index = module['lessons'].index(lesson['id'])
        after = (next(l for l in course['lessons'] if l['id'] == module['lessons'][local_index + 1])['route']
                 if local_index + 1 < len(module['lessons']) else by_id[module['applications'][0]]['route'])
        label = 'Continue to next lesson' if local_index + 1 < len(module['lessons']) else 'Continue to project application'
    return dict(reading=reading_id, module=module['id'], lesson=reading['lesson'], role=reading['role'],
                moduleNumber=course['modules'].index(module) + 1,
                lessonNumber=module['lessons'].index(lesson['id']) + 1 if lesson else None,
                position=index + 1, total=len(sequence), previous=by_id[sequence[index - 1]]['route'] if index else None,
                next=after, nextLabel=label, acknowledge=reading['role'] in {'core', 'application'})


def lesson_navigation_v2(course, lesson_id):
    lessons = course['lessons']
    lesson = next((l for l in lessons if l['id'] == lesson_id), None)
    if lesson is None:
        return None
    module = next(m for m in course['modules'] if m['id'] == lesson['module'])
    index = lessons.index(lesson)
    by_id = {r['id']: r for r in course['readings']}
    module_end = lesson_id == module['lessons'][-1]
    after = by_id[module['applications'][0]]['route'] if module_end else lessons[index + 1]['route']
    practice = lesson['practice']
    return dict(lesson=lesson, module=module, previous=lessons[index - 1] if index else None,
                next=lessons[index + 1] if index + 1 < len(lessons) else None, moduleEnd=module_end,
                afterLesson=after, checkpoint=module['projectCheckpoint']['route'],
                readings=[by_id[key]['route'] for key in lesson['required']],
                browser=practice['route'] + f'?lesson={lesson_id}&step=browser#challenge' if practice else None,
                python=practice['route'] + f'?lesson={lesson_id}&step=python#implement' if practice else None)
