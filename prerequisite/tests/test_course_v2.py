"""V2 ownership, source, practice and reviewed-identity contract failures."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from course_v2 import load_course_v2, validate_course_v2, validate_fragment, canonical_route, reading_context
from migration_v2 import load_migration_inputs, validate_migration_contracts
from course import validate_course, lesson_navigation, reading_url, resolve_context


class CourseV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.course = load_course_v2()
        cls.labs = json.loads((ROOT / 'site/labs/assets/lab-registry.json').read_text(encoding='utf-8'))
        cls.snapshot, cls.mapping, cls.relocations = load_migration_inputs()

    def errors(self, course):
        return validate_course_v2(course, self.labs, allow_planned=True)

    def test_draft_is_valid_but_publication_requires_bodies(self):
        self.assertEqual(self.errors(self.course), [])
        self.assertEqual(validate_migration_contracts(self.course,self.labs,self.snapshot,self.mapping,self.relocations), [])
        errors = validate_course(self.course,self.labs)
        self.assertEqual(sum('source not authored/missing' in e for e in errors),sum(r['status']=='planned' for r in self.course['readings']))

    def test_delivered_metadata_needs_authored_status_but_not_unpublished_fragments(self):
        course = deepcopy(self.course)
        course['readings'][0]['status'] = 'planned'
        self.assertTrue(validate_course_v2(course,self.labs,check_sources=False))
        for reading in course['readings']: reading['status'] = 'authored'
        self.assertEqual(validate_course_v2(course,self.labs,check_sources=False), [])
        with TemporaryDirectory() as temporary:
            self.assertTrue(validate_course_v2(course,self.labs,source_root=temporary))

    def test_malformed_ownership_duplicate_membership_and_application_role(self):
        for mutation in ['owner','module','repeat','application','unowned']:
            course = deepcopy(self.course)
            if mutation == 'owner': course['readings'][0]['lesson'] = 'p1-state'
            if mutation == 'module': course['lessons'][0]['module'] = 'planning'
            if mutation == 'repeat': course['lessons'][1]['required'].append(course['lessons'][0]['required'][0])
            if mutation == 'application': next(r for r in course['readings'] if r['role']=='application')['lesson'] = 'p1-loop'
            if mutation == 'unowned': course['lessons'][0]['required'].pop()
            self.assertTrue(self.errors(course),mutation)

    def test_duplicate_ids_routes_and_source_traversal(self):
        for mutation in ['id','route','source']:
            course = deepcopy(self.course)
            if mutation == 'id': course['readings'][1]['id'] = course['readings'][0]['id']
            if mutation == 'route': course['readings'][1]['route'] = course['readings'][0]['route']
            if mutation == 'source': course['readings'][0]['source'] = 'content/../../site/index.html'
            self.assertTrue(self.errors(course),mutation)

    def test_wrong_ownership_types_return_errors_without_crashing(self):
        for group, field, value in [('modules','phase',{}),('lessons','module',[]),
                                    ('readings','lesson',{}),('readings','role',[]),
                                    ('lessons','practice',{'labId':[],'route':None})]:
            course = deepcopy(self.course)
            course[group][0][field] = value
            self.assertTrue(self.errors(course))

    def test_legacy_section_fields_cannot_masquerade_as_dedicated_readings(self):
        course = deepcopy(self.course)
        course['readings'][0]['anchor'] = 'old-section'
        self.assertTrue(any('legacy section-assignment' in e for e in self.errors(course)))

    def test_practice_is_independent_of_lesson_identity(self):
        course = deepcopy(self.course)
        lesson = course['lessons'][0]
        old_id, new_id = lesson['id'], 'interaction-basics'
        lesson['id'], lesson['route'] = new_id, canonical_route('lesson',new_id)
        course['modules'][0]['lessons'][0] = new_id
        for other in course['lessons']:
            other['prerequisites'] = [new_id if p == old_id else p for p in other['prerequisites']]
        for reading in course['readings']:
            if reading['lesson'] == old_id: reading['lesson'] = new_id
        self.assertEqual(self.errors(course), [])
        self.assertEqual(lesson['practice']['labId'], 'p1-loop')
        self.assertEqual(reading_context(course,lesson['required'][-1])['next'], 'labs/phase-1/p1-loop.html?lesson=interaction-basics&step=browser#challenge')

    def test_theory_only_has_no_manufactured_lab(self):
        lesson = next(l for l in self.course['lessons'] if l['id'] == 'p1-probability')
        self.assertIsNone(lesson['practice'])
        context = reading_context(self.course,lesson['required'][-1])
        self.assertEqual(context['next'], 'lessons/p1-values.html')
        self.assertEqual(context['position'], 2)
        optional = next(r for r in self.course['readings'] if r['role'] == 'further-depth')
        self.assertFalse(reading_context(self.course,optional['id'])['acknowledge'])
        navigation = lesson_navigation(self.course,lesson['id'])
        self.assertIsNone(navigation['browser'])
        self.assertIsNone(navigation['python'])
        self.assertEqual(navigation['afterLesson'],'lessons/p1-values.html')

    def test_shared_python_helpers_dispatch_v2_without_section_queries(self):
        reading = self.course['readings'][0]
        self.assertEqual(reading_url(reading,'p1-loop'),reading['route'])
        self.assertEqual(resolve_context(self.course,reading['route']),reading_context(self.course,reading['id']))
        self.assertIsNone(resolve_context(self.course,reading['route'],lesson_id='p1-state',step='theory'))
        self.assertIsNone(resolve_context(self.course,'unknown.html'))

    def test_complete_fragment_can_be_authored_without_other_placeholder_bodies(self):
        with TemporaryDirectory() as temporary:
            course = deepcopy(self.course)
            for item in course['readings']: item['status'] = 'planned'
            reading = course['readings'][0]
            reading['status'] = 'authored'
            path = Path(temporary) / reading['source']
            path.parent.mkdir(parents=True)
            path.write_text('<h2 id="worked-example">An interaction</h2><p>' + 'A small agent observes a location and chooses a legal action. ' * 6 + '</p><pre><code>action = 1</code></pre>',encoding='utf-8')
            self.assertEqual(validate_course_v2(course,self.labs,source_root=temporary,allow_planned=True), [])
            path.write_text((ROOT / 'site/phase-1-rl-prerequisites/01-rl-fundamentals.html').read_text(encoding='utf-8'),encoding='utf-8')
            self.assertTrue(any('forbidden' in e for e in validate_course_v2(course,self.labs,source_root=temporary,allow_planned=True)))

    def test_fragment_rejects_placeholders_bad_markup_and_active_content(self):
        for source in ['<p>TODO</p>', '<h2>Title</h2><p>Unclosed', '<script>alert(1)</script>',
                       '<h2 id="repeat">One</h2><h2 id="repeat">Two</h2>', '<p onclick="bad()">Example</p>']:
            self.assertTrue(validate_fragment(source))

    def test_future_and_optional_concepts_cannot_supply_core_prerequisites(self):
        for prerequisite in ['p9-ppo/old-current','p1-values/bellman-fixed-points']:
            course = deepcopy(self.course)
            course['readings'][0]['requires'].append(prerequisite)
            self.assertTrue(any('prerequisite concepts' in e for e in self.errors(course)))

    def test_changed_evidence_meaning_and_unreviewed_equivalence_are_rejected(self):
        for mutation in ['practice','checklist','equivalence','unknown-route','missing-route']:
            labs, course, mapping, routes = map(deepcopy,[self.labs,self.course,self.mapping,self.relocations])
            if mutation == 'practice': labs['labs'][0]['acceptance'] = ['A changed exercise contract.']
            if mutation == 'checklist': course['modules'][0]['projectCheckpoint']['checks'][0]['text'] = 'New knowledge'
            if mutation == 'equivalence':
                course['readings'][0]['status'] = 'planned'
                mapping['readings'][0].update(decision='equivalent',newIds=[course['readings'][0]['id']])
            if mutation == 'unknown-route': routes['routes'][0]['targets'] = ['https://example.com']
            if mutation == 'missing-route': routes['routes'].pop()
            self.assertTrue(validate_migration_contracts(course,labs,self.snapshot,mapping,routes),mutation)

    def test_python_and_javascript_reject_the_same_metadata_mutations(self):
        cases = [deepcopy(self.course) for _ in range(8)]
        cases[1]['readings'][0]['lesson'] = 'p1-state'
        cases[2]['readings'][1]['id'] = cases[2]['readings'][0]['id']
        cases[3]['lessons'][0]['practice'] = None
        cases[4]['lessons'][3]['required'] = []
        cases[5]['readings'][0]['source'] = '../legacy.html'
        cases[6]['readings'][0]['requires'] = ['p9-ppo/old-current']
        cases[7]['readings'][0]['anchor'] = 'old-section'
        script = "import {validateCourseV2} from './site/assets/course-model-v2.js'; let s=''; for await (const c of process.stdin) s+=c; const {cases,labs}=JSON.parse(s); console.log(JSON.stringify(cases.map(c=>{try{validateCourseV2(c,labs);return true;}catch{return false;}})));"
        run = subprocess.run(['node','--input-type=module','-e',script],input=json.dumps({'cases':cases,'labs':self.labs}),cwd=ROOT,text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(run.stdout),[not self.errors(c) for c in cases])


if __name__ == '__main__':
    unittest.main()
