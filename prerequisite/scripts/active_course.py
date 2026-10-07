"""Shared v2 rendering inputs; legacy URLs contain relocation controls only."""
import json
import posixpath
from html import escape
from paths import ROOT, SITE


def raw_lab_sources():
    from build_foundation_pages import outputs as foundation
    from build_tabular_pages import outputs as tabular
    from build_neural_pages import outputs as neural
    from build_multiagent_pages import outputs as multiagent
    from build_policy_pages import outputs as policy
    result={'labs/phase-1/p1-loop.html':(ROOT/'content/labs/p1-loop.html').read_text(encoding='utf-8')}
    for builder in (foundation,tabular,neural,multiagent,policy):
        result.update({path.relative_to(SITE).as_posix():source for path,source in builder(raw=True).items()})
    return result


def supplementary_pages(course,labs,relocations,page):
    e=escape
    readings={r['route']:r for r in course['readings']}
    modules={m['id']:m for m in course['modules']}
    result={}
    glossary=json.loads((ROOT/'content/glossary.json').read_text(encoding='utf-8'))
    body='<h1>Glossary</h1><p>Look up vocabulary here; use the linked module for examples, assumptions and derivations.</p>'
    for module in course['modules']:
        body+=f'<section id="{module["id"]}"><h2>{e(module["title"])}</h2><dl>'
        body+=''.join(f'<dt>{e(term["term"])}</dt><dd>{e(term["definition"])}</dd>' for term in glossary if term['module']==module['id'])
        body+=f'</dl><p><a href="{module["route"]}">Review this module</a></p></section>'
    result['glossary.html']=page('glossary.html','Glossary',body)
    body='<h1>Lab catalog</h1><p>25 browser experiments and local Python packs. Use the lesson guides for the required reading sequence.</p>'
    for module in course['modules']:
        body+=f'<section id="phase-{module["phase"]}"><h2>{e(module["title"])}</h2>'
        for lesson in (l for l in course['lessons'] if l['module']==module['id'] and l['practice']):
            lab=next(lab for lab in labs['labs'] if lab['id']==lesson['practice']['labId'])
            body+=f'<section id="{lab["id"]}" data-lab-id="{lab["id"]}"><h3>{e(lesson["title"])}</h3><p>{e(lab["objective"])}</p><p><a href="../{lesson["route"]}">Lesson guide</a> · <a href="../{lesson["practice"]["route"]}?lesson={lesson["id"]}&amp;step=browser#challenge">Browser lab</a> · <a href="downloads/{lab["id"]}.zip">Python pack</a></p><p data-catalog-lab="{lab["id"]}"></p></section>'
        body+='</section>'
    result['labs/index.html']=page('labs/index.html','Lab catalog',body)
    groups={}
    for entry in relocations['routes']:
        groups.setdefault(entry['oldUrl'].split('#')[0],[]).append(entry)
    for route,entries in groups.items():
        base=posixpath.dirname(route)
        link=lambda target: e(posixpath.relpath(target.split('#')[0],base)+(('#'+target.split('#',1)[1]) if '#' in target else ''),quote=True)
        body='<h1>This topic has moved</h1><p>The course now uses focused readings. Choose the topic you need; visiting a relocation does not mark any reading complete.</p>'
        for entry in entries:
            anchor=entry['oldUrl'].split('#',1)[1] if '#' in entry['oldUrl'] else 'relocation-page'
            body+=f'<section id="{e(anchor,quote=True)}"><h2>{"Choose a reading" if entry["kind"]=="choices" else "Open the current topic"}</h2><ul>'
            for target in entry['targets']:
                label=readings[target]['title'] if target in readings else 'Glossary' if target.startswith('glossary') else next(m['title'] for m in modules.values() if m['route']==target)
                body+=f'<li><a href="{link(target)}">{e(label)}</a></li>'
            body+=f'</ul><p><a href="{link(entry["fallback"])}">Module overview</a></p></section>'
        # Static choices work without JavaScript. The script only handles reviewed
        # single-target deep links and never copies arbitrary context/query strings.
        result[route]=page(route,'Topic relocation',body,extra=f'<script type="module" src="{link("assets/reading-relocation.js")}"></script>')
    return result
