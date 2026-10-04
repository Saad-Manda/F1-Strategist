"""Verify the generated learner journey and retained reference contents."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_course import outputs, integrate_index
from course import load_course, lesson_navigation
from build_neural_readings import PAGES
from validate_labs import validate_page


class Anchors(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))


def test_course_pages_are_current_and_resolve_at_any_static_mount():
    generated = outputs()
    page_cache = {}
    assert len(generated) == 35
    for path, source in generated.items():
        assert path.read_text(encoding='utf-8') == source
        assert validate_page(path, cache=page_cache) == []
        assert 'aria-controls="course-outline" aria-expanded="false"' in source
        assert source.count('id="course-outline"') == 1
        assert 'href="#main"' in source
        assert 'id="main"' in source
        assert len([a for a in Anchors(source).links if a.get('class') == 'course-primary']) <= 1


def test_home_opens_first_theory_and_module_ends_open_project_checkpoints():
    course = load_course(); generated = outputs(course)
    links = Anchors(generated[ROOT / 'site/index.html']).links
    primary = next(a for a in links if a.get('class') == 'course-primary')
    assert primary['href'] == 'lessons/p1-loop.html#theory'
    for module in course['modules']:
        end = lesson_navigation(course, module['lessons'][-1])
        source = generated[ROOT / 'site' / end['lesson']['route']]
        assert f'../{module["route"]}#project-checkpoint' in source
        assert module['projectCheckpoint']['preparationLabel'] in source
    roadmap = generated[ROOT / 'site/roadmap.html']
    assert 'Phase 2:' in roadmap and 'Phase 3:' in roadmap and 'Phase 7:' in roadmap
    assert 'self-play is optional' in roadmap


def test_sidebar_offers_all_numbered_lessons_steps_and_exact_required_readings():
    course = load_course()
    source = outputs(course)[ROOT / 'site/lessons/p9-ppo.html']
    links = Anchors(source).links
    lessons = [a for a in links if 'data-outline-lesson-link' in a]
    assert len(lessons) == 25
    assert {a['data-outline-lesson-link'] for a in lessons} == {l['id'] for l in course['lessons']}
    assert '7.4 · Clipping an incentive, not a probability' in source
    for lesson in course['lessons']:
        steps = [a for a in links if a.get('data-outline-owner') == lesson['id'] and 'data-outline-step' in a]
        assert {a['data-outline-step'] for a in steps} == {'theory', 'browser', 'python'}
        readings = [a['data-outline-reading'] for a in links if a.get('data-outline-owner') == lesson['id'] and 'data-outline-reading' in a]
        assert readings == lesson['required']


def test_library_contains_every_reading_and_every_lab_as_reference():
    course = load_course(); source = outputs(course)[ROOT / 'site/library.html']
    links = {a['href'] for a in Anchors(source).links}
    for resource in course['resources']:
        if resource['kind'] == 'page':
            assert resource['route'] in links
    for lesson in course['lessons']:
        assert lesson['lab'] in links and lesson['route'] in links
    # The sidebar intentionally offers guided course navigation from the library.
    # The library's own resource links remain reference visits.
    content = re.search(r'<main\b.*?</main>', source, re.S)[0]
    assert '?lesson=' not in content and '?module=' not in content


def test_compatibility_indexes_cannot_restore_competing_sequences():
    for path in (ROOT / 'site').glob('phase-*/index.html'):
        source = path.read_text(encoding='utf-8')
        assert integrate_index(path.relative_to(ROOT / 'site').as_posix(), source) == source
        assert 'Course roadmap' in source and 'Topic contents' in source
        assert 'Start here' not in source and '<h2>Reading order</h2>' not in source
        assert 'Read pages ' not in source
        assert 'class="next"' not in source


def test_original_reference_topics_and_generated_bridge_prose_are_preserved():
    # These topic sections still match the original committed reading indexes.
    # Whole-page N0 hashes continue covering all unchanged chapter shells/content.
    baseline = json.loads((ROOT / 'tests/reference-content-baseline.json').read_text(encoding='utf-8'))
    assert len(baseline) == 5
    for route, sections in baseline.items():
        source = (ROOT / 'site' / route).read_text(encoding='utf-8')
        current = {h: ' '.join(body.split()) for h, body in re.findall(
            r'<h2>(.*?)</h2>(.*?)(?=<h2>|<div class="pagenav">)', source, re.S)}
        for heading, expected in sections.items():
            assert hashlib.sha256(current[heading].encode('utf-8')).hexdigest() == expected
    for filename, (_, body, _) in PAGES.items():
        source = (ROOT / 'site/phase-5-dqn-prerequisites' / filename).read_text(encoding='utf-8')
        assert body in source
