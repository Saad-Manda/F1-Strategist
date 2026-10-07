import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createReadingSession} from '../site/assets/reading-store.js';
import {MIGRATION_MESSAGE,migrationNoticeSeen} from '../site/assets/course-progress-v2.js';
import {acknowledgeReading,courseContinue,moduleReady} from '../site/assets/reading-navigation.js';
const data=JSON.parse(fs.readFileSync(new URL('../site/assets/course-reading-data.json',import.meta.url)));
class Storage {
 values=new Map();blocked=false;
 getItem(k){return this.values.get(k)??null;}
 setItem(k,v){if(this.blocked)throw Error('Blocked');this.values.set(k,v);}
 removeItem(k){if(this.blocked)throw Error('Blocked');this.values.delete(k);}
}
const locks={request:async(name,options,fn)=>fn()};
const create=(storage=new Storage(),lock=locks)=>createReadingSession({storage,locks:lock,data});
const finish=id=>b=>{if(!b.course.readings.includes(id))b.course.readings.push(id);return b;};
const [first,second]=data.course.lessons[0].required;
const legacy=()=>({version:1,readings:[data.snapshot.course.resources[0].id],browser:['p1-loop'],checks:{},resume:{kind:'lesson',lesson:'p1-loop',step:'python'}});
const lab=()=>({version:1,labs:{'p1-loop':{attempts:3,prediction:'terminal',explanation:'Final observations and ending flags checked.',status:'completed',hints:2,solution:true,verified:true}}});

