import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createProgressStore,getSharedProgressStore,PROGRESS_KEY} from '../site/labs/assets/storage.js';
import {createCourseStore,emptyCourse,validateCourseProgress,lessonProgress,moduleProgress,continueTarget,COURSE_KEY} from '../site/assets/course-progress.js';
const course=JSON.parse(readFileSync(new URL('../site/assets/course-registry.json',import.meta.url),'utf8'));
const memory=()=>{const values=new Map();return {getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value),removeItem:key=>values.delete(key)};};
function setup(storage=memory()) {return {storage,labs:createProgressStore(course.lessons.map(l=>l.id),storage),store:createCourseStore(course,storage)};}
function completeLesson(store,labs,id){const lesson=course.lessons.find(l=>l.id===id);for(const key of lesson.required)store.acknowledge(key);store.browser(id);labs.set(id,{status:'completed',verified:true,explanation:'QA: local implementation checks and browser evidence compared.'});}
function bridge(store,module){for(const key of module.projectCheckpoint.required)store.acknowledge(key);for(const c of module.projectCheckpoint.checks)store.check(module.id,c.id,true);}

test('legacy completed labs are preserved without invented course acknowledgments',()=>{
 const {labs,store,storage}=setup();labs.set('p1-loop',{status:'completed',verified:true,explanation:'Existing verification',hints:2,solution:true,prediction:'terminal',attempts:3});
 const original=labs.export();const restored=createCourseStore(course,storage);
 const state=lessonProgress(course,restored.data,labs,'p1-loop');
 assert.equal(state.python,true);assert.equal(state.complete,false);assert.equal(state.step,'theory');assert.equal(state.browser,false);
 assert.equal(labs.export(),original);assert.equal(continueTarget(course,store.data,labs).lesson,'p1-loop');
});
test('explicit reading/browser state restores and all three kinds of evidence are required',()=>{
 const {labs,store,storage}=setup();const id='p1-loop',lesson=course.lessons[0];
 store.acknowledge(lesson.required[0]);let state=lessonProgress(course,store.data,labs,id);assert.equal(state.status,'In progress');assert.equal(state.complete,false);
 for(const key of lesson.required)store.acknowledge(key);assert.equal(lessonProgress(course,store.data,labs,id).step,'browser');
 store.browser(id);assert.equal(lessonProgress(course,store.data,labs,id).step,'python');
 labs.set(id,{status:'completed',verified:true,explanation:'Local checks ran.'});assert.equal(lessonProgress(course,store.data,labs,id).complete,true);
 const restored=createCourseStore(course,storage);assert.equal(lessonProgress(course,restored.data,labs,id).complete,true);
 labs.set(id,{verified:false,status:'attempted'});assert.equal(lessonProgress(course,store.data,labs,id).step,'python');
 store.acknowledge(lesson.required[0],false);assert.equal(lessonProgress(course,store.data,labs,id).step,'theory');
});
test('resume follows the last unfinished guided step, skips completed pointers, and persists exact theory resources',()=>{
 const {labs,store,storage}=setup();store.visit({kind:'lesson',lesson:'p1-state',step:'browser'});
 assert.equal(continueTarget(course,store.data,labs).lesson,'p1-state');assert.equal(continueTarget(course,store.data,labs).step,'browser');
 store.browser('p1-state');assert.equal(continueTarget(course,store.data,labs).lesson,'p1-loop');
 const key=course.lessons[0].required[1];store.visit({kind:'lesson',lesson:'p1-loop',step:'theory',resource:key});
 assert.equal(continueTarget(course,createCourseStore(course,storage).data,labs).url.includes(resourceAnchor(key)),true);
 function resourceAnchor(id){return course.resources.find(r=>r.id===id).anchor;}
});
test('module checkpoints interrupt later resumes, separate learning from readiness, then permit advancing',()=>{
 const {labs,store}=setup(),module=course.modules[0];for(const id of module.lessons)completeLesson(store,labs,id);
 assert.equal(moduleProgress(course,store.data,labs,module.id).learningComplete,true);assert.equal(moduleProgress(course,store.data,labs,module.id).ready,false);
 store.visit({kind:'lesson',lesson:'p35-backward',step:'python'});assert.equal(continueTarget(course,store.data,labs).url,module.projectCheckpoint.route);
 bridge(store,module);assert.equal(moduleProgress(course,store.data,labs,module.id).ready,true);assert.equal(continueTarget(course,store.data,labs).lesson,'p35-backward');
});
test('the entire course ends with Review, with no automatic loop back to Start',()=>{
 const {labs,store}=setup();for(const l of course.lessons)completeLesson(store,labs,l.id);for(const m of course.modules)bridge(store,m);
 store.visit({kind:'lesson',lesson:'p9-ppo',step:'python'});assert.equal(continueTarget(course,store.data,labs).kind,'review');
 store.browser('p9-ppo',false);assert.equal(continueTarget(course,store.data,labs).step,'browser');
});
test('combined round trip and legacy import preserve all lab fields, with legacy theory explicitly outstanding',()=>{
 const one=setup();completeLesson(one.store,one.labs,'p1-loop');one.labs.set('p1-loop',{hints:3,solution:true,prediction:'terminal',attempts:4});
 const two=setup();two.store.import(one.store.export(one.labs),two.labs);assert.equal(two.labs.export(),one.labs.export());assert.deepEqual(two.store.data,one.store.data);
 two.store.import(one.labs.export(),two.labs);assert.deepEqual(two.store.data,emptyCourse());assert.equal(two.labs.get('p1-loop').status,'completed');assert.equal(lessonProgress(course,two.store.data,two.labs,'p1-loop').complete,false);
});
test('validate the entire import before replacing either record, including invalid completed lab evidence',()=>{
 const {labs,store,storage}=setup();completeLesson(store,labs,'p1-loop');const before=store.export(labs),rawLabs=storage.getItem(PROGRESS_KEY),rawCourse=storage.getItem(COURSE_KEY);
 const invalid=JSON.parse(before);invalid.course.readings.push('unknown');assert.throws(()=>store.import(JSON.stringify(invalid),labs));
 invalid.course=emptyCourse();invalid.labs.labs['p1-loop'].verified=false;assert.throws(()=>store.import(JSON.stringify(invalid),labs));
 assert.throws(()=>store.import('{bad',labs));assert.equal(store.export(labs),before);assert.equal(storage.getItem(PROGRESS_KEY),rawLabs);assert.equal(storage.getItem(COURSE_KEY),rawCourse);
});
test('a second-key write failure rolls back storage and retains both live records',()=>{
 const values=memory();let fail=false;
 const storage={...values,setItem(key,value){if(fail&&key===COURSE_KEY){fail=false;throw new Error('quota');}values.setItem(key,value);}};
 const {labs,store}=setup(storage);completeLesson(store,labs,'p1-loop');const before=store.export(labs),oldLabs=storage.getItem(PROGRESS_KEY),oldCourse=storage.getItem(COURSE_KEY);
 fail=true;assert.throws(()=>store.import(JSON.stringify({version:1,labs:{}}),labs),/existing progress retained/);
 assert.equal(store.export(labs),before);assert.equal(storage.getItem(PROGRESS_KEY),oldLabs);assert.equal(storage.getItem(COURSE_KEY),oldCourse);assert.match(store.warning,/retained/);
});
test('blocked storage keeps usable page state and export, without claiming persistence',()=>{
 const blocked={getItem(){throw new Error('blocked');},setItem(){throw new Error('blocked');}};
 const {labs,store}=setup(blocked);store.acknowledge(course.lessons[0].required[0]);store.browser('p1-loop');labs.set('p1-loop',{attempts:1,status:'attempted'});
 assert.match(store.warning,/this page only/);assert.equal(JSON.parse(store.export(labs)).course.browser[0],'p1-loop');assert.equal(labs.get('p1-loop').attempts,1);
 assert.throws(()=>store.import(JSON.stringify({version:1,labs:{}}),labs));assert.equal(store.data.browser[0],'p1-loop');
});
test('lesson reset preserves shared readings and other lesson records; whole reset clears only the two owned keys',()=>{
 const {labs,store,storage}=setup();completeLesson(store,labs,'p1-loop');completeLesson(store,labs,'p1-state');
 const shared=course.lessons.find(l=>l.id==='p4-sarsa').optional[0];store.acknowledge(shared);
 storage.setItem('unrelated','keep');store.resetLesson('p1-loop',labs);
 assert.equal(labs.get('p1-loop').status,'not-started');assert.equal(labs.get('p1-state').status,'completed');assert.equal(lessonProgress(course,store.data,labs,'p1-state').complete,true);assert.equal(store.data.readings.includes(shared),true);
 store.resetAll(labs);assert.deepEqual(store.data,emptyCourse());assert.deepEqual(JSON.parse(labs.export()).labs,{});assert.equal(storage.getItem('unrelated'),'keep');
});
test('invalid course identities, duplicate acknowledgments and unsafe resume data are rejected',()=>{
 for(const patch of [{readings:['unknown']},{browser:['p1-loop','p1-loop']},{checks:{unknown:[]}},{resume:{kind:'lesson',lesson:'p1-loop',step:'anything'}},{resume:{kind:'lesson',lesson:'p1-loop',step:'theory',resource:'../private'}}])assert.throws(()=>validateCourseProgress({...emptyCourse(),...patch},course));
});
test('store notifications update counters when verification, reset, or imports revoke completion',()=>{
 const {labs,store}=setup();let complete=0;const refresh=()=>{complete=course.lessons.filter(l=>lessonProgress(course,store.data,labs,l.id).complete).length;};labs.subscribe(refresh);store.subscribe(refresh);
 completeLesson(store,labs,'p1-loop');assert.equal(complete,1);labs.set('p1-loop',{status:'attempted',verified:false});assert.equal(complete,0);
 completeLesson(store,labs,'p1-loop');store.resetLesson('p1-loop',labs);assert.equal(complete,0);
});
test('corrupt saved records are retained until an explicit valid import, with warnings and a usable session',()=>{
 const storage=memory();storage.setItem(COURSE_KEY,'{corrupt');storage.setItem(PROGRESS_KEY,'{corrupt labs');
 const {store,labs}=setup(storage);store.acknowledge(course.lessons[0].required[0]);labs.set('p1-loop',{status:'attempted',attempts:1});
 assert.equal(storage.getItem(COURSE_KEY),'{corrupt');assert.equal(storage.getItem(PROGRESS_KEY),'{corrupt labs');assert.match(store.warning,/this page only/);assert.match(labs.warning,/session only/);
 store.import(JSON.stringify({version:1,labs:{}}),labs);assert.deepEqual(JSON.parse(storage.getItem(COURSE_KEY)),emptyCourse());assert.equal(store.warning,'');assert.equal(labs.warning,'');
});
test('same-page lab controls and course UI share the live store even when localStorage is blocked',()=>{
 const previous=globalThis.window;globalThis.window={get localStorage(){throw new Error('blocked');}};
 try {const a=getSharedProgressStore(['p1-loop','p1-state']),b=getSharedProgressStore(['p1-state','p1-loop']);assert.equal(a,b);a.set('p1-loop',{attempts:1,status:'attempted'});assert.equal(b.get('p1-loop').attempts,1);}
 finally {if(previous===undefined)delete globalThis.window;else globalThis.window=previous;}
});
test('corruption detected during refresh retains live evidence and prevents automatic overwrite',()=>{
 const {storage,store,labs}=setup();completeLesson(store,labs,'p1-loop');
 storage.setItem(COURSE_KEY,'{external corrupt course');storage.setItem(PROGRESS_KEY,'{external corrupt labs');
 store.refresh();labs.refresh();assert.equal(lessonProgress(course,store.data,labs,'p1-loop').complete,true);
 store.browser('p1-state');labs.set('p1-state',{status:'attempted',attempts:1});
 assert.equal(storage.getItem(COURSE_KEY),'{external corrupt course');assert.equal(storage.getItem(PROGRESS_KEY),'{external corrupt labs');
 assert.match(store.warning,/this page only/);assert.match(labs.warning,/session only/);
 store.import(JSON.stringify({version:1,labs:{}}),labs);assert.equal(store.warning,'');assert.equal(labs.warning,'');
});
test('reset preserves a required resource shared by another lesson',()=>{
 const sharedCourse=structuredClone(course),key=sharedCourse.lessons[0].required[0];sharedCourse.lessons[1].required.push(key);
 const storage=memory(),labs=createProgressStore(sharedCourse.lessons.map(l=>l.id),storage),store=createCourseStore(sharedCourse,storage);
 for(const l of sharedCourse.lessons.slice(0,2)){for(const r of l.required)store.acknowledge(r);store.browser(l.id);labs.set(l.id,{status:'completed',verified:true,explanation:'QA shared-resource witness.'});}
 store.resetLesson('p1-loop',labs);assert.equal(store.data.readings.includes(key),true);assert.equal(lessonProgress(sharedCourse,store.data,labs,'p1-state').complete,true);
});
