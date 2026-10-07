import {createReadingSession} from './reading-store.js?v=reading-20261006-r8';
export const rootURL=new URL('../index.html',import.meta.url);
export const data=await fetch(new URL('course-reading-data.json?v=reading-20261006-r8',import.meta.url),{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('Course metadata unavailable. Reload this page.');return r.json();});
if(data.release!=='reading-20261006-r8' || data.course.schemaVersion!==2)throw new Error('Course assets changed. Reload this page before saving.');
let storage;
try {storage=localStorage;} catch {storage={getItem(){throw new Error('Storage unavailable');}};}
export const session=await createReadingSession({storage,locks:navigator.locks,data});
window.addEventListener('storage',event=>{
  if([null,'rl-course:v1','rl-course:v2','rl-labs:v1'].includes(event.key))session.refresh(event.key);
});
