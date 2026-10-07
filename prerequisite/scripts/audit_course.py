"""Audit the active reading course and unchanged exercise/fixture bytes."""
import json,hashlib
from paths import ROOT,SITE
from course import validate_course
def audit(course,labs):return validate_course(course,labs)
def preservation_errors():
    baseline=json.loads((ROOT/'tests/content-baseline.json').read_text(encoding='utf-8'))
    return [f'Preserved exercise/fixture changed: {route}' for route,digest in baseline.items()
            if not (SITE/route).is_file() or hashlib.sha256((SITE/route).read_bytes()).hexdigest()!=digest]
if __name__=='__main__':
    from course import load_course
    from build_catalog import load_registry
    errors=audit(load_course(),load_registry())+preservation_errors()
    if errors:raise SystemExit('\n'.join(errors))
    print('Active v2 course and preserved exercise/fixture bytes verified.')
