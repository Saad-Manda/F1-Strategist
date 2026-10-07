// Exercise shared controls with a DOM fixture; browser layout checks are separate.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createReadingSession} from '../site/assets/reading-store.js';
class Element {
 constructor(){this.hidden=true;this.value='';this.checked=false;this.textContent='';this.disabled=false;this.dataset={};this.events={};this.attributes={};}
 addEventListener(name,handler){this.events[name]=handler;} setAttribute(name,value){this.attributes[name]=value;}
 fire(name){assert.ok(this.events[name]);return this.events[name]({preventDefault(){},target:this});}
}
const memory=()=>{const saved=new Map();return {getItem:key=>saved.get(key)??null,setItem:(key,value)=>saved.set(key,value),removeItem:key=>saved.delete(key)};};
let sequence=0;
async function mount(storage,lab='p9-gae'){
 const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
 const hints=Array.from({length:3},()=>new Element()),radios=Array.from({length:3},(_,i)=>{const r=new Element();r.value=String(i);r.dataset.feedback='Compare the trace with your prediction.';return r;});
 globalThis.window={localStorage:storage};
 globalThis.document={body:{dataset:{labId:lab,lessonId:lab}},getElementById:get,querySelector:selector=>selector==='[name="prediction"]:checked'?radios.find(r=>r.checked):get(selector.slice(1)),querySelectorAll:selector=>selector==='[data-hint]'?hints:radios};
 const data=JSON.parse(await readFile(new URL('../site/assets/course-reading-data.json',import.meta.url),'utf8'));
 globalThis.qaSession=await createReadingSession({storage,locks:{request:async(name,opts,fn)=>fn()},data});
 const source=(await readFile(new URL('../site/assets/reading-lab.js',import.meta.url),'utf8')).replace(/^import .*?;\r?\n/,'const session=globalThis.qaSession;\n');
 await import('data:text/javascript;base64,'+Buffer.from(source+'\n// fixture '+sequence++).toString('base64'));

 return {get,hints,radios};
}
test('shared controls gate completion, restore requested help and distinguish resets',async()=>{
 const storage=memory();let {get,hints,radios}=await mount(storage);
 assert.ok(hints.every(h=>h.hidden));assert.equal(get('solution').hidden,true);
 await get('complete-lab').fire('click');assert.match(get('completion-feedback').textContent,/write your explanation/);
 radios[0].checked=true;await get('prediction-form').fire('submit');assert.equal(get('lab-progress').textContent,'Attempted');
 await get('next-hint').fire('click');await get('reveal-solution').fire('click');assert.equal(hints[0].hidden,false);assert.equal(hints[1].hidden,true);
 get('explanation').value='Final observations supply the nonterminal bootstrap; reset boundaries cut the trace.';await get('explanation').fire('input');
 get('verified').checked=true;await get('verified').fire('change');await get('complete-lab').fire('click');assert.equal(get('lab-progress').textContent,'Completed');
 ({get,hints}=await mount(storage));assert.equal(get('lab-progress').textContent,'Completed');assert.equal(hints[0].hidden,false);assert.equal(get('solution').hidden,false);
 get('verified').checked=false;await get('verified').fire('change');assert.equal(get('lab-progress').textContent,'Attempted');
 assert.match(get('completion-feedback').textContent,/Completion removed/);
 get('verified').checked=true;await get('verified').fire('change');await get('complete-lab').fire('click');
 get('explanation').value='';await get('explanation').fire('input');assert.equal(get('lab-progress').textContent,'Attempted');assert.match(get('completion-feedback').textContent,/Completion removed/);
 await get('reset-progress').fire('click');assert.equal(get('lab-progress').textContent,'Not started');assert.ok(hints.every(h=>h.hidden));assert.equal(get('solution').hidden,true);
});
test('blocked storage preserves data and disables verification',async()=>{
 const blocked={getItem(){throw Error('blocked');},setItem(){throw Error('blocked');}};
 const {get}=await mount(blocked);
 assert.match(get('saved-status').textContent,/could not be loaded/);
 assert.equal(get('complete-lab').disabled,true);
 get('explanation').value='QA explanation';get('verified').checked=true;
 await get('complete-lab').fire('click');assert.equal(get('lab-progress').textContent,'Not started');
});
