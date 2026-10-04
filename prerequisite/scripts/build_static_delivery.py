"""Validate and bundle the static publish folder. No build or backend at deployment."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
import zipfile
from build_catalog import ROOT,SITE
from build_lab_downloads import FILES
from validate_labs import validate_page
from course import validate_course

def publish_files(site=SITE):
    return sorted(p for p in site.rglob('*') if p.is_file() and not any(x in {'__pycache__','.pytest_cache','.git'} for x in p.relative_to(site).parts) and p.suffix not in {'.pyc','.pyo'})

def resource_links(path):
    if path.suffix not in {'.js','.css'}:return []
    source=path.read_text(encoding='utf-8')
    if path.suffix=='.js':
        return re.findall(r'''(?:\bfrom\s*|\bimport\s*|\bnew URL\(\s*)['"]([^'"]+)['"]''',source)
    if path.suffix=='.css':
        return [x.strip(' \"\'') for x in re.findall(r'url\(([^)]+)\)',source)]
    return []

def validate_delivery(site=SITE):
    errors=[];files=publish_files(site);page_cache={}
    for path in files:
        if path.suffix=='.html':errors.extend(validate_page(path,site,page_cache))
        for link in resource_links(path):
            if '://' in link or link.startswith('data:'):continue
            target=(path.parent/link.split('?')[0].split('#')[0]).resolve()
            if link.startswith('/') or not target.is_relative_to(site.resolve()) or not target.is_file():errors.append(f'{path.relative_to(site)}: invalid static asset {link}')
    data=json.loads((site/'labs'/'assets'/'lab-registry.json').read_text(encoding='utf-8'))
    try:
        course=json.loads((site/'assets'/'course-registry.json').read_text(encoding='utf-8'))
        errors.extend(validate_course(course,data,site=site))
    except (OSError,json.JSONDecodeError) as error:
        errors.append(f'Invalid course registry: {error}')
    for lab in data['labs']:
        if lab['status']!='ready':errors.append(f'{lab["id"]}: incomplete lab in final delivery');continue
        folder=site/'labs'/'downloads'/lab['id'];archive=folder.with_suffix('.zip')
        required=set(FILES)|({'compare.py'} if (folder/'compare.py').is_file() else set())
        try:
            with zipfile.ZipFile(archive) as z:
                expected={f'{lab["id"]}/{name}' for name in required}
                if set(z.namelist())!=expected:errors.append(f'{lab["id"]}: wrong archive manifest')
                for name in required:
                    if z.read(f'{lab["id"]}/{name}')!=(folder/name).read_bytes():errors.append(f'{lab["id"]}: stale archived {name}')
        except (OSError,KeyError,zipfile.BadZipFile) as e:errors.append(f'{lab["id"]}: invalid archive: {e}')
    return errors

def archive_bytes():
    errors=validate_delivery()
    if errors:raise ValueError('\n'.join(errors))
    stream=BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for path in publish_files():
            info=zipfile.ZipInfo(path.relative_to(SITE).as_posix(),date_time=(2026,10,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,path.read_bytes())
    return stream.getvalue()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args()
    payload=archive_bytes();target=ROOT/'dist'/'rl-prerequisites-static.zip'
    if args.write:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
    elif not target.exists() or target.read_bytes()!=payload:raise SystemExit('Static delivery is missing or stale. Run with --write.')
    print(f'Validated {len(publish_files())} publish files and 25 standalone packs. Static archive '+('written.' if args.write else 'is current.'))
