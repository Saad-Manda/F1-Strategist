"""R7 replaces v1 page-byte requirements with reviewed coverage and v2 ownership."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from course import load_course
from build_catalog import load_registry
from audit_course import audit,preservation_errors
from migration_v2 import load_migration_inputs,validate_migration_contracts

def test_active_inventory_and_migration_meanings_are_valid():
    course=load_course();labs=load_registry()
    assert course==json.loads((ROOT/'content/course-registry.json').read_text(encoding='utf-8'))
    assert audit(course,labs)==[] and preservation_errors()==[]
    assert validate_migration_contracts(course,labs,*load_migration_inputs())==[]

def test_all_frozen_sections_have_reviewed_current_destinations():
    course=load_course();known={r['id'] for r in course['readings']}
    frozen=json.loads((ROOT/'curriculum/coverage-map.json').read_text(encoding='utf-8'))
    assert len(frozen['sections'])>300
    for section in frozen['sections']:
        assert hashlib.sha256(section['sourceHtml'].encode()).hexdigest()==section['sha256']
        assert section['destinations']
    covered=set()
    for name in ('foundations','planning-tabular','neural','advanced'):
        mapping=json.loads((ROOT/f'content/{name}-coverage.json').read_text(encoding='utf-8'))
        for section in mapping['sections']:
            covered.update(section['destinations'])
    # R3 deliberately adds explicit probability foundations absent from the old
    # source sequence; they introduce prerequisites rather than replace a section.
    assert known-covered=={'p1-probability/probability-outcomes','p1-probability/weighted-expectation'}

def test_lab_references_use_canonical_readings_not_relocations():
    known={r['route'] for r in load_course()['readings']}
    for lab in load_registry()['labs']:
        assert set(lab['references'])<=known
