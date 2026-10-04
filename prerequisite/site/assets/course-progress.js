import { validateProgress, PROGRESS_KEY } from '../labs/assets/storage.js?v=outline-20261004';
import { readingTarget } from './course-context.js?v=outline-20261004';
export const COURSE_KEY = 'rl-course:v1';
export const emptyCourse = () => ({version:1, readings:[], browser:[], checks:{}, resume:null});
const object = value => value && typeof value === 'object' && !Array.isArray(value);
function ids(value, allowed) {
  if (!Array.isArray(value) || value.some(id => typeof id !== 'string' || !allowed.includes(id)) || new Set(value).size !== value.length) throw new Error('Unknown or duplicate progress IDs.');
  return [...value];
}
export function validateCourseProgress(data, course) {
  if (!object(data) || data.version !== 1 || !object(data.checks)) throw new Error('Invalid course progress version or record.');
  const result = {version:1, readings:ids(data.readings, course.resources.map(r=>r.id)), browser:ids(data.browser, course.lessons.map(l=>l.id)), checks:{}, resume:null};
  for (const [id, values] of Object.entries(data.checks)) {
    const module = course.modules.find(m=>m.id===id);
    if (!module) throw new Error('Unknown checkpoint.');
    result.checks[id] = ids(values, module.projectCheckpoint.checks.map(c=>c.id));
  }
  if (data.resume !== null) {
    const r = data.resume;
    if (!object(r)) throw new Error('Invalid resume position.');
    if (r.kind === 'checkpoint' && course.modules.some(m=>m.id===r.module)) result.resume={kind:r.kind,module:r.module};
    else if (r.kind === 'lesson') {
      const lesson = course.lessons.find(l=>l.id===r.lesson);
      if (!lesson || !['theory','browser','python'].includes(r.step) || (r.resource !== undefined && (r.step !== 'theory' || !lesson.required.includes(r.resource)))) throw new Error('Invalid lesson resume position.');
      result.resume={kind:r.kind,lesson:r.lesson,step:r.step,...(r.resource ? {resource:r.resource}:{})};
    } else throw new Error('Invalid resume position.');
  }
  return result;
}
export function lessonProgress(course, data, labs, id) {
  const lesson = course.lessons.find(l=>l.id===id);
  const missing = lesson.required.filter(id=>!data.readings.includes(id));
  const browser = data.browser.includes(id), record = labs.get(id);
  const python = record.status === 'completed' && record.verified && Boolean(record.explanation.trim());
  const complete = !missing.length && browser && python;
  const started = lesson.required.some(id=>data.readings.includes(id)) || browser || record.status !== 'not-started';
  return {missing,browser,python,complete,status:complete?'Completed':started?'In progress':'Not started',step:missing.length?'theory':!browser?'browser':!python?'python':null};
}
export function moduleProgress(course, data, labs, id) {
  const module = course.modules.find(m=>m.id===id);
  const completed = module.lessons.filter(id=>lessonProgress(course,data,labs,id).complete).length;
  const missing = module.projectCheckpoint.required.filter(id=>!data.readings.includes(id));
  const checks = module.projectCheckpoint.checks.filter(c=>!(data.checks[id]||[]).includes(c.id));
  return {completed,total:module.lessons.length,learningComplete:completed===module.lessons.length,missing,checks,ready:completed===module.lessons.length&&!missing.length&&!checks.length};
}
export function continueTarget(course, data, labs, scope = null) {
  const resources = new Map(course.resources.map(r=>[r.id,r]));
  const modules = scope ? course.modules.filter(m=>m.id===scope) : course.modules;
  function checkpoint(module) { return {kind:'checkpoint',module:module.id,url:module.projectCheckpoint.route,label:module.projectCheckpoint.preparationLabel}; }
  function target(lesson, step, resource) {
    return {kind:'lesson',lesson:lesson.id,module:lesson.module,step,
      url:step==='theory'?readingTarget(resources.get(resource),lesson.id):`${lesson.lab}?lesson=${lesson.id}&step=${step}${step==='browser'?'#challenge':'#implement'}`,
      label:`${lesson.title} · ${step==='theory'?'Read theory':step==='browser'?'Browser lab':'Local Python and reflection'}`};
  }
  // A finished module's preparation must be completed before resuming a later module.
  const barrier = modules.find(m=>{const state=moduleProgress(course,data,labs,m.id);return state.learningComplete&&!state.ready;});
  const resume = data.resume;
  if (resume) {
    const lesson = course.lessons.find(l=>l.id===resume.lesson);
    const module = course.modules.find(m=>m.id===(lesson?.module||resume.module));
    if (module && modules.includes(module)) {
      if (barrier && course.modules.indexOf(module)>course.modules.indexOf(barrier)) return checkpoint(barrier);
      if (resume.kind==='checkpoint' && moduleProgress(course,data,labs,module.id).learningComplete && !moduleProgress(course,data,labs,module.id).ready) return checkpoint(module);
      if (lesson) {
        const state=lessonProgress(course,data,labs,lesson.id);
        if (resume.step==='theory' && state.missing.length) return target(lesson,'theory',state.missing.includes(resume.resource)?resume.resource:state.missing[0]);
        if (resume.step==='browser'&&!state.browser) return target(lesson,'browser');
        if (resume.step==='python'&&!state.python) return target(lesson,'python');
      }
    }
  }
  for (const module of modules) {
    for (const id of module.lessons) {
      const lesson=course.lessons.find(l=>l.id===id), state=lessonProgress(course,data,labs,id);
      if (!state.complete) return target(lesson,state.step,state.missing[0]);
    }
    if (!moduleProgress(course,data,labs,module.id).ready) return checkpoint(module);
  }
  return {kind:'review',url:scope?course.modules.find(m=>m.id===scope).route:'roadmap.html',label:scope?'Review module':'Review course'};
}
export function validateBundle(raw, course) {
  if (typeof raw !== 'string' || raw.length > 500000) throw new Error('Progress file is too large.');
  const value=JSON.parse(raw), known=course.lessons.map(l=>l.id);
  if (value?.format !== undefined || value?.course !== undefined) {
    if(value.format!=='rl-course-progress'||value.version!==1)throw new Error('Unsupported combined progress format or version.');
    return {course:validateCourseProgress(value.course,course),labs:validateProgress(value.labs,known)};
  }
  // Legacy exports preserve lab evidence and explicitly leave theory unacknowledged.
  return {course:emptyCourse(),labs:validateProgress(value,known)};
}
export function createCourseStore(course, suppliedStorage) {
  let storage, data=emptyCourse(), warning='', writable=true;
  const listeners=new Set();
  const emit=()=>{for(const listener of listeners)listener();};
  try {storage=suppliedStorage===undefined?window.localStorage:suppliedStorage;if(!storage)throw new Error();const raw=storage.getItem(COURSE_KEY);if(raw)data=validateCourseProgress(JSON.parse(raw),course);}
  catch {writable=false;warning='Saved course progress is unavailable or unreadable. Changes may last only on this page; export before leaving.';}
  function save(next) {
    data=validateCourseProgress(next,course);
    try {if(!storage||!writable)throw new Error();storage.setItem(COURSE_KEY,JSON.stringify(data));warning='';}
    catch {warning='Course progress is kept on this page only. Export before leaving; persistence between pages is unavailable.';}
    emit();
  }
  const api={
    get data(){return structuredClone(data);},get warning(){return warning;},
    subscribe(listener){listeners.add(listener);return()=>listeners.delete(listener);},
    acknowledge(id,done=true){save({...data,readings:done?[...new Set([...data.readings,id])]:data.readings.filter(key=>key!==id)});},
    browser(id,done=true){save({...data,browser:done?[...new Set([...data.browser,id])]:data.browser.filter(key=>key!==id)});},
    check(module,id,done){const values=data.checks[module]||[];save({...data,checks:{...data.checks,[module]:done?[...new Set([...values,id])]:values.filter(key=>key!==id)}});},
    visit(resume){if(JSON.stringify(data.resume)!==JSON.stringify(resume))save({...data,resume});},
    refresh(){try{data=validateCourseProgress(JSON.parse(storage.getItem(COURSE_KEY)||JSON.stringify(emptyCourse())),course);warning='';writable=true;}catch{writable=false;warning='Saved course progress is unreadable; current page progress retained.';}emit();},
    export(labs){return JSON.stringify({format:'rl-course-progress',version:1,course:data,labs:JSON.parse(labs.export())},null,2);},
    import(raw,labs){
      const incoming=validateBundle(raw,course); // Validate both records before touching either key.
      let previous;
      try {
        if(!storage)throw new Error('Storage unavailable');
        previous=[storage.getItem(PROGRESS_KEY),storage.getItem(COURSE_KEY)];
        storage.setItem(PROGRESS_KEY,JSON.stringify(incoming.labs));storage.setItem(COURSE_KEY,JSON.stringify(incoming.course));
      } catch {
        let restored=true;
        if(previous)for(const [i,key]of [PROGRESS_KEY,COURSE_KEY].entries())try{if(previous[i]===null)storage.removeItem(key);else storage.setItem(key,previous[i]);}catch{restored=false;}
        warning=restored?'Import could not be saved; existing progress retained.':'Import failed and storage rollback failed. Current page progress is retained; export it before leaving.';
        emit();throw new Error(warning);
      }
      data=incoming.course;warning='';writable=true;labs.replaceValidated(incoming.labs);emit();
    },
    resetLesson(id,labs){
      const lesson=course.lessons.find(l=>l.id===id);
      const exclusive=lesson.required.filter(key=>!course.lessons.some(other=>other.id!==id&&other.required.includes(key))&&!course.modules.some(m=>m.projectCheckpoint.required.includes(key)));
      const next={...data,readings:data.readings.filter(key=>!exclusive.includes(key)),browser:data.browser.filter(key=>key!==id),resume:data.resume?.lesson===id?null:data.resume};
      const labData=JSON.parse(labs.export());delete labData.labs[id];
      api.import(JSON.stringify({format:'rl-course-progress',version:1,course:next,labs:labData}),labs);
    },
    resetAll(labs){api.import(JSON.stringify({format:'rl-course-progress',version:1,course:emptyCourse(),labs:{version:1,labs:{}}}),labs);}
  };
  return api;
}
