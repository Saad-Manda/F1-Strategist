"""Static course contents, enhanced with current position and progress in the browser."""
from html import escape
import posixpath
import re
from course import load_course, reading_url, checkpoint_reading_url


def strip_outline(source):
    return re.sub(r'<!-- Course outline -->.*?<!-- /Course outline -->', '', source, flags=re.S)


def outline(route, course=None):
    course = course or load_course()
    resources = {r['id']: r for r in course['resources']}
    lessons = {l['id']: l for l in course['lessons']}
    current_lesson = next((l for l in course['lessons'] if route in (l['route'], l['lab'])), None)
    page = next((r for r in course['resources'] if r['route'] == route and r['kind'] == 'page'), None)
    current_module = next((m for m in course['modules'] if m['route'] == route or
                          (current_lesson and current_lesson['module'] == m['id']) or
                          (page and page['phase'] == m['phase'])), None)
    def anchor(target, text, cls='', **attrs):
        path = target.split('?')[0].split('#')[0]
        href = posixpath.relpath(path, posixpath.dirname(route) or '.') + target[len(path):]
        attributes = ''.join(f' {key.replace("_", "-")}="{escape(value, quote=True)}"' for key, value in attrs.items())
        return f'<a class="outline-link {cls}" href="{escape(href, quote=True)}"{attributes}>{text}</a>'
    result = ['<!-- Course outline --><aside id="course-outline" class="course-outline" aria-labelledby="course-outline-title">',
              '<div class="outline-intro"><div class="outline-heading"><h2 id="course-outline-title">Course contents</h2><button class="outline-close" type="button" hidden>Close contents</button></div>',
              '<p class="outline-location" role="status">Choose a module or lesson</p>',
              '<nav class="outline-global" aria-label="Course destinations">' + ''.join(anchor(path, title) for path, title in [('index.html','Home'),('roadmap.html','Roadmap'),('library.html','Library')]) + '</nav>',
              '</div><nav class="outline-tree" aria-label="Modules, lessons and steps">']
    for module in course['modules']:
        mid = module['id']; opened = bool(current_module and current_module['id'] == mid)
        result.append(f'<details class="outline-module" data-outline-module="{mid}"' + (' open' if opened else '') + '><summary>')
        result.append(anchor(module['route'], f'<span class="outline-number">{module["number"]}</span><span>{escape(module["title"])}<small>Project Phase {module["phase"]}</small></span><span class="outline-count" data-outline-count="{mid}"></span>', 'outline-module-link', data_outline_module_link=mid))
        result.append('<span class="outline-chevron" aria-hidden="true">›</span></summary><div class="outline-module-content">')
        for index, lid in enumerate(module['lessons'], 1):
            lesson = lessons[lid]; number = f'{module["number"]}.{index}'
            result.append(f'<details class="outline-lesson" data-outline-lesson="{lid}"' + (' open' if current_lesson and current_lesson['id'] == lid else '') + '><summary>')
            result.append(anchor(lesson['route']+'#theory', f'<span class="outline-number">{number}</span><span>{escape(lesson["title"])}<small data-outline-status="{lid}"></small></span>', 'outline-lesson-link', data_outline_lesson_link=lid))
            result.append('<span class="outline-chevron" aria-hidden="true">›</span></summary><div class="outline-steps">')
            for step, label, target in [('theory','Read theory',reading_url(resources[lesson['required'][0]],lid)), ('browser','Browser lab',lesson['lab']+f'?lesson={lid}&step=browser#challenge'), ('python','Python practice',lesson['lab']+f'?lesson={lid}&step=python#implement')]:
                result.append(anchor(target, escape(label)+'<span class="outline-check" aria-hidden="true"></span>', 'outline-step', data_outline_step=step, data_outline_owner=lid))
                if step == 'theory':
                    result.append('<div class="outline-readings">')
                    for key in lesson['required']:
                        resource = resources[key]
                        result.append(anchor(reading_url(resource,lid), escape(resource.get('heading') or resource['title'])+'<span class="outline-check" aria-hidden="true"></span>', 'outline-reading', data_outline_reading=key, data_outline_owner=lid))
                    result.append('</div>')
            result.append('</div></details>')
        result.append(anchor(module['projectCheckpoint']['route'], 'Project checkpoint<span class="outline-check" aria-hidden="true"></span>', 'outline-checkpoint', data_outline_checkpoint=mid))
        result.append('<div class="outline-bridges">')
        for key in module['projectCheckpoint']['required']:
            resource=resources[key]
            result.append(anchor(checkpoint_reading_url(resource,mid), escape(resource['title'])+'<span class="outline-check" aria-hidden="true"></span>', 'outline-reading', data_outline_bridge=key, data_outline_module_owner=mid))
        result.append('</div><details class="outline-reference"><summary>Reference readings</summary>')
        for resource in course['resources']:
            if resource['kind'] == 'page' and resource['phase'] == module['phase']:
                result.append(anchor(resource['route'], escape(resource['title']), 'outline-reading', data_outline_reference=resource['id']))
        result.append('</details></div></details>')
    result.append('</nav></aside><div class="course-drawer-backdrop" hidden></div><!-- /Course outline -->')
    return ''.join(result)
