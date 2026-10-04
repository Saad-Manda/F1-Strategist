import { resolveCourseContext, readingTarget } from './course-context.js?v=outline-20261004';
import { lessonProgress, moduleProgress, continueTarget } from './course-progress.js?v=outline-20261004';

export const stepNames = {theory:'Read theory',browser:'Browser lab',python:'Python practice'};
export function lessonNumber(course, id) {
  const lesson=course.lessons.find(l=>l.id===id), module=course.modules.find(m=>m.id===lesson?.module);
  return module ? `${module.number}.${module.lessons.indexOf(id)+1}` : null;
}
export function outlinePosition(course, route, search='', hash='') {
  const context=resolveCourseContext(course,route,search,hash);
  if(context)return {module:context.module.id,lesson:context.lesson?.id,step:context.step,
    reading:context.kind==='lesson'?context.resource?.id:undefined,
    bridge:context.kind==='checkpoint'?context.resource.id:undefined,checkpoint:context.kind==='checkpoint'};
  const lesson=course.lessons.find(l=>l.route===route||l.lab===route);
  if(lesson)return {module:lesson.module,lesson:lesson.id,
    step:['#theory','#browser','#python'].includes(hash)?hash.slice(1):lesson.lab===route?(['#implement','#reflect'].includes(hash)?'python':'browser'):'theory'};
  const module=course.modules.find(m=>m.route===route);
  if(module)return {module:module.id,checkpoint:hash==='#project-checkpoint'};
  const page=course.resources.find(r=>r.kind==='page'&&r.route===route);
  if(page)return {module:course.modules.find(m=>m.phase===page.phase)?.id,reference:page.id};
  return {};
}

