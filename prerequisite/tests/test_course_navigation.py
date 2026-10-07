"""All active entry points share one cache version and transaction coordinator."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_static_delivery import resource_links
from course_assets import ASSET_VERSION
from active_course import raw_lab_sources
from build_readings import render_outputs

def test_active_runtime_graph_is_versioned_and_has_no_legacy_writers():
    active=['assets/reading-bootstrap.js','assets/reading-navigation.js','assets/reading-shell.js','assets/reading-lab.js','assets/reading-session.js','assets/reading-store.js','assets/reading-relocation.js','assets/course-progress-v2.js']
    for route in active:
        for target in resource_links(ROOT/'site'/route):
            if '.js' in target or '.json' in target:assert target.endswith('?v='+ASSET_VERSION),(route,target)
    for path in (ROOT/'site').rglob('*.html'):
        source=path.read_text(encoding='utf-8')
        assert 'course-navigation.js' not in source and 'lab-shell.js' not in source
        for target in resource_links(ROOT/'site/assets/reading-shell.js'):assert 'course-progress.js' not in target

def test_raw_lab_regeneration_preserves_controls_and_exact_v2_handoffs():
    sources=raw_lab_sources();_,pages=render_outputs(sources)
    assert len(sources)==25
    for route in sources:
        source=pages[route]
        assert (ROOT/'site'/route).read_text(encoding='utf-8')==source
        for control in ('challenge','experiment','implement','reflect','prediction-form','next-hint','reveal-solution','explanation','verified','complete-lab','finish-browser'):
            assert f'id="{control}"' in source
        assert 'After Python practice' in source and '-prerequisites/' not in source

def test_retired_generators_cannot_resurrect_legacy_sources():
    from build_neural_readings import outputs as neural
    from build_reading_links import outputs as links
    from build_reading_sections import outputs as sections
    assert neural()==links()==sections()=={}
