"""Render the complete authoritative reading course and unchanged practice bodies."""
import argparse
import json
import posixpath
import re
from html import escape as e
from paths import ROOT, SITE
from course_v2 import load_course_v2, validate_course_v2, reading_context, lesson_navigation_v2
from course_assets import version_assets


def render_outputs(lab_sources=None):
    course = load_course_v2()
    labs = json.loads((SITE / 'labs/assets/lab-registry.json').read_text(encoding='utf-8'))
    errors = validate_course_v2(course, labs, allow_planned=True)
    if errors:
        raise ValueError('\n'.join(errors))
    readings = {r['id']: r for r in course['readings']}
    lessons = {l['id']: l for l in course['lessons']}
    available = lambda l: all(readings[k]['status'] == 'authored' for k in l['required'])
    available_names = ', '.join(m['title'] for m in course['modules'] if all(available(lessons[k]) for k in m['lessons']))
    availability_note = 'Later modules are planned' if any(r['status']=='planned' for r in readings.values()) else 'All learning modules are authored'

    def page(route, title, body, current=None, lesson=None, extra='', lab=None, module_id=None):
        def href(target):
            path, *suffix = re.split(r'(?=[?#])', target, maxsplit=1)
            return e(posixpath.relpath(path, posixpath.dirname(route) or '.') + ''.join(suffix), quote=True)
        def link(target, label, attrs=''):
            return f'<a class="outline-link" href="{href(target)}" {attrs}>{label}</a>'
        tree = []
        for mi, module in enumerate(course['modules'], 1):
            active = lesson in module['lessons'] or module_id == module['id'] or (current and readings[current]['module'] == module['id'])
            rows = []
            for li, key in enumerate(module['lessons'], 1):
                l = lessons[key]
                steps = []
                for rid in l['required'] + l['optional']:
                    r = readings[rid]
                    label = e(r['title']) + (' · Optional depth' if r['role']=='further-depth' else '') + f'<small data-reading-status="{rid}"></small>'
                    steps.append(link(r['route'], label, f'data-reading="{rid}"' + (' aria-current="page" data-current' if rid == current else '')) if r['status'] == 'authored' else f'<span class="outline-link planned">{label} · Planned</span>')
                if l['practice'] and available(l):
                    for step, label, anchor in [('browser','Browser lab','challenge'),('python','Python practice','implement')]:
                        steps.append(link(l['practice']['route'] + f'?lesson={key}&step={step}#{anchor}', label, f'data-practice-step="{step}" data-practice-owner="{key}"'))
                overview = link(l['route'], 'Lesson overview') if available(l) else f'<span class="outline-link planned">Planned lesson</span>'
                rows.append(f'<details {"open" if key == lesson else ""}><summary>{mi}.{li} {e(l["title"])}</summary>{overview}<div class="outline-steps">{"".join(steps)}</div></details>')
            applications = ''.join(link(readings[k]['route'], e(readings[k]['title']) + f'<small data-reading-status="{k}"></small>', 'aria-current="page" data-current' if k==current else '') if readings[k]['status']=='authored' else f'<span class="outline-link planned">{e(readings[k]["title"])} · Planned</span>' for k in module['applications'])
            tree.append(f'<details {"open" if active else ""}><summary>{mi}. {e(module["title"])}</summary>{link(module["route"], "Module overview")}{"".join(rows)}<details {"open" if current in module["applications"] else ""}><summary>Project application</summary>{applications}</details>{link(module["projectCheckpoint"]["route"], "Project checkpoint")}</details>')
        return version_assets(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} · Reading course</title>
