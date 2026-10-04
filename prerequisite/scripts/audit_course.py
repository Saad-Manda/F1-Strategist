"""Audit the course contract against the delivered learning material.

This checks metadata, coverage and educational payload preservation.
Run from any working directory; no production project or ignored plans are needed.
"""
import argparse
import hashlib
import json
from course import validate_course, lesson_navigation, reading_url, checkpoint_reading_url

from paths import ROOT, SITE

COURSE = SITE / 'assets' / 'course-registry.json'


def audit(course, labs):
    return validate_course(course, labs)


def preservation_errors():
    baseline = json.loads((ROOT / 'tests' / 'content-baseline.json').read_text(encoding='utf-8'))
    errors = []
    for route, expected in baseline.items():
        path = SITE / route
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f'Preserved exercise/fixture changed: {route}')
    return errors


def report(course):
    lines = ['# Reading coverage', '',
             'All 79 original reading pages remain available. Targeted sections belong to',
             'their parent page. Project readiness is separate from concept completion.',
             'All pages are discoverable in the reference library; assigned sections keep',
             'their exact boundaries and explicit progress identity. Reference browsing',
             'does not change the guided Continue position.',
             '', '| Reading | Classification | Theory lessons | Project checkpoint |',
             '|---|---|---|---|']
    resources = {r['id']: r for r in course['resources']}
    for resource in course['resources']:
        if resource['kind'] != 'page':
            continue
        route = resource['route']
        lessons = [l['id'] for l in course['lessons']
                   if any(resources[key]['route'] == route for key in l['required'])]
        modules = [m['phase'] for m in course['modules'] if resource['id'] in m['projectCheckpoint']['required']]
        lines.append(f'| `{route}` | {resource["category"]} | {", ".join(lessons) or "—"} | {", ".join(modules) or "—"} |')
    return '\n'.join(lines) + '\n'


def assignments_report(course):
    resources = {r['id']: r for r in course['resources']}
    lines = ['# Course reading assignments and project handoffs', '',
             'Generated from the canonical course registry. Follow each lesson’s theory',
             'assignments, browser experiment, and local Python practice, then finish',
             'the module’s project bridge before implementing that project phase.', '']
    for module in course['modules']:
        lines += [f'## Module {module["number"]}: {module["title"]} — Project Phase {module["phase"]}', '']
        for lesson in course['lessons']:
            if lesson['module'] != module['id']:
                continue
            nav = lesson_navigation(course, lesson['id'])
            lines += [f'### {lesson["id"]}: {lesson["title"]}', '', lesson['readingGoal'], '', 'Required theory, in order:', '']
            for i, key in enumerate(lesson['required'], 1):
                resource = resources[key]
                lines += [f'{i}. **{resource["title"]}** — `{reading_url(resource)}`. {resource["instruction"]}']
            lines += ['', f'Browser: `{nav["browser"]}`.', f'Local Python: `{nav["python"]}`.',
                      f'Previous lesson: {nav["previous"]["id"] if nav["previous"] else "Start of course"}.',
                      f'Next lesson: {nav["next"]["id"] if nav["next"] else "Course review"}.', '']
            if nav['moduleEnd']:
                lines += [f'Before moving on: finish the Phase {module["phase"]} project checkpoint and implement that phase locally.', '']
            if lesson['optional']:
                lines += ['Optional review/deeper reading (full pages remain available):', '']
                lines += [f'- {resources[key]["title"]} — `{reading_url(resources[key])}`.' for key in lesson['optional']]
                lines += ['']
        checkpoint = module['projectCheckpoint']
        lines += [f'### {checkpoint["title"]}', '',
                  'After the concept labs, read these existing project bridge pages:', '']
        lines += [f'- {resources[key]["title"]} — `{checkpoint_reading_url(resources[key], module["id"])}`.' for key in checkpoint['required']]
        lines += ['', 'Transfer checklist:', ''] + ['- ' + check['text'] for check in checkpoint['checks']]
        lines += ['', f'Local project plan: `{checkpoint["plan"]}` (not a hosted course page).',
                  checkpoint['readinessMeaning'], '']
    lines += ['## Project stages without dedicated RL modules', '']
    for stage in course['projectStages']:
        if stage['module'] is None:
            lines += [f'- **Phase {stage["phase"]}: {stage["title"]}** — {stage["guidance"]}']
    return '\n'.join(lines) + '\n'


def outputs(course):
    return {ROOT / 'docs/READING_COVERAGE.md': report(course),
            ROOT / 'docs/READING_ASSIGNMENTS.md': assignments_report(course)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Write the reading coverage report')
    args = parser.parse_args()
    course = json.loads(COURSE.read_text(encoding='utf-8'))
    labs = json.loads((SITE / 'labs/assets/lab-registry.json').read_text(encoding='utf-8'))
    errors = audit(course, labs) + preservation_errors()
    if errors:
        raise SystemExit('\n'.join(errors))
    for target, content in outputs(course).items():
        if args.write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
        elif not target.is_file() or target.read_text(encoding='utf-8') != content:
            raise SystemExit(f'Course report is stale: {target.name}. Run audit_course.py --write.')
    pages = sum(r['kind'] == 'page' for r in course['resources'])
    sections = sum(r['kind'] == 'section' for r in course['resources'])
    print(f'Course audit passed: {len(course["lessons"])} lessons, {len(course["modules"])} modules, '
          f'{pages} reading pages, {sections} targeted sections; exercise and fixture bytes preserved.')



if __name__ == '__main__':
    main()
