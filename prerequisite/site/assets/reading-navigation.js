// Availability is a preview boundary; prerequisites never lock authored pages.
import {unfinishedStep} from './course-progress-v2.js?v=reading-20261006-r8';
export function moduleReady(course,bundle,moduleId) {
  const m=course.modules.find(m=>m.id===moduleId);
  return m.lessons.every(id=>{
    const l=course.lessons.find(l=>l.id===id);
    return l.required.every(r=>bundle.course.readings.includes(r)) && (!l.practice ||
      (bundle.course.browser.includes(l.practice.labId) && bundle.labs.labs[l.practice.labId]?.status==='completed'));
  }) && m.applications.every(id=>bundle.course.readings.includes(id)) &&
    m.projectCheckpoint.checks.every(c=>(bundle.course.checks[m.id]||[]).includes(c.id));
}
export function previewContinue(course,bundle) {
  const readings=new Map(course.readings.map(r=>[r.id,r]));
  // A reviewed migration or explicit guided acknowledgment can resume within a
  // surviving lesson/module. Optional reference visits never become this pointer.
  const resume=bundle.course.resume;
  if(resume && course.readings.every(r=>r.status==='authored')) {
    const r=resume.kind==='reading' && readings.get(resume.reading);
    const lessonId=resume.kind==='lesson'?resume.lesson:r?.role!=='further-depth'?r?.lesson:null;
    const moduleId=resume.kind==='checkpoint'?resume.module:r?.role==='application'?r.module:null;
    if(lessonId || moduleId) {
      const next=unfinishedStep(course,bundle.course,bundle.labs,{lessonId:lessonId||null,moduleId:moduleId||null});
      if(next.kind==='reading')return {url:next.url,label:'Continue: '+readings.get(next.reading).title};
      if(next.kind==='lesson')return {url:next.url,label:'Continue: '+(next.step==='browser'?'Browser lab':'Python practice')+' · '+course.lessons.find(l=>l.id===next.lesson).title};
      if(next.kind==='checkpoint')return {url:next.url,label:'Continue: Project preparation checkpoint'};
    }
  }
  for(const m of course.modules) {
    for(const id of m.lessons) {
      const l=course.lessons.find(l=>l.id===id);
      if(!l.required.every(id=>readings.get(id).status==='authored'))
        return {url:'roadmap.html',label:'Review roadmap · Later modules are planned'};
      const missing=l.required.find(id=>!bundle.course.readings.includes(id));
      if(missing)return {url:readings.get(missing).route,label:'Continue: '+readings.get(missing).title};
      if(l.practice) {
        const browser=!bundle.course.browser.includes(l.practice.labId);
        if(browser || bundle.labs.labs[l.practice.labId]?.status!=='completed')
          return {url:l.practice.route+`?lesson=${l.id}&step=${browser?'browser#challenge':'python#implement'}`,label:'Continue: '+(browser?'Browser lab':'Python practice')+' · '+l.title};
      }
    }
    for(const id of m.applications) {
      const r=readings.get(id);
      if(r.status!=='authored')return {url:m.route,label:'Review module · Application is planned'};
      if(!bundle.course.readings.includes(id))return {url:r.route,label:'Continue: '+r.title};
    }
    if(!m.projectCheckpoint.checks.every(c=>(bundle.course.checks[m.id]||[]).includes(c.id)))
      return {url:m.projectCheckpoint.route,label:'Continue: Project preparation checkpoint'};
    // A completed available module hands off to its project work before planned lessons.
    const next=course.modules[course.modules.indexOf(m)+1];
    if(next && !course.lessons.find(l=>l.id===next.lessons[0]).required.every(id=>readings.get(id).status==='authored'))
      return projectHandoff(course,m.id);
  }
  return {url:'roadmap.html',label:'Review completed course'};
}
export const courseContinue=previewContinue;
export function acknowledgeReading(course,bundle,id) {
  const reading=course.readings.find(r=>r.id===id && r.status==='authored');
  if(!reading)throw new Error('Unknown authored reading.');
  if(!bundle.course.readings.includes(id))bundle.course.readings.push(id);
  if(reading.role!=='further-depth')bundle.course.resume={kind:'reading',reading:id};
  return bundle;
}
export function projectHandoff(course,moduleId) {
  const module=course.modules.find(m=>m.id===moduleId);
  const index=course.projectStages.findIndex(s=>s.module===moduleId);
  const next=course.projectStages[index+1];
  return {url:next?'roadmap.html#phase-'+next.phase:'roadmap.html',label:'Continue: '+(next?next.title:'Project roadmap')+' · '+module.title+' preparation complete'};
}
