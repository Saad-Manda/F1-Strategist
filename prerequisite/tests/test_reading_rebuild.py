"""Independent coverage and dependency checks for the R0 curriculum handoff."""
from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_reading_rebuild import outputs, validate


class EducationalHeadings(HTMLParser):
    def __init__(self):
        super().__init__()
        self.started = False
        self.current = None
        self.parts = []
        self.headings = []

    def handle_starttag(self, tag, attrs):
        if tag == 'h1':
            self.started = True
        if self.started and tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self.current = tag
            self.parts = []

    def handle_data(self, data):
        if self.current:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == self.current:
            self.headings.append((tag, ' '.join(''.join(self.parts).split())))
            self.current = None


class ReadingRebuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def load(name):
            return json.loads((ROOT / 'curriculum' / name).read_text(encoding='utf-8'))
        cls.outline = load('outline.json')
        cls.coverage = load('coverage-map.json')
        cls.snapshot = load('legacy-v1-identities.json')

    def test_all_legacy_educational_headings_are_retained_in_inventory(self):
        for resource in self.snapshot['course']['resources']:
            if resource['kind'] != 'page':
                continue
            parser = EducationalHeadings()
            parser.feed(''.join(r['sourceHtml'] for r in self.coverage['sections'] if r['route']==resource['route']))
            records = [r for r in self.coverage['sections'] if r['route'] == resource['route']]
            inventoried = [heading for r in records for heading in [r['heading'], *r['subheadings']]]
            self.assertEqual([heading for _, heading in parser.headings], inventoried, resource['route'])
            self.assertTrue(all(r['destinations'] for r in records))

    def test_concrete_advanced_examples_and_cautions_have_destinations(self):
        examples = {
            '06-double-dqn.html': ('online [5,4,100]', 'p5-double-dueling/double-selection'),
            '07-prioritized-experience-replay.html': ('[1,4,9]', 'p5-per/importance-weights'),
            '07-pickling-and-subprocvecenv.html': ('CloudpickleWrapper', 'policy-gradients/workers'),
            '04-ppo-clipped-objective.html': ('Clipping limits an incentive', 'p9-ppo/surrogate-limits'),
        }
        for filename, (witness, destination) in examples.items():
            matching = [r for r in self.coverage['sections'] if r['route'].endswith(filename) and witness in r['text']]
            self.assertTrue(matching, filename)
            self.assertTrue(any(destination in r['destinations'] for r in matching), destination)

    def test_unknown_optional_and_future_dependencies_are_rejected(self):
        for prerequisite in ['nonexistent/concept', 'p1-values/bellman-fixed-points', 'p9-ppo/old-current']:
            altered = deepcopy(self.outline)
            altered['readings'][0]['requires'].append(prerequisite)
            with self.assertRaisesRegex(ValueError, 'Unmet concepts'):
                validate(altered, self.coverage, self.snapshot['labs'])

    def test_missing_and_duplicated_practice_are_rejected(self):
        for action in ['missing', 'duplicate']:
            altered = deepcopy(self.outline)
            if action == 'missing':
                altered['lessons'][0]['practice'] = None
            else:
                altered['lessons'][1]['practice'] = altered['lessons'][0]['practice']
            with self.assertRaisesRegex(ValueError, 'practice destination'):
                validate(altered, self.coverage, self.snapshot['labs'])

    def test_duplicate_routes_and_unmapped_topics_are_rejected(self):
        altered = deepcopy(self.outline)
        altered['readings'][1]['route'] = altered['readings'][0]['route']
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate(altered, self.coverage, self.snapshot['labs'])
        uncovered = deepcopy(self.coverage)
        uncovered['sections'][0]['destinations'] = []
        with self.assertRaisesRegex(ValueError, 'Unmapped'):
            validate(self.outline, uncovered, self.snapshot['labs'])

    def test_ppo_core_does_not_require_self_play_or_dqn_extensions(self):
        readings = {r['id']: r for r in self.outline['readings']}
        pending = [r['id'] for r in readings.values() if r['lesson'] == 'p9-ppo']
        seen = set()
        while pending:
            key = pending.pop()
            if key not in seen:
                seen.add(key)
                pending.extend(readings[key]['requires'])
        self.assertTrue(any(k.startswith('p9-probability/') for k in seen))
        self.assertFalse(any(k.startswith(('p8-', 'p5-double-dueling/', 'p5-per/')) for k in seen))

    def test_artifacts_are_reproducible_and_outside_publish_tree(self):
        for path, source in outputs().items():
            self.assertEqual(path.read_text(encoding='utf-8'), source, path.name)
            self.assertFalse(path.is_relative_to(ROOT / 'site'))


if __name__ == '__main__':
    unittest.main()