export function mountCourseOutline(runtime) {
  const aside=document.querySelector('#course-outline');if(!aside)return;
  const {course,store,labs,root}=runtime;
  const route=decodeURIComponent(location.pathname).slice(root.pathname.length)||'index.html';
  const nav=document.querySelector('.course-nav'), toggle=nav?.querySelector('.course-menu');
  const close=aside.querySelector('.outline-close'), backdrop=document.querySelector('.course-drawer-backdrop');
  const mobile=window.matchMedia('(max-width:960px)');
  const main=document.querySelector('main');const originalInert=main?.inert;
  let opened=false,previousPosition;
  document.body.dataset.outlineEnhanced='';if(toggle)toggle.hidden=false;close.hidden=false;
  function drawer(value,returnFocus=true) {
    opened=value&&mobile.matches;
    document.body.classList.toggle('course-drawer-open',opened);backdrop.hidden=!opened;
    toggle?.setAttribute('aria-expanded',String(opened));
    if(main)main.inert=opened?true:originalInert;
    if(opened){aside.setAttribute('role','dialog');aside.setAttribute('aria-modal','true');requestAnimationFrame(()=>{if(opened)close.focus();});}
    else {aside.removeAttribute('role');aside.removeAttribute('aria-modal');if(returnFocus)toggle?.focus();}
  }
  toggle?.addEventListener('click',()=>drawer(!opened));close.addEventListener('click',()=>drawer(false));backdrop.addEventListener('click',()=>drawer(false));
  mobile.addEventListener('change',()=>{drawer(false,false);});
  document.addEventListener('keydown',event=>{
    if(!opened)return;
    if(event.key==='Escape'){event.preventDefault();drawer(false);}
    if(event.key==='Tab'){
      const focusable=[...aside.querySelectorAll('a[href],button,summary')].filter(element=>{
        if(element.hidden||!element.getClientRects().length)return false;
        for(let parent=element.parentElement;parent&&parent!==aside;parent=parent.parentElement)
          if(parent.tagName==='DETAILS'&&!parent.open&&!parent.firstElementChild.contains(element))return false;
        return true;
      });
      const first=focusable[0],last=focusable.at(-1);
      if(!aside.contains(document.activeElement)){event.preventDefault();first.focus();}
      else if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
    }
  });
  aside.addEventListener('click',event=>{if(opened&&event.target.closest('a'))drawer(false,false);});
  function done(link,value) {
    link.toggleAttribute('data-done',Boolean(value));const check=link.querySelector('.outline-check');
    if(check){check.textContent=value?'✓':'';check.setAttribute('aria-hidden',value?'false':'true');if(value)check.setAttribute('aria-label','Completed');else check.removeAttribute('aria-label');}
  }
  function current(link,value,kind='location') {
    link.toggleAttribute('data-current',Boolean(value));if(value)link.setAttribute('aria-current',kind);else link.removeAttribute('aria-current');
  }
  function render() {
    const data=store.data,position=outlinePosition(course,route,location.search,location.hash);
    let activeModule=position.module;
    if(!activeModule&&['index.html','roadmap.html','library.html'].includes(route))activeModule=continueTarget(course,data,labs).module;
    const module=course.modules.find(m=>m.id===activeModule), lesson=course.lessons.find(l=>l.id===position.lesson);
    for(const item of aside.querySelectorAll('[data-outline-module]')) {
      const id=item.dataset.outlineModule,state=moduleProgress(course,data,labs,id);
      item.toggleAttribute('data-current-parent',id===activeModule);
      aside.querySelector(`[data-outline-count="${id}"]`).textContent=`${state.completed}/${state.total}`;
    }
    for(const link of aside.querySelectorAll('[data-outline-module-link]'))current(link,course.modules.find(m=>m.id===link.dataset.outlineModuleLink).route===route&&!position.checkpoint,'page');
    for(const link of aside.querySelectorAll('[data-outline-lesson-link]')) {
      const id=link.dataset.outlineLessonLink,state=lessonProgress(course,data,labs,id);
      aside.querySelector(`[data-outline-status="${id}"]`).textContent=state.status==='Not started'?'':state.status;
      link.closest('details').toggleAttribute('data-current-parent',id===position.lesson);
      current(link,course.lessons.find(l=>l.id===id).route===route,'page');
    }
    for(const link of aside.querySelectorAll('[data-outline-step]')) {
      const id=link.dataset.outlineOwner,step=link.dataset.outlineStep,l=course.lessons.find(l=>l.id===id),state=lessonProgress(course,data,labs,id);
      if(step==='theory')link.href=new URL(readingTarget(course.resources.find(r=>r.id===(state.missing[0]||l.required[0])),id),root).href;
      done(link,step==='theory'?!state.missing.length:step==='browser'?state.browser:state.python);
      current(link,id===position.lesson&&step===position.step,'step');
    }
    for(const link of aside.querySelectorAll('[data-outline-reading]')) {
      done(link,data.readings.includes(link.dataset.outlineReading));
      current(link,link.dataset.outlineOwner===position.lesson&&link.dataset.outlineReading===position.reading);
    }
    for(const link of aside.querySelectorAll('[data-outline-checkpoint]')) {done(link,moduleProgress(course,data,labs,link.dataset.outlineCheckpoint).ready);current(link,link.dataset.outlineCheckpoint===position.module&&position.checkpoint&&!position.bridge);}
    for(const link of aside.querySelectorAll('[data-outline-bridge]')) {done(link,data.readings.includes(link.dataset.outlineBridge));current(link,link.dataset.outlineModuleOwner===position.module&&link.dataset.outlineBridge===position.bridge);}
    for(const link of aside.querySelectorAll('[data-outline-reference]'))current(link,link.dataset.outlineReference===position.reference,'page');
    for(const link of aside.querySelectorAll('.outline-global a'))current(link,new URL(link.href).pathname.slice(root.pathname.length)===route,'page');
    let label=module?`${module.number} · ${module.title}`:'Course';
    if(lesson)label+=` / ${lessonNumber(course,lesson.id)} · ${lesson.title} / ${stepNames[position.step]}`;
    if(position.reading&&lesson?.required.includes(position.reading))label+=` / Reading ${lesson.required.indexOf(position.reading)+1} of ${lesson.required.length}`;
    if(position.reference)label+=' / Reference reading';if(position.checkpoint)label+=' / Project checkpoint';
    if(!position.module)label=({'index.html':'Course home','roadmap.html':'Course roadmap','library.html':'Reference library'})[route]||'Course';
    aside.querySelector('.outline-location').textContent=label;
    const signature=JSON.stringify({activeModule,...position});
    if(signature!==previousPosition) {
      for(const item of aside.querySelectorAll('[data-outline-module]'))item.open=item.dataset.outlineModule===activeModule;
      for(const item of aside.querySelectorAll('[data-outline-lesson]'))item.open=item.dataset.outlineLesson===position.lesson;
      for(const item of aside.querySelectorAll('.outline-reference'))item.open=Boolean(position.reference&&item.closest('[data-outline-module]').dataset.outlineModule===position.module);
      const active=aside.querySelector('.outline-reading[data-current],.outline-step[data-current],.outline-checkpoint[data-current],.outline-module-link[data-current]');
      const tree=aside.querySelector('.outline-tree');
      if(active&&tree){const bounds=active.getBoundingClientRect(),viewport=tree.getBoundingClientRect();if(bounds.top<viewport.top||bounds.bottom>viewport.bottom)tree.scrollTop=Math.max(0,bounds.top-viewport.top+tree.scrollTop-80);}
      previousPosition=signature;
    }
  }
  store.subscribe(render);labs.subscribe(render);window.addEventListener('hashchange',render);render();
}