test('the full active course saves, restores, exports and resumes every required step independently',async()=>{
 const storage=new Storage(),session=await create(storage),course=data.course;
 for(const module of course.modules){
  for(const lessonId of module.lessons){
   const lesson=course.lessons.find(l=>l.id===lessonId);
   for(const id of lesson.required){
    assert.equal(courseContinue(course,session.bundle).url,course.readings.find(r=>r.id===id).route);
    await session.update(b=>acknowledgeReading(course,b,id));
   }
   if(lesson.practice){
    const id=lesson.practice.labId;
    assert.match(courseContinue(course,session.bundle).url,/step=browser#challenge$/);
    await session.update(b=>{b.course.browser.push(id);b.course.resume={kind:'lesson',lesson:lessonId,step:'python'};return b;});
    assert.match(courseContinue(course,session.bundle).url,/step=python#implement$/);
    await session.update(b=>{b.labs.labs[id]={attempts:1,prediction:'',explanation:'Independent local reference checks passed.',status:'completed',hints:0,solution:false,verified:true};return b;});
   }
  }
  for(const id of module.applications){
   assert.equal(courseContinue(course,session.bundle).url,course.readings.find(r=>r.id===id).route);
   await session.update(b=>acknowledgeReading(course,b,id));
  }
  assert.equal(courseContinue(course,session.bundle).url,module.projectCheckpoint.route);
  assert.equal(moduleReady(course,session.bundle,module.id),false);
  await session.update(b=>{b.course.checks[module.id]=module.projectCheckpoint.checks.map(c=>c.id);b.course.resume={kind:'checkpoint',module:module.id};return b;});
  assert.equal(moduleReady(course,(await create(storage)).bundle,module.id),true);
 }
 assert.equal(session.bundle.course.readings.length,131);
 assert.equal(session.bundle.course.browser.length,25);
 assert.equal(courseContinue(course,session.bundle).url,'roadmap.html');
 for(const r of course.readings.filter(r=>r.role==='further-depth'))await session.update(b=>acknowledgeReading(course,b,r.id));
 const imported=await create();await imported.import(session.export());
 assert.deepEqual(imported.bundle,session.bundle);
 const before=session.bundle;
 await session.update(b=>{delete b.labs.labs['p9-gae'];b.course.browser=b.course.browser.filter(id=>id!=='p9-gae');return b;});
 assert.equal(session.bundle.course.readings.length,134);
 assert.deepEqual(session.bundle.labs.labs['p5-network'],before.labs.labs['p5-network']);
 assert.deepEqual(session.bundle.course.checks,before.course.checks);
 assert.equal(moduleReady(course,session.bundle,'policy-gradients'),false);
 assert.match(courseContinue(course,session.bundle).url,/p9-gae.*step=browser#challenge$/);
});

test('visits are read-only; queued acknowledgments merge and restore once',async()=>{
 const storage=new Storage(),session=await create(storage);assert.equal(storage.values.size,0);
 await Promise.all([session.update(finish(first)),session.update(finish(second))]);await session.update(finish(first));
 assert.deepEqual((await create(storage)).bundle.course.readings,[first,second]);
});
test('same-origin migration waits for older-tab acknowledgment and retains every lab field',async()=>{
 const storage=new Storage();storage.setItem('rl-course:v1',JSON.stringify(legacy()));storage.setItem('rl-labs:v1',JSON.stringify(lab()));
 const before=[...storage.values],session=await create(storage);
 assert.equal(session.pendingMigration,true);assert.deepEqual([...storage.values],before);
 assert.deepEqual(session.bundle.labs,lab());assert.deepEqual(session.bundle.course.readings,[]);
 await assert.rejects(session.update(finish(first)),/older course tabs/);
 await session.activateMigration();assert.equal(session.pendingMigration,false);
 assert.equal(storage.getItem('rl-course:v1'),before[0][1]);assert.ok(storage.getItem('rl-course:migration-backup:v1'));
 assert.equal(session.bundle.course.migration.noticePending,true);assert.ok(MIGRATION_MESSAGE.includes('lab work was retained'));
 await session.update(b=>{b.course=migrationNoticeSeen(b.course,data.course);return b;});
 assert.equal((await create(storage)).bundle.course.migration.noticePending,false);
});
test('lab-only origins retain evidence but do not invent browser or reading completion',async()=>{
 const storage=new Storage();storage.setItem('rl-labs:v1',JSON.stringify(lab()));const session=await create(storage);
 await session.activateMigration();assert.deepEqual(session.bundle.labs,lab());assert.deepEqual(session.bundle.course.browser,[]);assert.deepEqual(session.bundle.course.readings,[]);
});
test('legacy combined, lab-only and v2 imports preserve evidence and reject before mutation',async()=>{
 const storage=new Storage(),session=await create(storage);
 await session.import(JSON.stringify({format:'rl-course-progress',version:1,course:legacy(),labs:lab()}));
 assert.deepEqual(session.bundle.labs,lab());assert.deepEqual(session.bundle.course.readings,[]);
 const backup=storage.getItem('rl-course:migration-backup:v1');await session.import(JSON.stringify(lab()));
 const expected=session.bundle;await session.import(session.export());assert.deepEqual(session.bundle,expected);
 for(const bad of ['{invalid',JSON.stringify({version:1,labs:{unknown:{}}}),JSON.stringify({format:'rl-course-progress',version:2,course:{version:2,readings:['unknown']}})]){
  const before=[...storage.values];await assert.rejects(session.import(bad));assert.deepEqual([...storage.values],before);
 }
 assert.equal(storage.getItem('rl-course:migration-backup:v1'),backup);
});
test('failed writes preserve memory and durable state; corrupt data stays recoverable',async()=>{
 const storage=new Storage(),session=await create(storage);await session.update(finish(first));const before=[...storage.values],bundle=session.bundle;
 storage.blocked=true;await assert.rejects(session.update(finish(second)));assert.deepEqual(session.bundle,bundle);assert.deepEqual([...storage.values],before);
 const corrupt=new Storage();corrupt.setItem('rl-course:v1','{invalid');const broken=await create(corrupt);
 assert.equal(broken.writable,false);assert.match(broken.warning,/retained/);assert.equal(JSON.parse(broken.recoveryExport()).saved['rl-course:v1'],'{invalid');
 await assert.rejects(broken.update(finish(first)));assert.equal(corrupt.getItem('rl-course:v1'),'{invalid');
});
test('missing locks preserve exportable legacy work without migration writes',async()=>{
 const storage=new Storage();storage.setItem('rl-labs:v1',JSON.stringify(lab()));const before=[...storage.values],session=await create(storage,null);
 assert.deepEqual(session.bundle.labs,lab());assert.equal(session.writable,false);await assert.rejects(session.update(finish(first)));assert.deepEqual([...storage.values],before);
});
test('interrupted journal is recovered under the lock before displaying progress',async()=>{
 const storage=new Storage(),session=await create(storage);await session.update(finish(first));
 const before=Object.fromEntries(['rl-labs:v1','rl-course:v2','rl-course:migration-backup:v1'].map(k=>[k,storage.getItem(k)]));
 storage.setItem('rl-course:transaction:v2',JSON.stringify({version:1,before}));storage.setItem('rl-labs:v1','{half-written');
 assert.deepEqual((await create(storage)).bundle.course.readings,[first]);assert.equal(storage.getItem('rl-course:transaction:v2'),null);
});
test('an older writer stops new saves until tabs are reloaded',async()=>{
 const storage=new Storage(),session=await create(storage);await session.update(finish(first));await session.refresh('rl-course:v1');
 assert.equal(session.writable,false);await assert.rejects(session.update(finish(second)),/older course tab/);
});
