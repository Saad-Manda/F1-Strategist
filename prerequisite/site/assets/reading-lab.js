import {session} from './reading-session.js?v=reading-20261006-r8';
const id=document.body.dataset.labId;
const blank=()=>({attempts:0,prediction:'',explanation:'',status:'not-started',hints:0,solution:false,verified:false});
const get=()=>({...blank(),...session.bundle.labs.labs[id]});
const el=id=>document.getElementById(id);
const hints=[...document.querySelectorAll('[data-hint]')];
const feedback=el('completion-feedback');
let previousStatus=get().status;
function render() {
  const record=get();
  if(document.activeElement!==el('explanation')) el('explanation').value=record.explanation;
  el('verified').checked=record.verified;
  for(const input of document.querySelectorAll('[name="prediction"]')) input.checked=input.value===record.prediction;
  hints.forEach((hint,index)=>hint.hidden=index>=record.hints);
  el('next-hint').disabled=record.hints>=hints.length;
  el('next-hint').textContent=record.hints>=hints.length?'All hints shown':`Request hint ${record.hints+1} of ${hints.length}`;
  el('solution').hidden=!record.solution;
  el('reveal-solution').textContent=record.solution?'Hide explained solution':'Request explained solution';
  el('reveal-solution').setAttribute('aria-expanded',String(record.solution));
  el('lab-progress').textContent=record.status==='completed'?'Completed':record.status==='attempted'?'Attempted':'Not started';
  if(record.status!=='completed' && previousStatus==='completed') feedback.textContent='Completion removed. Restore your explanation and local-check confirmation before marking this lab complete again.';
  previousStatus=record.status;
  el('saved-status').textContent=session.warning || 'Course and lab progress saved in this browser.';
  for(const button of [el('finish-browser'),el('complete-lab'),el('reset-progress'),el('verified')])button.disabled=!session.writable;
}
async function patch(change) {
  try {await session.update(bundle=>{bundle.labs.labs[id]=change({...blank(),...bundle.labs.labs[id]});return bundle;});return true;}
  catch {render();return false;}
}
el('prediction-form').addEventListener('submit',async event=>{
  event.preventDefault();const selected=document.querySelector('[name="prediction"]:checked');
  if(!selected) {el('prediction-feedback').textContent='Choose a prediction first.';return;}
  const value=selected.value;
  if(await patch(r=>({...r,prediction:value,attempts:r.attempts+1,status:r.status==='completed'?'completed':'attempted'}))) el('prediction-feedback').textContent='Prediction saved. Run the experiment and compare the observed result with your prediction.';
});
el('next-hint').addEventListener('click',()=>patch(r=>({...r,hints:Math.min(hints.length,r.hints+1)})));
el('reveal-solution').addEventListener('click',()=>patch(r=>({...r,solution:!r.solution})));
function reflection() {
  const explanation=el('explanation').value,verified=el('verified').checked;
  return patch(r=>({...r,explanation,verified,status:r.status==='completed' && (!verified || !explanation.trim())?'attempted':r.status}));
}
el('explanation').addEventListener('input',reflection);el('verified').addEventListener('change',reflection);
el('complete-lab').addEventListener('click',async()=>{
  const explanation=el('explanation').value,verified=el('verified').checked;
  if(!verified || !explanation.trim()) {feedback.textContent='Confirm your local checks and write your explanation before marking this lab complete.';return;}
  try {await session.update(bundle=>{bundle.labs.labs[id]={...blank(),...bundle.labs.labs[id],explanation,verified,status:'completed'};bundle.course.resume={kind:'lesson',lesson:document.body.dataset.lessonId,step:'python'};return bundle;});feedback.textContent='Completed. Your explanation and local verification are recorded. Use Continue below to open the next lesson or project application.';}catch{render();}
});
const browser=el('finish-browser');
browser.hidden=false;
browser.addEventListener('click',async()=>{
  try {await session.update(bundle=>{if(!bundle.course.browser.includes(id)) bundle.course.browser.push(id);bundle.course.resume={kind:'lesson',lesson:document.body.dataset.lessonId,step:'python'};return bundle;});location.assign('?lesson='+document.body.dataset.lessonId+'&step=python#implement');} catch {render();}
});
el('export-progress').addEventListener('click',()=>el('reading-export').click());
el('import-progress').addEventListener('change',async event=>{
  const file=event.target.files[0];if(!file)return;
  try {if(file.size>1000000)throw new Error('Progress file is too large.');const raw=await file.text();if(!confirm('Replace course and lab progress with this file? Close or reload older course tabs before continuing.'))return;await session.import(raw);render();}
  catch(error) {el('saved-status').textContent='Import failed; existing progress retained. '+error.message;}
  event.target.value='';
});
el('reset-progress').addEventListener('click',async()=>{
  try {await session.update(bundle=>{delete bundle.labs.labs[id];bundle.course.browser=bundle.course.browser.filter(key=>key!==id);return bundle;});feedback.textContent='';} catch {render();}
});
for(const key of ['learning-controls','help-controls','reflection-controls','progress-tools'])el(key).hidden=false;
session.subscribe(render);render();
