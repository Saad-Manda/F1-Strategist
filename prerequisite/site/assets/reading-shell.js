import {session,data,rootURL} from './reading-session.js?v=reading-20261006-r8';
import {courseContinue,moduleReady,acknowledgeReading} from './reading-navigation.js?v=reading-20261006-r8';
import {MIGRATION_MESSAGE,migrationNoticeSeen} from './course-progress-v2.js?v=reading-20261006-r8';
const course=data.course;
const lesson=course.lessons.find(l => l.id===document.body.dataset.lessonId);
const module=course.modules.find(m=>m.id===document.body.dataset.moduleId);
const reading=document.body.dataset.readingId;
const readingData=course.readings.find(r=>r.id===reading);
const status=document.querySelector('#reading-status');
const finish=document.querySelector('#finish-reading');
function render() {
  const completed=session.bundle.course.readings;
  const total=document.querySelector('[data-course-count]');
  if(total)total.textContent=`${completed.filter(id=>course.readings.find(r=>r.id===id)?.role!=='further-depth').length} of ${course.readings.filter(r=>r.role!=='further-depth').length} required readings acknowledged · ${session.bundle.course.browser.length} of 25 browser labs · ${Object.values(session.bundle.labs.labs).filter(l=>l.status==='completed').length} of 25 Python practices verified`;
  for(const el of document.querySelectorAll('[data-catalog-lab]'))el.textContent=session.bundle.labs.labs[el.dataset.catalogLab]?.status==='completed'?'Python practice verified':'Python practice not yet verified';
  const notice=document.querySelector('#migration-notice');
  notice.hidden=!session.pendingMigration && !session.bundle.course.migration?.noticePending;
  document.querySelector('#migration-message').textContent=MIGRATION_MESSAGE+(session.pendingMigration?' Close or reload every older course tab before retaining progress; those tabs use the old saving protocol.':'');
  document.querySelector('#activate-migration').hidden=!session.pendingMigration;
  document.querySelector('#acknowledge-migration').hidden=session.pendingMigration || !session.bundle.course.migration?.noticePending;
  document.querySelector('#recovery-export').hidden=!session.warning;
  if(finish)finish.disabled=!session.writable;
  for(const el of document.querySelectorAll('[data-reading-status]')) el.textContent=completed.includes(el.dataset.readingStatus)?' ✓ Completed':'';
  for(const el of document.querySelectorAll('[data-lesson-count]')) el.textContent=`${lesson.required.filter(id=>completed.includes(id)).length} of ${lesson.required.length} required readings completed`;
  for(const el of document.querySelectorAll('[data-application-count]')) el.textContent=`${module.applications.filter(id=>completed.includes(id)).length} of ${module.applications.length} application readings completed`;
  if(finish) finish.textContent=completed.includes(reading)?'Continue':'Finish reading and continue';
  status.textContent=session.warning || (readingData?.role==='further-depth'?'Optional depth does not gate lesson or module completion.':reading ? 'Completion is saved only when you choose Finish reading and continue.' : 'Reading completion and practice completion are recorded separately.');
  for(const input of document.querySelectorAll('[data-check]')) {
    input.disabled=!session.writable;
    input.checked=(session.bundle.course.checks[module.id]||[]).includes(input.dataset.check);
  }
  const readiness=document.querySelector('[data-checkpoint-status]');
  if(readiness && module) readiness.textContent=moduleReady(course,session.bundle,module.id)?'Preparation complete: required learning, practice, application and checklist acknowledged. Production implementation still needs its own verification.':'Preparation in progress: required readings, browser labs, verified Python practice, application readings and all checklist items are tracked separately.';
  if(document.body.dataset.labId) {
    const step=new URLSearchParams(location.search).get('step')==='python'?'python':'browser';
    for(const a of document.querySelectorAll('[data-practice-step]')) {
      const active=a.dataset.practiceOwner===lesson.id && a.dataset.practiceStep===step;
      a.toggleAttribute('data-current',active);
      if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');
    }
  }
  const home=document.querySelector('[data-home-continue]');
  if(home) {
    const next=courseContinue(course,session.bundle);
    home.href=new URL(next.url,rootURL).href;home.textContent=next.label;
  }
}
for(const input of document.querySelectorAll('[data-check]')) input.addEventListener('change',async()=>{
  const checked=input.checked,id=input.dataset.check;
  input.disabled=true;
  try {await session.update(bundle=>{const values=new Set(bundle.course.checks[module.id]||[]);if(checked)values.add(id);else values.delete(id);bundle.course.checks[module.id]=[...values];bundle.course.resume={kind:'checkpoint',module:module.id};return bundle;});}
  catch {render();} finally {render();}
});
if(finish) {
  finish.hidden=false;
  finish.addEventListener('click',async()=>{
    finish.disabled=true;
    try {await session.update(bundle=>acknowledgeReading(course,bundle,reading)); location.assign(finish.dataset.next);}
    catch {render();} finally {render();}
  });
}
const exportButton=document.querySelector('#reading-export');
exportButton.hidden=false;
function download(raw,name){const url=URL.createObjectURL(new Blob([raw],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
exportButton.addEventListener('click',()=>download(session.export(),'rl-course-progress.json'));
document.querySelector('#recovery-export').addEventListener('click',()=>download(session.recoveryExport(),'rl-course-original-recovery.json'));
document.querySelector('#activate-migration').addEventListener('click',async()=>{try{await session.activateMigration();}catch{render();}});
document.querySelector('#acknowledge-migration').addEventListener('click',async()=>{try{await session.update(b=>{b.course=migrationNoticeSeen(b.course,course);return b;});}catch{render();}});
document.querySelector('#reading-import-label').hidden=false;
document.querySelector('#reading-import').addEventListener('change',async event=>{
  const file=event.target.files[0];if(!file)return;
  try{
    if(file.size>1000000)throw new Error('Progress file is too large.');
    const raw=await file.text();
    if(!confirm('Replace current course and lab progress with this file? Close or reload older course tabs before continuing.'))return;
    await session.import(raw);
  }catch(error){status.textContent='Import failed; existing progress retained. '+error.message;}
  finally{event.target.value='';}
});
session.subscribe(render);render();

const drawer=document.querySelector('#course-outline'),toggle=document.querySelector('#contents-toggle'),close=document.querySelector('.outline-close'),backdrop=document.querySelector('#reading-backdrop'),main=document.querySelector('main');
const mobile=matchMedia('(max-width:960px)');
document.body.dataset.outlineEnhanced='';toggle.hidden=false;close.hidden=false;
let priorFocus;
function setDrawer(open) {
  if(open) priorFocus=document.activeElement;
  document.body.classList.toggle('course-drawer-open',open);
  toggle.setAttribute('aria-expanded',String(open));
  backdrop.hidden=!open;main.inert=open;
  drawer.setAttribute('aria-modal',String(open));
  if(open) {drawer.setAttribute('role','dialog');close.focus();}
  else {drawer.removeAttribute('role');drawer.removeAttribute('aria-modal');if(priorFocus?.isConnected) priorFocus.focus();}
}
toggle.addEventListener('click',()=>setDrawer(!document.body.classList.contains('course-drawer-open')));
close.addEventListener('click',()=>setDrawer(false));backdrop.addEventListener('click',()=>setDrawer(false));
mobile.addEventListener('change',()=>setDrawer(false));
drawer.addEventListener('keydown',event=>{
  if(!mobile.matches || !document.body.classList.contains('course-drawer-open'))return;
  if(event.key==='Escape') {event.preventDefault();setDrawer(false);}
  if(event.key==='Tab') {
    const nodes=[...drawer.querySelectorAll('button,a[href],summary')].filter(el=>{
      if(!el.getClientRects().length)return false;
      // Closed details can retain layout boxes; their descendants cannot take focus.
      for(let parent=el.parentElement;parent && parent!==drawer;parent=parent.parentElement) {
        if(parent.tagName==='DETAILS' && !parent.open && el!==parent.firstElementChild)return false;
      }
      return true;
    });
    const first=nodes[0],last=nodes.at(-1);
    if(event.shiftKey && document.activeElement===first) {event.preventDefault();last.focus();}
    else if(!event.shiftKey && document.activeElement===last) {event.preventDefault();first.focus();}
  }
});
