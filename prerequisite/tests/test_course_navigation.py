"""All generators attach navigation without modifying chapter or experiment bodies."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_navigation import outputs, integrate_navigation, strip_navigation
from build_foundation_pages import outputs as foundation
from build_tabular_pages import outputs as tabular
from build_neural_pages import outputs as neural
from build_multiagent_pages import outputs as multiagent
from build_policy_pages import outputs as policy
from build_neural_readings import outputs as bridges
from validate_labs import validate_page
from course_assets import ASSET_VERSION


def test_course_and_lab_runtime_imports_share_the_entry_point_cache_version():
    # Mixed cached versions used to fail on getSharedProgressStore or create two
    # separate stores. Every entry must request the same changed module URLs.
    from build_static_delivery import resource_links
    affected = {'storage.js', 'course-context.js', 'course-progress.js', 'course-progress-ui.js', 'course-outline.js'}
    for route in ('assets/course-navigation.js', 'assets/course-progress-ui.js',
                  'assets/course-progress.js', 'assets/course-outline.js', 'labs/assets/lab-shell.js'):
        for target in resource_links(ROOT / 'site' / route):
            if Path(target.split('?')[0]).name in affected:
                assert target.endswith('?v=' + ASSET_VERSION), (route, target)
    for path in (ROOT / 'site/labs').glob('phase-*/*.html'):
        assert f'src="../assets/lab-shell.js?v={ASSET_VERSION}"' in path.read_text(encoding='utf-8')


def test_all_readings_and_labs_have_valid_static_course_returns_and_idempotent_context():
    pages = outputs()
    page_cache = {}
    assert len(pages) == 104
    for path, source in pages.items():
        assert path.read_text(encoding='utf-8') == source
        assert integrate_navigation(path, source) == source
        assert strip_navigation(integrate_navigation(path, source)) == strip_navigation(source)
        assert 'id="course-context"' in source
        assert 'Course roadmap' in source
        assert source.count('class="course-nav"') == 1
        assert source.count('id="course-outline"') == 1
        assert sum(source.count(f'src="{prefix}assets/course-navigation.js?v={ASSET_VERSION}"') for prefix in ('../','../../')) == 1
        assert validate_page(path, cache=page_cache) == []


def test_regenerating_every_phase_preserves_course_context_and_exercise_controls():
    pages = {}
    for builder in (foundation, tabular, neural, multiagent, policy): pages.update(builder())
    assert len(pages) == 24  # The original p1-loop HTML is source material.
    for path, source in pages.items():
        assert path.read_text(encoding='utf-8') == source
        for key in ('course-context', 'challenge', 'experiment', 'implement', 'reflect',
                    'prediction-form', 'next-hint', 'reveal-solution', 'explanation', 'verified', 'complete-lab'):
            assert f'id="{key}"' in source
    for path, source in bridges().items():
        assert path.read_text(encoding='utf-8') == source
        assert 'id="course-context"' in source
