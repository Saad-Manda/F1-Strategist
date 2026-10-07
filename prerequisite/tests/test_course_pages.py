"""Current v2 entry points, static choices and lab handoffs."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_course import outputs
from course import load_course
from validate_labs import validate_page

def test_course_pages_are_current_and_resolve_at_any_static_mount():
    generated=outputs();cache={}
    for path,source in generated.items():
        assert path.read_text(encoding='utf-8')==source
        if path.suffix!='.html':continue
        assert validate_page(path,cache=cache)==[]
        assert source.count('id="course-outline"')==1
        assert 'JavaScript is required to save completion' in source

def test_home_library_numbering_and_project_stages_use_v2():
    course=load_course();generated=outputs();site=ROOT/'site'
    assert 'href="readings/p1-loop/agent-environment-loop.html">Start reading 1.1' in generated[site/'index.html']
    assert '7.5 Limit incentives for policy changes' in generated[site/'lessons/p9-ppo.html']
    assert '27 lessons' in generated[site/'index.html']
    assert 'phase-1-rl-prerequisites/' not in generated[site/'library.html']
    for reading in course['readings']:assert reading['route'] in generated[site/'library.html']
    for stage in course['projectStages']:assert f'id="phase-{stage["phase"]}"' in generated[site/'roadmap.html']

def test_reviewed_old_urls_have_static_choices_without_legacy_bodies():
    relocations=json.loads((ROOT/'content/route-relocations.json').read_text(encoding='utf-8'))
    generated=outputs()
    for entry in relocations['routes']:
        route,*anchor=entry['oldUrl'].split('#',1);source=generated[ROOT/'site'/route]
        assert 'This topic has moved' in source
        assert 'reading-relocation.js?v=reading-20261006-r8' in source
        if anchor:assert f'id="{anchor[0]}"' in source
        assert 'class="pagenav"' not in source
    assert {p.relative_to(ROOT/'site').as_posix() for p in (ROOT/'site').glob('phase-*/*.html')}=={e['oldUrl'].split('#')[0] for e in relocations['routes']}
