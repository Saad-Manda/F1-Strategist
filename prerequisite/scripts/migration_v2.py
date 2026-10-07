"""Validate reviewed R1 decisions against frozen v1 identities and v2 ownership."""
import hashlib
import json
from paths import ROOT

MEANING_FIELDS = ('id', 'phase', 'route', 'mode', 'model', 'objective', 'browser', 'localTask', 'acceptance', 'dependencies')


def meaning_hash(lab):
    data = {k: lab[k] for k in MEANING_FIELDS}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def validate_migration_contracts(course, labs, snapshot, mapping, relocations):
    errors = []
    old = snapshot['course']
    readings = {r['id']: r for r in course['readings']}
    lessons = {l['id']: l for l in course['lessons']}
    modules = {m['id']: m for m in course['modules']}
    oldlabs = {l['id']: l for l in snapshot['labs']['labs']}
    currentlabs = {l['id']: l for l in labs['labs']}
    if (mapping.get('version') != 1 or mapping.get('fromCourseVersion') != 1 or mapping.get('toCourseVersion') != 2
            or not isinstance(mapping.get('reviewedOn'), str) or not mapping['reviewedOn'].strip()):
        return ['Invalid reviewed migration-map version.']

    def inventory(name, keys, expected):
        records = mapping.get(name)
        if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
            errors.append(f'{name}: missing migration decisions.')
            return []
        values = [tuple(r.get(k) for k in keys) for r in records]
        if any(any(not isinstance(k, str) for k in value) for value in values) or len(values) != len(set(values)) or set(values) != expected:
            errors.append(f'{name}: incomplete/duplicate migration decisions.')
        return records

    for decision in inventory('readings', ('oldId',), {(r['id'],) for r in old['resources']}):
        targets = decision.get('newIds')
        if (not isinstance(targets, list) or any(not isinstance(k, str) or k not in readings for k in targets)
                or len(targets) != len(set(k for k in targets if isinstance(k, str))) or not decision.get('reason')):
            errors.append('Invalid reviewed reading equivalence targets.')
            continue
        if decision.get('decision') == 'unread':
            if targets:
                errors.append('Unread decisions cannot carry completion.')
        elif decision.get('decision') != 'equivalent' or not targets or any(readings[k]['status'] != 'authored' for k in targets):
            errors.append('Equivalence requires explicitly reviewed authored readings.')
    for decision in inventory('practice', ('oldLesson',), {(l['id'],) for l in old['lessons']}):
        key = decision.get('labId')
        lesson = lessons.get(decision.get('newLesson'), {})
        if (key not in oldlabs or key not in currentlabs or decision.get('decision') != 'retain'
                or decision.get('oldLesson') != key or not isinstance(lesson.get('practice'), dict)
                or lesson['practice'].get('labId') != key or not decision.get('reason')):
            errors.append('Invalid reviewed practice destination.')
        elif meaning_hash(oldlabs[key]) != meaning_hash(currentlabs[key]) or decision.get('meaningSha256') != meaning_hash(oldlabs[key]):
            errors.append('Practice meaning changed; evidence retention must be reviewed again.')
    oldchecks = {(m['id'], c['id']): c['text'] for m in old['modules'] for c in m['projectCheckpoint']['checks']}
    for decision in inventory('checklists', ('oldModule', 'oldCheck'), set(oldchecks)):
        original = oldchecks.get((decision.get('oldModule'), decision.get('oldCheck')))
        module = modules.get(decision.get('newModule'), {})
        current = next((c['text'] for c in module.get('projectCheckpoint', {}).get('checks', []) if c['id'] == decision.get('newCheck')), None)
        if decision.get('decision') != 'retain' or not decision.get('reason') or original is None or current != original or decision.get('text') != current:
            errors.append('Changed/invalid checklist meaning.')
    for decision in inventory('resume', ('oldLesson',), {(l['id'],) for l in old['lessons']}):
        module = decision.get('module')
        key = decision.get('newLesson')
        if module not in modules or (key is not None and (key not in lessons or lessons[key]['module'] != module)):
            errors.append('Invalid resume fallback destination.')
    routes = relocations.get('routes')
    if (relocations.get('version') != 1 or not isinstance(relocations.get('reviewedOn'), str) or not relocations['reviewedOn'].strip()
            or not isinstance(routes, list) or any(not isinstance(r, dict) for r in routes)):
        return errors + ['Invalid reviewed relocations.']
    old_urls = [r.get('oldUrl') for r in routes]
    if any(not isinstance(k, str) for k in old_urls) or len(old_urls) != len(set(k for k in old_urls if isinstance(k, str))) or set(old_urls) != {r['id'] for r in old['resources']}:
        errors.append('Relocations must cover known old identities exactly once.')
    allowed = {r['route'] for r in readings.values()} | {m['route'] for m in modules.values()} | {'glossary.html#' + k for k in modules}
    for relocation in routes:
        module = modules.get(relocation.get('module'))
        targets = relocation.get('targets')
        if (not module or relocation.get('fallback') != module['route'] or not relocation.get('reason')
                or not isinstance(targets, list) or not targets or any(not isinstance(t, str) or t not in allowed for t in targets)
                or len(targets) != len(set(t for t in targets if isinstance(t, str)))
                or relocation.get('kind') != ('redirect' if len(targets) == 1 else 'choices')):
            errors.append('Invalid relocation targets; unknown URLs must not redirect.')
    return errors


def load_migration_inputs():
    def load(path):
        return json.loads((ROOT / path).read_text(encoding='utf-8'))
    return (load('curriculum/legacy-v1-identities.json'), load('content/progress-migration.json'),
            load('content/route-relocations.json'))
