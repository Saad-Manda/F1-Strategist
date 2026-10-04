"""Add stable navigation anchors to assigned headings without changing their content."""
import argparse
from html import escape
import re
from course import heading_text, load_course
from paths import SITE


def integrate_sections(path, source, course=None):
    course = load_course() if course is None else course
    route = path.relative_to(SITE).as_posix()
    for resource in course['resources']:
        if resource.get('kind') != 'section' or resource['route'] != route:
            continue
        matches = [m for m in re.finditer(r'<h2\b([^>]*)>(.*?)</h2>', source, re.S | re.I)
                   if heading_text(m[2]) == resource['heading']]
        if len(matches) != 1:
            raise ValueError(f'{route}: missing/ambiguous assigned heading {resource["heading"]}')
        match = matches[0]
        existing = re.search(r'\bid\s*=\s*([\"\'])(.*?)\1', match[1])
        if existing and existing[2] != resource['anchor']:
            raise ValueError(f'{route}: existing heading anchor must be preserved')
        if not existing:
            replacement = f'<h2 id="{escape(resource["anchor"], quote=True)}"{match[1]}>{match[2]}</h2>'
            source = source[:match.start()] + replacement + source[match.end():]
    return source


def outputs():
    course = load_course()
    return {SITE / route: integrate_sections(SITE / route, (SITE / route).read_text(encoding='utf-8'), course)
            for route in sorted({r['route'] for r in course['resources'] if r.get('kind') == 'section'})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    pages = outputs()
    for path, source in pages.items():
        if args.write:
            path.write_text(source, encoding='utf-8')
        elif path.read_text(encoding='utf-8') != source:
            raise SystemExit(f'Missing course section anchors: {path}')
    print(f'Course section anchors {"written" if args.write else "checked"} in {len(pages)} reading pages.')


if __name__ == '__main__':
    main()
