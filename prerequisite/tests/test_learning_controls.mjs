// Exercise shared controls with a DOM fixture; browser layout checks are separate.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
class Element {
 constructor(){this.hidden=true;this.value='';this.checked=false;this.textContent='';this.disabled=false;this.dataset={};this.events={};this.attributes={};}
 addEventListener(name,handler){this.events[name]=handler;} setAttribute(name,value){this.attributes[name]=value;}
 fire(name){assert.ok(this.events[name]);return this.events[name]({preventDefault(){},target:this});}
}
const memory=()=>{let saved=null;return {getItem:()=>saved,setItem:(key,value)=>{saved=value;}};};
let sequence=0;
async function mount(storage,lab='p9-gae'){
 const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
 const hints=Array.from({length:3},()=>new Element()),radios=Array.from({length:3},(_,i)=>{const r=new Element();r.value=String(i);r.dataset.feedback='Compare the trace with your prediction.';return r;});
 globalThis.window={localStorage:storage};
 globalThis.document={body:{dataset:{labId:lab}},getElementById:get,querySelector:selector=>selector==='input[name="prediction"]:checked'?radios.find(r=>r.checked):get(selector.slice(1)),querySelectorAll:selector=>selector==='[data-hint]'?hints:radios};
 globalThis.fetch=async()=>({ok:true,json:async()=>JSON.parse(await readFile(new URL('../site/labs/assets/lab-registry.json',import.meta.url),'utf8'))});
 await import(`../site/labs/assets/lab-shell.js?qa=${sequence++}`);
 return {get,hints,radios};
}
test('shared controls gate completion, restore requested help and distinguish resets',async()=>{
 const storage=memory();let {get,hints,radios}=await mount(storage);
 assert.ok(hints.every(h=>h.hidden));assert.equal(get('solution').hidden,true);
 get('complete-lab').fire('click');assert.match(get('completion-feedback').textContent,/write your explanation/);
 radios[0].checked=true;get('prediction-form').fire('submit');assert.equal(get('lab-progress').textContent,'Attempted');
 get('next-hint').fire('click');get('reveal-solution').fire('click');assert.equal(hints[0].hidden,false);assert.equal(hints[1].hidden,true);
 get('explanation').value='Final observations supply the nonterminal bootstrap; reset boundaries cut the trace.';get('explanation').fire('input');
 get('verified').checked=true;get('verified').fire('change');get('complete-lab').fire('click');assert.equal(get('lab-progress').textContent,'Completed');
 ({get,hints}=await mount(storage));assert.equal(get('lab-progress').textContent,'Completed');assert.equal(hints[0].hidden,false);assert.equal(get('solution').hidden,false);
 get('verified').checked=false;get('verified').fire('change');assert.equal(get('lab-progress').textContent,'Attempted');
 assert.match(get('completion-feedback').textContent,/Completion removed/);
 get('verified').checked=true;get('verified').fire('change');get('complete-lab').fire('click');
 get('explanation').value='';get('explanation').fire('input');assert.equal(get('lab-progress').textContent,'Attempted');assert.match(get('completion-feedback').textContent,/Completion removed/);
 get('reset-progress').fire('click');assert.equal(get('lab-progress').textContent,'Not started');assert.ok(hints.every(h=>h.hidden));assert.equal(get('solution').hidden,true);
});
test('blocked storage keeps controls usable with a visible session warning',async()=>{
 const blocked={getItem(){throw Error('blocked');},setItem(){throw Error('blocked');}};
 const {get,hints}=await mount(blocked);
 assert.match(get('saved-status').textContent,/unavailable/);get('next-hint').fire('click');assert.equal(hints[0].hidden,false);assert.match(get('saved-status').textContent,/session only/);
 get('explanation').value='QA explanation';get('explanation').fire('input');get('verified').checked=true;get('complete-lab').fire('click');assert.equal(get('lab-progress').textContent,'Completed');
});
