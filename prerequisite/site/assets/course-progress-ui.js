import { getSharedProgressStore } from '../labs/assets/storage.js?v=outline-20261004';
import { createCourseStore, lessonProgress, moduleProgress, continueTarget, COURSE_KEY } from './course-progress.js?v=outline-20261004';
import { readingTarget } from './course-context.js?v=outline-20261004';
let loading;
export function getCourseRuntime() {
  return loading ||= (async()=>{
    const response=await fetch(new URL('./course-registry.json',import.meta.url));
    if(!response.ok)throw new Error('Course metadata unavailable');
    const course=await response.json();
    const labs=getSharedProgressStore(course.lessons.map(l=>l.id));
    const store=createCourseStore(course);
    const root=new URL('../index.html',import.meta.url);root.pathname=root.pathname.slice(0,-'index.html'.length);
    return {course,labs,store,root};
  })();
}
function node(tag,text,parent) {const value=document.createElement(tag);value.textContent=text;parent.append(value);return value;}
function button(label,parent,run){const value=node('button',label,parent);value.type='button';value.addEventListener('click',run);return value;}
function destination(anchor,url,label,root){anchor.href=new URL(url,root).href;anchor.textContent=label;}
export function recordContextVisit(runtime,context) {
  const {store}=runtime;
  if(context.kind==='checkpoint')store.visit({kind:'checkpoint',module:context.module.id});
  else store.visit({kind:'lesson',lesson:context.lesson.id,step:context.step,...(context.step==='theory'&&context.lesson.required.includes(context.resource?.id)?{resource:context.resource.id}:{})});
}
export function contextProgress(runtime,panel,context) {
  const {store,labs,course}=runtime, data=store.data;
  const controls=node('div','',panel);controls.className='course-acknowledgments';
  if(context.resource) {
    const done=data.readings.includes(context.resource.id);
    node('p',done?'Reading acknowledged · Already read':'Reading acknowledgment pending',controls);
    button(done?'Mark this reading not done':'Mark this reading done',controls,()=>store.acknowledge(context.resource.id,!done));
  }
  if(context.step==='browser') {
    const done=data.browser.includes(context.lesson.id);
    node('p',done?'Browser practice acknowledged':'Acknowledge after making your prediction and investigating the experiment.',controls);
    button(done?'Revoke browser acknowledgment':'Mark browser practice done',controls,()=>store.browser(context.lesson.id,!done));
  }
  if(context.lesson) {
    const state=lessonProgress(course,data,labs,context.lesson.id);
    node('p',`${state.status} · Theory ${state.missing.length?'pending':'acknowledged'} · Browser ${state.browser?'acknowledged':'pending'} · Python ${state.python?'verified':'pending'}`,controls);
    if(state.python&&(state.missing.length||!state.browser))node('p','Your completed lab work is preserved. Theory and browser acknowledgments remain outstanding.',controls);
  }
}
export async function mountCourseProgress() {
  const runtime=await getCourseRuntime(),{course,labs,store,root}=runtime;
  const route=decodeURIComponent(location.pathname).slice(root.pathname.length);
  const lesson=course.lessons.find(l=>l.route===route);
  const module=course.modules.find(m=>m.route===route);
  const main=document.querySelector('main');
  if(!main)return;
  const content=main.querySelector('.doc')||main;
  const tools=node('section','',content);tools.className='course-progress-tools';tools.setAttribute('aria-label','Course progress');
  node('h2','Your course progress',tools);
  const status=node('p','',tools);status.setAttribute('role','status');
  const feedback=node('p','',tools);feedback.setAttribute('role','status');
  const exportButton=button('Export course and lab progress',tools,()=>{
    const url=URL.createObjectURL(new Blob([store.export(labs)],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download='rl-course-progress.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  const label=node('label','Import course or legacy lab progress (replaces saved records)',tools);
  const input=node('input','',label);input.type='file';input.accept='.json,application/json';
  input.addEventListener('change',async()=>{
    const file=input.files[0];if(!file)return;
    try{if(file.size>500000)throw new Error('Progress file is too large.');store.import(await file.text(),labs);feedback.textContent='Imported course and lab progress.';}
    catch(error){feedback.textContent=`Import failed. ${error.message}`;}
    input.value='';
  });
  const reset=node('details','',tools);node('summary','Reset all course progress',reset);
  node('p','Clears every reading/browser acknowledgment, transfer checklist, and all 25 labs’ predictions, hints, solutions, reflections and verification. Other browser data stays intact.',reset);
  const resetButton=button('Reset all course and lab progress',reset,()=>{
    confirmation.hidden=false;cancelReset.focus();
  });
  const confirmation=node('div','',reset);confirmation.hidden=true;
  confirmation.setAttribute('role','group');confirmation.setAttribute('aria-labelledby','course-reset-confirmation');
  const confirmationTitle=node('h3','Confirm reset of all course and lab progress',confirmation);confirmationTitle.id='course-reset-confirmation';
  node('p','This clears readings, browser acknowledgments, transfer checklists, and all 25 labs’ predictions, hints, solutions, reflections and verification. Export first if you want a backup.',confirmation);
  const cancelReset=button('Cancel reset · keep progress',confirmation,()=>{confirmation.hidden=true;resetButton.focus();});
  button('Confirm reset all course and lab progress',confirmation,()=>{
    try{store.resetAll(labs);confirmation.hidden=true;resetButton.focus();feedback.textContent='All course and lab progress reset.';}catch(error){feedback.textContent=error.message;}
  });
  const lessonId=lesson?.id||document.body.dataset.labId;
  if(lessonId&&course.lessons.some(l=>l.id===lessonId)) {
    const resetLesson=node('details','',tools);node('summary','Reset this lesson',resetLesson);
    node('p','Clears this lesson’s browser acknowledgment, exclusive required readings, and lab prediction/help/reflection/verification. Shared readings, other lessons and project checklists are kept. Reset experiment changes only the experiment.',resetLesson);
    button('Reset this lesson’s course and lab progress',resetLesson,()=>{
      try{store.resetLesson(lessonId,labs);feedback.textContent='This lesson reset. Shared reading acknowledgments and other lessons kept.';}catch(error){feedback.textContent=error.message;}
    });
  }
  let summary;
  if(lesson||module){summary=node('p','',content);summary.className='course-progress-summary';main.querySelector('h1')?.after(summary);}
  const checkpoint=module&&document.querySelector('#project-checkpoint');
  const checklist=checkpoint&&node('div','',checkpoint);
  const requiredList=lesson&&document.querySelector('#theory .course-readings');
  let assigned,alreadyRead,readList,readingNote;
  if(requiredList) {
    assigned=[...requiredList.children];alreadyRead=document.createElement('details');
    node('summary','Already read · review as needed',alreadyRead);readList=node('ol','',alreadyRead);readList.className='course-readings';
    requiredList.previousElementSibling.before(alreadyRead);
    readingNote=document.createElement('p');requiredList.after(readingNote);
  }
  function render() {
    const data=store.data;
    const completed=course.lessons.filter(l=>lessonProgress(course,data,labs,l.id).complete).length;
    status.textContent=store.warning||labs.warning||`${completed} of ${course.lessons.length} lessons completed. Progress stays in this browser; export before changing browsers or hosting origins.`;
    for(const item of document.querySelectorAll('[data-course-lesson-state]')) {
      const state=lessonProgress(course,data,labs,item.dataset.courseLessonState);
      let badge=item.querySelector('[data-lesson-status]');if(!badge){badge=node('span','',item);badge.dataset.lessonStatus='';badge.className='course-meta';}
      badge.textContent=state.status;
    }
    for(const item of document.querySelectorAll('[data-course-module-state]')) {
      const state=moduleProgress(course,data,labs,item.dataset.courseModuleState);
      let badge=item.querySelector('[data-module-status]');if(!badge){badge=node('p','',item);badge.dataset.moduleStatus='';badge.className='course-meta';}
      badge.textContent=`${state.completed} of ${state.total} lessons completed · ${state.ready?'Project checkpoint acknowledged':state.learningComplete?'Project preparation pending':'Module learning pending'}`;
    }
    for(const item of document.querySelectorAll('[data-reading-id]')) {
      let badge=item.querySelector('[data-reading-status]');if(!badge){badge=node('span','',item);badge.dataset.readingStatus='';badge.className='course-meta';}
      badge.textContent=data.readings.includes(item.dataset.readingId)?'Already read':'Reading acknowledgment pending';
    }
    const target=continueTarget(course,data,labs), home=document.querySelector('.course-start[aria-label="Start learning"]');
    if(home) {
      const touched=data.resume||data.readings.length||data.browser.length||Object.keys(data.checks).length||Object.keys(JSON.parse(labs.export()).labs).length;
      destination(home.querySelector('a'),touched?target.url:course.lessons[0].route+'#theory',target.kind==='review'?'Review course':touched?'Continue learning':'Start learning',root);
      home.querySelector('p').textContent=`${completed} of ${course.lessons.length} lessons completed · ${course.modules.find(m=>m.id===target.module)?.title||'Course review'} · ${target.label}`;
    }
    if(lesson) {
      const state=lessonProgress(course,data,labs,lesson.id);
      summary.textContent=`${state.status} · Theory ${state.missing.length?'pending':'acknowledged'} · Browser ${state.browser?'acknowledged':'pending'} · Python ${state.python?'verified':'pending'}`;
      if(state.python&&!state.complete)summary.textContent+=' · Existing lab completion is preserved; course acknowledgments are still needed.';
      const index=course.lessons.indexOf(lesson),m=course.modules.find(m=>m.id===lesson.module);
      let url,label;
      if(state.missing.length){const r=course.resources.find(r=>r.id===state.missing[0]);url=readingTarget(r,lesson.id);label='Read theory: '+r.title;}
      else if(!state.browser){url=`${lesson.lab}?lesson=${lesson.id}&step=browser#challenge`;label='Open browser lab';}
      else if(!state.python){url=`${lesson.lab}?lesson=${lesson.id}&step=python#implement`;label='Practice in Python';}
      else {url=lesson.id===m.lessons.at(-1)?m.projectCheckpoint.route:course.lessons[index+1].route+'#theory';label=lesson.id===m.lessons.at(-1)?m.projectCheckpoint.preparationLabel:'Read next lesson’s theory: '+course.lessons[index+1].title;}
      destination(document.querySelector('.course-primary'),url,label,root);
      if(assigned) {
        for(const item of assigned)(data.readings.includes(item.dataset.readingId)?readList:requiredList).append(item);
        alreadyRead.hidden=!readList.children.length;
        readingNote.textContent=state.missing.length?'Acknowledge each required reading explicitly; opening or scrolling a page does not mark it done.':'All required theory is acknowledged. You can review it under Already read.';
      }
    }
    if(module) {
      const state=moduleProgress(course,data,labs,module.id),next=continueTarget(course,data,labs,module.id);
      summary.textContent=`${state.completed} of ${state.total} lessons completed · ${state.ready?module.projectCheckpoint.title:state.learningComplete?'Project preparation pending':'Module learning pending'}`;
      destination(document.querySelector('.course-primary'),next.url,next.kind==='review'?'Review module':'Continue module · '+next.label,root);
      checklist.replaceChildren();node('h3','Acknowledge project transfer',checklist);
      for(const check of module.projectCheckpoint.checks) {
        const label=node('label','',checklist),input=node('input','',label);input.type='checkbox';input.checked=(data.checks[module.id]||[]).includes(check.id);
        label.append(' '+check.text);input.addEventListener('change',()=>store.check(module.id,check.id,input.checked));
      }
      node('p',state.ready?'Prerequisite checkpoint acknowledged. Implement this project phase locally; course readiness does not certify production implementation.':'Finish all lessons, project bridge readings, and transfer checks to acknowledge readiness.',checklist);
    }
  }
  // Reference browsing never updates the guided resume pointer.
  if(lesson) {
    const step=['theory','browser','python'].includes(location.hash.slice(1))?location.hash.slice(1):'theory';
    store.visit({kind:'lesson',lesson:lesson.id,step});
    window.addEventListener('hashchange',()=>{const step=location.hash.slice(1);if(['theory','browser','python'].includes(step))store.visit({kind:'lesson',lesson:lesson.id,step});});
  } else if(module&&location.hash==='#project-checkpoint')store.visit({kind:'checkpoint',module:module.id});
  store.subscribe(render);labs.subscribe(render);render();
  window.addEventListener('storage',event=>{if(event.key===COURSE_KEY||event.key==='rl-labs:v1'||event.key===null){store.refresh();labs.refresh();}});
  return runtime;
}
