"""R2 navigation, portable rendering and numerical teaching witnesses."""
from html.parser import HTMLParser
from pathlib import Path
import importlib.util
import json
import posixpath
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'scripts'))
from build_readings import render_outputs
from validate_labs import validate_page


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.code=[]
        self.in_code=False
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag in ('a','link','script'):
            self.links.append(attrs.get('href',attrs.get('src','')))
        if tag=='code': self.in_code=True;self.code.append('')
    def handle_endtag(self,tag):
        if tag=='code':self.in_code=False
    def handle_data(self,text):
        if self.in_code:self.code[-1]+=text


def test_authored_pages_are_distinct_reproducible_and_keep_v1_inactive():
    outputs,overlays=render_outputs()
    assert (outputs,overlays)==render_outputs()
    pages={k:v for k,v in outputs.items() if k.startswith(('readings/','applications/'))}
    assert len(pages)==134 and len(set(pages.values()))==134
    for route,source in outputs.items():assert (ROOT/'site'/route).read_text(encoding='utf-8')==source
    for route,source in pages.items():
        assert ' of ' in source
        assert 'Finish reading and continue' in source or 'Optional depth does not gate progress' in source
        assert 'JavaScript is required to save completion' in source
        assert 'phase-1-rl-prerequisites/' not in source
    assert 'reading-bootstrap.js' in (ROOT/'site/index.html').read_text(encoding='utf-8')
    assert 'reading-bootstrap.js' in overlays['index.html']
    assert 'phase-1-rl-prerequisites/' not in overlays['labs/phase-1/p1-loop.html']
    for route,source in overlays.items():
        if route.startswith('labs/'):
            assert '-prerequisites/' not in source


def test_root_and_nested_static_links_need_no_javascript():
    outputs,overlays=render_outputs()
    routes={**outputs,**overlays}
    for route,source in routes.items():
        if not route.endswith('.html'):continue
        parser=Elements();parser.feed(source)
        for link in parser.links:
            target=urlsplit(link)
            if target.scheme:continue
            assert not target.path.startswith('/')
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(route),target.path)) if target.path else route
            assert resolved in routes or (ROOT/'site'/resolved).is_file(),(route,link)
            assert not resolved.startswith('../')
            if target.fragment and resolved in routes:
                assert f'id="{target.fragment}"' in routes[resolved],(route,link)


def test_reading_code_and_trace_witnesses_match_unchanged_pack():
    import gymnasium as gym
    from gymnasium.utils.env_checker import check_env
    path=ROOT/'site/labs/downloads/p1-loop/solution.py'
    spec=importlib.util.spec_from_file_location('chain_reading_witness',path)
    pack=importlib.util.module_from_spec(spec)
    sys.path.insert(0,str(path.parent))
    try: spec.loader.exec_module(pack)
    finally: sys.path.pop(0)
    namespace={'ChainEnv':pack.ChainEnv}
    def blocks(name):
        parser=Elements();parser.feed((ROOT/f'content/readings/p1-loop/{name}.html').read_text(encoding='utf-8'))
        return [c for c in parser.code if '\n' in c]
    exec(blocks('agent-environment-loop')[0],namespace)
    exec(next(c for c in blocks('episode-endings') if c.startswith('def collect_episode')),namespace)
    env=gym.wrappers.TimeLimit(pack.ChainEnv(),max_episode_steps=6)
    trace=namespace['collect_episode'](env,namespace['policy'],seed=7)
    assert [(r['observation'],r['reward'],r['terminated'],r['truncated']) for r in trace]==[(1,-1.0,False,False),(2,5.0,True,False)]
    assert sum(r['reward'] for r in trace)==4
    env.close()
    exec(blocks('episode-endings')[0],namespace)
    assert (namespace['observation'],namespace['reward'],namespace['terminated'],namespace['truncated'])==(1,-1.0,False,True)
    namespace['env'].close()
    for snippet in blocks('spaces-and-contract'):exec(snippet,namespace)
    env=pack.ChainEnv();check_env(env,skip_render_check=True);env.reset(seed=7)
    assert env.step(0)[:4]==(0,-1.0,False,False)
    env.close()
    env=gym.wrappers.TimeLimit(pack.ChainEnv(),max_episode_steps=2)
    trace=namespace['collect_episode'](env,namespace['policy'])
    assert trace[-1]['terminated'] and trace[-1]['truncated']
    env.close()


def test_repeated_sidebar_anchors_share_resolution_without_accepting_outside_paths(tmp_path, monkeypatch):
    site=tmp_path/'site';site.mkdir()
    target=site/'target.html';target.write_text('<h1 id="topic">Topic</h1>',encoding='utf-8')
    source=site/'index.html'
    source.write_text('<a href="target.html#topic">Review</a>'*40,encoding='utf-8')
    original=Path.resolve
    calls={}
    def resolved(path,*args,**kwargs):
        calls[path]=calls.get(path,0)+1
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'resolve',resolved)
    assert validate_page(source,site,cache={})==[]
    assert calls[target]<=2
    outside=tmp_path/'outside.html';outside.write_text('<h1>Outside</h1>',encoding='utf-8')
    source.write_text('<a href="../outside.html">Outside</a>',encoding='utf-8')
    assert any('outside publish-folder' in error for error in validate_page(source,site,cache={}))
