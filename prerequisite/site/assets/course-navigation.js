import { resolveCourseContext, readingTarget } from './course-context.js?v=outline-20261004';
import { getCourseRuntime, contextProgress, recordContextVisit, mountCourseProgress } from './course-progress-ui.js?v=outline-20261004';
import { mountCourseOutline, lessonNumber } from './course-outline.js?v=outline-20261004';

const panel = document.querySelector('#course-context');
if (panel) {
  const root = new URL('../index.html', import.meta.url);
  root.pathname = root.pathname.slice(0, -'index.html'.length);
  try {
    const runtime = await getCourseRuntime();
    const course = runtime.course;
    const route = decodeURIComponent(location.pathname).slice(root.pathname.length);
    const defaultContent = [...panel.childNodes].map(node => node.cloneNode(true));
    const footer = document.querySelector('#course-forward');
    const defaultFooter = footer && [...footer.childNodes].map(node => node.cloneNode(true));
    const suppressed = [...document.querySelectorAll('.sidebar, .pagenav, .catalog-footer, section[aria-label="Practice this concept"]')]
      .map(node => [node, node.hidden]);
    const referenceLinks = [...document.querySelectorAll('.doc a[href]')].filter(node => !panel.contains(node))
      .map(node => [node, node.getAttribute('href')]);
    function element(tag, text, parent = panel) {
      const node = document.createElement(tag); node.textContent = text; parent.append(node); return node;
    }
    function anchor(target, label, parent = panel, primary = false) {
      const node = element('a', label, parent); node.href = new URL(target, root).href;
      node.className = primary ? 'course-primary' : 'course-link'; return node;
    }
    function renderContext(visit=false) {
      const context = resolveCourseContext(course, route, location.search, location.hash);
      if(visit&&context)recordContextVisit(runtime,context);
      suppressed.forEach(([node, hidden]) => { node.hidden = context ? true : hidden; });
      document.body.classList.toggle('course-guided', Boolean(context));
      panel.replaceChildren();
      footer?.replaceChildren();
      referenceLinks.forEach(([node, href]) => { node.setAttribute('href', href); });
      if (!context) {
        panel.append(...defaultContent.map(node => node.cloneNode(true)));
        if (footer) footer.append(...defaultFooter.map(node => node.cloneNode(true)));
        return;
      }
      if (context.lesson) {
        const allowed = new Set(context.lesson.required.concat(context.lesson.optional)
          .map(id => course.resources.find(r => r.id === id).route));
        for (const [node, href] of referenceLinks) {
          const target = new URL(href, location.href);
          if (target.origin !== root.origin || !target.pathname.startsWith(root.pathname)) continue;
          const targetRoute = decodeURIComponent(target.pathname).slice(root.pathname.length);
          if (allowed.has(targetRoute)) {
            target.search = new URLSearchParams({lesson:context.lesson.id, step:'theory'}).toString();
            node.href = target.href;
          } else if (targetRoute === context.lesson.lab && target.pathname !== location.pathname) {
            node.href = new URL(`${context.lesson.lab}?lesson=${context.lesson.id}&step=browser#challenge`, root).href;
          }
        }
      }
      const crumbs = element('p', '', panel); crumbs.className = 'course-breadcrumb';
      anchor('index.html', 'Course', crumbs); crumbs.append(' → ');
      anchor(context.module.route, context.module.number + ' · ' + context.module.title, crumbs);
      if (context.lesson) {
        crumbs.append(' → '); anchor(context.lesson.route, lessonNumber(course,context.lesson.id) + ' · ' + context.lesson.title, crumbs);
        crumbs.append(' → ' + ({theory:'Read theory', browser:'Browser lab', python:'Local Python and reflection'})[context.step]);
      } else crumbs.append(' → Project preparation');
      element('h2', context.kind === 'checkpoint' ? context.title : context.lesson.title);
      if (context.resource) element('p', context.resource.instruction);
      if (context.step === 'browser') element('p', 'Predict and investigate below. The theory in this lab is available for review. After your investigation, practice in local Python.');
      if (context.step === 'python') element('p', 'Python runs on your machine. Use the download and checks below, then record your reflection and local verification before continuing. Optional training is separate.');
      if (context.lesson && context.step !== 'theory') {
        const review = element('details', ''); element('summary', 'Review required theory', review);
        const list = element('ol', '', review);
        for (const id of context.lesson.required) {
          const resource = course.resources.find(r => r.id === id);
          anchor(readingTarget(resource, context.lesson.id), resource.title, element('li', '', list));
        }
      }
      anchor(context.next, context.nextLabel, panel, true);
      if (footer) {
        anchor(context.next, context.nextLabel, footer, true);
      }
      contextProgress(runtime,panel,context);
      if (context.step === 'python') element('p', 'Continue after completing the reflection and local checks below.');
    }
    renderContext(true);
    runtime.store.subscribe(()=>renderContext());
    runtime.labs.subscribe(()=>renderContext());
    window.addEventListener('hashchange', ()=>renderContext(true));
  } catch {
    // Failed metadata, malformed URLs, or offline browsing retain static reference links.
    const warning = document.createElement('p');
    warning.textContent = 'Course guidance could not load. Use the lesson and roadmap links above; reading and local Python downloads remain available.';
    panel.append(warning);
  }
}
try { const runtime=await mountCourseProgress();mountCourseOutline(runtime); }
catch {
  const main=document.querySelector('main');
  if(main){const warning=document.createElement('p');warning.textContent='Course progress could not load. Static navigation and local Python downloads remain available.';main.append(warning);}
}
