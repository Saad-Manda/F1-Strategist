"""Add missing contextual practice links from the registry. Use --write to update."""
import argparse
from collections import defaultdict
from html import escape
import re
from build_catalog import SITE,load_registry
from build_reading_sections import integrate_sections

def mappings():
    data=load_registry();result=defaultdict(list)
    for lab in data['labs']:
        if lab['status']!='ready':continue
        for reference in lab['references']:result[SITE/reference].append(lab)
        phase=next(p for p in data['phases'] if p['id']==lab['phase'])
        result[SITE/phase['readingDirectory']/'index.html'].append(lab)
    return result

def integrate_practice(path,source):
    source=integrate_sections(path,source)
    source=re.sub(r'\s*<!-- RL practice links -->.*?<!-- /RL practice links -->\n?', '',source,flags=re.S)
    if path.name == 'index.html' and '<!-- Course reference -->' in source:
        return source
    labs=mappings().get(path,[])
    missing=[lab for lab in labs if f'../labs/{lab["route"]}' not in source]
    if not missing:return source
    links=' · '.join(f'<a href="../labs/{escape(lab["route"])}">{escape(lab["title"])}</a>' for lab in missing)
    block=f'      <!-- RL practice links -->\n      <section aria-label="Practice this concept"><h2>Try it in a lab</h2><p>{links}</p><p>Predict a result, experiment in the browser, then implement it in local Python. Request hints or a solution when you need them.</p></section>\n      <!-- /RL practice links -->\n'
    if '<div class="pagenav">' in source:return re.sub(r'\s*<div class="pagenav">','\n\n'+block+'      <div class="pagenav">',source,count=1)
    marker='</div></main>' if '</div></main>' in source else '    </div>\n  </main>'
    if marker not in source:raise ValueError(f'No reading insertion point: {path}')
    return source.replace(marker,'\n'+block+marker,1)

def integrate(path,source):
    from build_navigation import integrate_navigation,strip_navigation
    return integrate_navigation(path,integrate_practice(path,strip_navigation(source)))

def outputs():
    from course import load_course
    paths={SITE/resource['route'] for resource in load_course()['resources']}
    return {path:integrate(path,path.read_text(encoding='utf-8')) for path in sorted(paths)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args()
    for path,source in outputs().items():
        if args.write:path.write_text(source,encoding='utf-8')
        elif path.read_text(encoding='utf-8')!=source:raise SystemExit(f'Missing contextual practice links: {path}')
    print('Contextual reading links '+('generated.' if args.write else 'are current.'))
