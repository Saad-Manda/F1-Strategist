"""Validate publish-folder independence, contextual links and all pack manifests."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import sys,threading,urllib.request,zipfile,json
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
from build_catalog import SITE,load_registry
from build_reading_links import mappings,outputs
from build_static_delivery import archive_bytes,validate_delivery

def test_contextual_links_cover_every_mapped_reading_and_phase():
    for path,labs in mappings().items():
        source=path.read_text(encoding='utf-8')
        if path.name == 'index.html' and '<!-- Course reference -->' in source:
            assert 'href="../roadmap.html"' in source
            assert 'href="../library.html"' in source
            continue
        for lab in labs:assert f'../labs/{lab["route"]}' in source
    for path,source in outputs().items():assert path.read_text(encoding='utf-8')==source

def test_static_delivery_is_independent_and_archive_is_reproducible(tmp_path):
    payload=archive_bytes();assert payload==archive_bytes()
    with zipfile.ZipFile(BytesIO(payload)) as z:
        assert 'index.html' in z.namelist() and len([n for n in z.namelist() if n.endswith('.zip')])==25
        assert not any('__pycache__' in n or '.antigravity' in n or n.startswith(('scripts/','tests/','venv/')) for n in z.namelist())
        z.extractall(tmp_path)
    assert validate_delivery(tmp_path)==[]
    bad=tmp_path/'labs'/'assets'/'experiments'/'policy.js';bad.write_text("import {x} from '../../../../outside.js';",encoding='utf-8')
    assert any('invalid static asset' in e for e in validate_delivery(tmp_path))
    registry=tmp_path/'assets'/'course-registry.json'
    course=json.loads(registry.read_text(encoding='utf-8'))
    course['resources'][0]['route']='../private.html'
    registry.write_text(json.dumps(course),encoding='utf-8')
    assert any('invalid reading route' in e for e in validate_delivery(tmp_path))

def test_extracted_site_serves_root_and_subdirectory_without_rewrites(tmp_path):
    with zipfile.ZipFile(BytesIO(archive_bytes())) as z:z.extractall(tmp_path/'prerequisites')
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    for directory,prefix in ((tmp_path/'prerequisites',''),(tmp_path,'/prerequisites')):
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(directory)))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            # Serve the entire extracted publish tree, including the new guides,
            # readings, runtime assets and every pack; no source tree is consulted.
            extracted=tmp_path/'prerequisites'
            paths=sorted(path.relative_to(extracted).as_posix() for path in extracted.rglob('*') if path.is_file())
            for path in paths:
                with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}{prefix}/{path}',timeout=10) as response:assert response.status==200
            try:urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}{prefix}/unwritten.html',timeout=10)
            except urllib.error.HTTPError as e:assert e.code==404
            else:raise AssertionError('A missing file must not become an SPA fallback')
        finally:server.shutdown();server.server_close();thread.join(timeout=2)