<link rel="stylesheet" href="{href('assets/style.css')}"><link rel="stylesheet" href="{href('assets/course.css')}"><link rel="stylesheet" href="{href('assets/reading.css')}">{extra}
<script type="module" src="{href('assets/reading-bootstrap.js')}"></script></head>
<body class="reading-page" data-reading-id="{current or ''}" data-lesson-id="{lesson or ''}" data-module-id="{module_id or (readings[current]['module'] if current else lessons[lesson]['module'] if lesson else '')}" {('data-lab-id="'+lab+'"' if lab else '')}>
<a class="skip-link" href="#main">Skip to reading</a><nav class="course-nav" aria-label="Course navigation"><a class="course-brand" href="{href('index.html')}">Reading course</a><button id="contents-toggle" class="course-menu" aria-controls="course-outline" aria-expanded="false" hidden>Course contents</button></nav>
<aside id="course-outline" class="course-outline" aria-label="Course contents"><div class="outline-heading"><h2>Course contents</h2><button class="outline-close" hidden>Close contents</button></div><p class="outline-location">7 learning modules · 134 readings · 25 practice pairs</p><nav class="outline-global">{link('index.html','Home')}{link('roadmap.html','Roadmap')}{link('library.html','Library')}{link('glossary.html','Glossary')}{link('labs/index.html','Lab catalog')}</nav><nav class="outline-tree" aria-label="Modules, lessons and readings">{''.join(tree)}</nav></aside><div id="reading-backdrop" class="course-drawer-backdrop" hidden></div>
<main id="main" tabindex="-1"><article class="doc">{body}<section id="migration-notice" hidden><p id="migration-message" role="status"></p><button id="activate-migration" hidden>I have closed or reloaded other course tabs · Retain my progress</button><button id="acknowledge-migration" hidden>Acknowledge course update</button></section><p id="reading-status" role="status" aria-live="polite"></p><noscript><p>JavaScript is required to save completion. Reading links, Previous, Next and Python downloads remain available.</p></noscript><div class="button-row"><button id="reading-export" hidden>Export course and lab progress</button><label id="reading-import-label" hidden>Import course or lab progress (replaces current progress)<input id="reading-import" type="file" accept=".json,application/json"></label><button id="recovery-export" hidden>Export original saved data for recovery</button></div></article></main></body></html>\n''')

    from migration_v2 import load_migration_inputs
    snapshot,mapping,relocations=load_migration_inputs()
    outputs = {'assets/course-reading-data.json': json.dumps({'course':course,'labs':labs,'snapshot':snapshot,'mapping':mapping,'release':'reading-20261006-r8'},indent=2) + '\n',
               'assets/course-registry.json':json.dumps(course,ensure_ascii=False,indent=2)+'\n',
               'assets/route-relocations.json':json.dumps(relocations,ensure_ascii=False,indent=2)+'\n'}
    overlays = {}
    for r in course['readings']:
        if r['status'] != 'authored':
            continue
        context = reading_context(course, r['id'])
        l = lessons.get(r['lesson'])
        module = next(m for m in course['modules'] if m['id']==r['module'])
        base = posixpath.dirname(r['route'])
        relative = lambda target: e(posixpath.relpath(target.split('?')[0], base) + ('?' + target.split('?',1)[1] if '?' in target else ''), quote=True)
        prev = f'<a class="course-link" href="{relative(context["previous"])}">Previous</a>' if context['previous'] else f'<a class="course-link" href="{relative(l["route"] if l else module["route"])}">{"Lesson" if l else "Module"} overview</a>'
        owner = f'<a href="{relative(l["route"])}">Lesson {context["moduleNumber"]}.{context["lessonNumber"]}</a>' if l else 'Project application'
        kind = 'Optional depth reading' if r['role']=='further-depth' else 'Application reading' if not l else 'Reading'
        body = f'<p class="course-breadcrumb"><a href="{relative(module["route"])}">Module {context["moduleNumber"]}: {e(module["title"])}</a> · {owner}</p><p class="course-meta">{kind} {context["position"]} of {context["total"]} · {r["minutes"]} minutes</p><h1>{e(r["title"])}</h1><p class="dek">{e(r["goal"])}</p>' + ('<p data-lesson-count></p>' if l else '<p data-application-count></p>')
        body += (ROOT / r['source']).read_text(encoding='utf-8')
        primary = f'<button class="course-primary" id="finish-reading" data-next="{relative(context["next"])}" hidden>Finish reading and continue</button>' if context['acknowledge'] else f'<a class="course-primary" href="{relative(context["next"])}">Return to lesson · Optional depth does not gate progress</a>'
        next_label = next((n['title'] for n in course['lessons'] if n['route']==context['next']),context['nextLabel'].removeprefix('Continue to '))
        body += f'<nav class="course-actions" aria-label="Reading actions">{prev}{primary}<a class="course-link" href="{relative(context["next"])}">Next: {e(next_label)}</a></nav>'
        outputs[r['route']] = page(r['route'],r['title'],body,r['id'],r['lesson'])
    first = next(l for l in course['lessons'] if available(l))
    overlays['index.html'] = page('index.html','Learn reinforcement learning',f'<p class="course-meta">7 modules · 27 lessons · 134 readings · 25 practice pairs</p><h1>Learn reinforcement learning, one idea at a time</h1><p>Read an explanation, inspect the evidence in a browser, then build and check it in Python. Each module ends with F1 application readings and a separate preparation checkpoint.</p><a class="course-primary" href="{readings[first["required"][0]]["route"]}">Start reading 1.1</a><p><a href="modules/foundations.html">Explore Module 1: Foundations</a></p><a class="course-link" data-home-continue href="{readings[first["required"][0]]["route"]}">Continue learning</a><p data-course-count></p>')
    for module in course['modules']:
        items = ''.join(f'<li><a href="../{lessons[k]["route"]}">{e(lessons[k]["title"])}</a></li>' if available(lessons[k]) else f'<li>{e(lessons[k]["title"])} · Planned</li>' for k in module['lessons'])
        ready = all(readings[k]['status']=='authored' for k in module['applications']) and all(available(lessons[k]) for k in module['lessons'])
        apps = ''.join(f'<li><a href="../{readings[k]["route"]}">{e(readings[k]["title"])}</a></li>' if readings[k]['status']=='authored' else f'<li>{e(readings[k]["title"])} · Planned</li>' for k in module['applications'])
        checks = ''.join(f'<p><label><input type="checkbox" data-check="{c["id"]}" disabled> {e(c["text"])}</label></p>' for c in module['projectCheckpoint']['checks']) if ready else '<p>This checkpoint becomes available when this module is authored.</p>'
        stage_index = next(i for i,s in enumerate(course['projectStages']) if s['module']==module['id'])
        next_stage = course['projectStages'][stage_index+1] if stage_index+1<len(course['projectStages']) else None
        handoff = f'<p><a href="../roadmap.html#phase-{next_stage["phase"]}">Next project stage: {e(next_stage["title"])} (Phase {e(next_stage["phase"])})</a></p>' if next_stage else '<p>Review the full project roadmap and its implementation plans.</p>'
        next_module = course['modules'][course['modules'].index(module)+1] if course['modules'].index(module)+1<len(course['modules']) else None
        if next_module:
            handoff += f'<p><a href="../{next_module["route"]}">Next learning module: {e(next_module["title"])}</a>' + (' · Planned' if not all(available(lessons[k]) for k in next_module['lessons']) else '') + '</p>'
        if module['id']=='foundations': handoff += '<p><a href="../roadmap.html#phase-3">Baseline strategies (Phase 3)</a></p>'
        checkpoint = f'<section id="project-checkpoint"><h2>{e(module["projectCheckpoint"]["preparationLabel"])}</h2><p>Review the project implementation plan: <code>{e(module["projectCheckpoint"]["plan"])}</code>.</p><p>{e(module["projectCheckpoint"]["readinessMeaning"])}</p>' + ('<p data-application-count></p>' if ready else '') + checks + ('<p data-checkpoint-status role="status"></p>' if ready else '') + handoff + '</section>'
        overlays[module['route']] = page(module['route'],module['title'],f'<h1>{e(module["title"])}</h1><p>{e(module["objective"])}</p><p>Follow the lessons in order, then transfer the concepts to the project application. Prerequisites guide you; you can browse ahead.</p><ol>{items}</ol><h2>Project application</h2><ol>{apps}</ol>{checkpoint}',module_id=module['id'])
    for l in course['lessons']:
        if not available(l): continue
        items = ''.join(f'<li><a href="../{readings[k]["route"]}">{e(readings[k]["title"])}</a></li>' for k in l['required'])
        m = next(m for m in course['modules'] if m['id']==l['module'])
        numbering = f'{course["modules"].index(m)+1}.{m["lessons"].index(l["id"])+1}'
        prior = ', '.join(lessons[k]['title'] for k in l['prerequisites']) or 'Basic Python; no prior reinforcement learning knowledge'
        goals = ''.join(f'<li>{e(readings[k]["goal"])}</li>' for k in l['required'])
        practice = f'<p><a href="../{l["practice"]["route"]}?lesson={l["id"]}&amp;step=browser#challenge">Browser lab</a> · <a href="../{l["practice"]["route"]}?lesson={l["id"]}&amp;step=python#implement">Python practice</a></p>' if l['practice'] else '<p>Theory-only lesson: no browser lab or Python pack. Finish the required readings to continue to the next lesson.</p>'
        depth = '<h2>Optional further depth</h2>' + ''.join(f'<p><a href="../{readings[k]["route"]}">{e(readings[k]["title"])}</a> · Does not gate completion.</p>' for k in l['optional']) if l['optional'] else ''
        overlays[l['route']] = page(l['route'],l['title'],f'<p class="course-meta">Lesson {numbering}</p><h1>{e(l["title"])}</h1><p>Suggested prerequisites: {e(prior)}.</p><h2>What you will understand</h2><ul>{goals}</ul><p data-lesson-count></p><h2>Read theory</h2><ol>{items}</ol><a class="course-primary" href="../{readings[l["required"][0]]["route"]}">Start reading</a>{practice}{depth}',lesson=l['id'])
        # New theory-only routes have no v1 page to preserve; make their links portable.
        if l['practice'] is None: outputs[l['route']]=overlays[l['route']]
    for route,title in [('library.html','Reading library'),('roadmap.html','Course roadmap')]:
        body = ''.join(f'<li><a href="{r["route"]}">{e(r["title"])}</a></li>' for r in readings.values() if r['status']=='authored')
        if route=='roadmap.html':
            body = ''.join(f'<section id="phase-{s["phase"]}"><h2>Phase {e(s["phase"])}: {e(s["title"])}</h2>' + (f'<p><a href="modules/{s["module"]}.html">Open learning module</a></p>' if s['module'] else '<p>Project implementation stage; no separate RL lesson. Follow its project plan after the preceding preparation.</p>') + '</section>' for s in course['projectStages'])
            overlays[route] = page(route,title,f'<h1>{title}</h1><p>Available: {e(available_names)}. {availability_note}. Project stages retain setup, dashboard, baselines and deployment alongside the learning sequence.</p>{body}')
        else:
            body=''.join(f'<section><h2>{e(m["title"])}</h2><ol>'+''.join(f'<li><a href="{r["route"]}">{e(r["title"])}</a> · {e(r["role"])}</li>' for r in readings.values() if r['module']==m['id'])+'</ol></section>' for m in course['modules'])
            overlays[route] = page(route,title,f'<h1>{title}</h1><p>All 134 readings, including optional depth and project application. The sidebar shows the course sequence.</p>{body}<p><a href="labs/index.html">Browse the 25 practice pairs</a> · <a href="glossary.html">Glossary</a></p>')
    from active_course import supplementary_pages, raw_lab_sources
    overlays.update(supplementary_pages(course,labs,relocations,page))
    if lab_sources is None: lab_sources=raw_lab_sources()
    for l in course['lessons']:
        if not available(l) or not l['practice']: continue
        route = l['practice']['route']; lab_id=l['practice']['labId']
        if route not in lab_sources: continue
        raw = lab_sources[route]
        raw = re.sub(r'<!-- Course attachment:.*?<!-- /Course attachment -->','',raw,flags=re.S)
        body = raw.split('<div class="doc">',1)[1].rsplit('</div></main>',1)[0]
        body = re.sub(r'<p class="catalog-footer">.*?</p>','',body,flags=re.S)
        body = re.sub(r'<p>Read alongside:.*?</p>', '<p>Review the lesson readings: <a href="../../'+l['route']+'">'+e(l['title'])+'</a>.</p>', body, flags=re.S)
        body = re.sub(r'href="../index.html#([^"]+)"',lambda match:'href="../../'+lessons[match[1]]['route']+'"' if match[1] in lessons else match[0],body)
        body = re.sub(r'href="../../phase-[^"/]+-prerequisites/[^" ]+"', 'href="../../'+readings[l['required'][0]]['route']+'"', body)
        body = body.replace('Later, value learners will still bootstrap at a nonterminal truncation; they won’t at true termination.', 'Later lessons explain why estimates of future rewards treat these boundaries differently.')
        body = body.replace('<section id="implement"', f'<nav class="course-actions"><button id="finish-browser" class="course-primary" hidden>Finish browser lab and continue to Python</button><a href="?lesson={l["id"]}&amp;step=python#implement">Next: Python practice</a></nav><section id="implement"')
        next_route=lesson_navigation_v2(course,l['id'])['afterLesson']
        next_label=next((n['title'] for n in course['lessons'] if n['route']==next_route),'F1 project application')
        body += f'<nav class="course-actions" aria-label="After Python practice"><a class="course-primary" href="../../{next_route}">Continue to {e(next_label)}</a><p>Python completion requires your explanation and confirmation of local checks. Browsing ahead remains available.</p></nav>'
        body = '\n'.join(line.rstrip() for line in body.splitlines())
        experiment_scripts = ''.join(f'<script type="module" src="{e(src,quote=True)}"></script>' for src in re.findall(r'<script[^>]+src="([^"]*experiments/[^"]+)"',raw))
        extra = '<link rel="stylesheet" href="../assets/labs.css">' + experiment_scripts + '<script type="module" src="../../assets/reading-lab.js"></script>'
        overlays[route] = page(route,l['title'],body,lesson=l['id'],extra=extra,lab=lab_id)
    return outputs, overlays


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args = parser.parse_args()
    outputs, overlays = render_outputs()
    outputs.update(overlays)
    stale = []
    for route, text in outputs.items():
        path = SITE / route
        if args.write:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(text,encoding='utf-8',newline='\n')
        elif not path.exists() or path.read_text(encoding='utf-8') != text:
            stale.append(route)
    if stale: raise SystemExit('Stale reading outputs: ' + ', '.join(stale))
    print(f'Active reading course verified: 134 readings, 27 lessons, 25 practice pairs; {len(outputs)} generated files.')


if __name__ == '__main__': main()
