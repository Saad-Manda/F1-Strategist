"""Attach reversible course navigation to all reading/lab sources (--write or check)."""
import argparse
import re
from build_course import action, navigation
from course import load_course
from paths import ROOT, SITE
from course_assets import version_assets
from course_sidebar import outline, strip_outline

MARKER = r'<!-- Course attachment: (assets|header|footer) -->.*?<!-- /Course attachment -->'


def strip_navigation(source):
    return strip_outline(re.sub(MARKER, '', source, flags=re.S))


def block(kind, content):
    return f'<!-- Course attachment: {kind} -->{content}<!-- /Course attachment -->'


def integrate_navigation(path, source, course=None):
    course = course or load_course()
    source = strip_navigation(source)
    route = path.relative_to(SITE).as_posix()
    lessons = [l for l in course['lessons'] if l['lab'] == route or any(
        r['route'] == route and r['id'] in l['required'] + l['optional'] for r in course['resources'])]
    if '../assets/course.css' not in source and '../../assets/course.css' not in source:
        from build_course import link
        source = source.replace('</head>', block('assets',
            f'<link rel="stylesheet" href="{link(route, "assets/course.css")}">'
            f'<script type="module" src="{link(route, "assets/course-navigation.js")}"></script>') + '</head>', 1)
    if 'class="course-nav"' not in source:
        source = re.sub(r'(<body\b[^>]*>)', lambda m: m[1] + block('header', navigation(route)), source, count=1)
    elif 'id="course-outline"' not in source:
        source = re.sub(r'(<nav class="course-nav".*?</nav>)', lambda m: m[1] + block('header', outline(route, course)), source, count=1, flags=re.S)
    links = ''.join(' · ' + action(route, l['route'] + '#theory', 'Open lesson: ' + l['title']) for l in lessons)
    panel = block('header', '<section id="course-context" class="course-context" aria-label="Course guidance">'
        '<p>Reference view · ' + action(route, 'roadmap.html', 'Course roadmap') + ' · '
        + action(route, 'library.html', 'Reference library') + '</p><p>'
        + (links.removeprefix(' · ') if links else 'Browse this topic as needed.') + '</p></section>')
    if '<div class="doc">' not in source:
        raise ValueError(f'No course guidance insertion point: {route}')
    source = source.replace('<div class="doc">', '<div class="doc">' + panel, 1)
    footer = block('footer', '<section id="course-forward" class="course-actions" aria-label="Course actions">'
        + action(route, 'roadmap.html', 'Back to roadmap') + '</section>')
    # Insert within .doc, retaining the original reference footer and all its bytes.
    marker = next((m for m in ('<div class="pagenav">', '<p class="catalog-footer">', '</div></main>', '    </div>\n  </main>') if m in source), None)
    if not marker: raise ValueError(f'No course footer insertion point: {route}')
    return version_assets(source.replace(marker, footer + marker, 1))


def outputs():
    course = load_course()
    routes = {r['route'] for r in course['resources']} | {l['lab'] for l in course['lessons']}
    return {SITE / route: integrate_navigation(SITE / route, (SITE / route).read_text(encoding='utf-8'), course)
            for route in sorted(routes)}


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--write', action='store_true'); args = p.parse_args()
    for path, source in outputs().items():
        if args.write: path.write_text(source, encoding='utf-8', newline='\n')
        elif path.read_text(encoding='utf-8') != source: raise SystemExit(f'Stale course navigation: {path}. Run with --write.')
    print('Course navigation for all 79 readings and 25 labs ' + ('generated.' if args.write else 'is current.'))


if __name__ == '__main__': main()
