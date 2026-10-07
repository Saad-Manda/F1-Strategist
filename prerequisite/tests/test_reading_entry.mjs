import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {courseContinue,acknowledgeReading} from '../site/assets/reading-navigation.js';
import {emptyCourseV2} from '../site/assets/course-progress-v2.js';
const data=JSON.parse(fs.readFileSync(new URL('../site/assets/course-reading-data.json',import.meta.url)));
const bundle=()=>({course:emptyCourseV2(),labs:{version:1,labs:{}}});
test('Continue honors surviving migrated lessons and exact unfinished reading identity',()=>{
 const b=bundle(),lesson=data.course.lessons.find(l=>l.id==='p9-gae');
 b.course.resume={kind:'reading',reading:lesson.required[0]};
 assert.equal(courseContinue(data.course,b).url,'readings/p9-gae/td-residuals.html');
 b.course.readings=[...lesson.required];b.course.resume={kind:'lesson',lesson:lesson.id,step:'python'};
 assert.match(courseContinue(data.course,b).url,/p9-gae.html\?lesson=p9-gae&step=browser#challenge$/);
 b.course.browser=[lesson.practice.labId];assert.match(courseContinue(data.course,b).url,/step=python#implement$/);
 b.course.readings.pop();assert.equal(courseContinue(data.course,b).url,'readings/p9-gae/gae-boundaries.html');
});
test('module resume checks required work; optional reference acknowledgments do not hijack Continue',()=>{
 const b=bundle(),m=data.course.modules[0];b.course.resume={kind:'checkpoint',module:m.id};
 assert.equal(courseContinue(data.course,b).url,data.course.readings[0].route);
 b.course.resume={kind:'reading',reading:data.course.readings.find(r=>r.role==='further-depth').id};
 assert.equal(courseContinue(data.course,b).url,data.course.readings[0].route);
});
test('stale metadata release fails before storage or migration writes',async()=>{
 let writes=0;globalThis.localStorage={getItem(){return null;},setItem(){writes++;}};
 globalThis.fetch=async()=>({ok:true,json:async()=>({...data,release:'old-release'})});
 await assert.rejects(import('../site/assets/reading-session.js?stale-entry-test'),/Course assets changed/);
 assert.equal(writes,0);
});

test('finishing optional depth retains an advanced guided resume and is idempotent',()=>{
 const b=bundle(),optional=data.course.readings.find(r=>r.role==='further-depth');
 b.course.resume={kind:'reading',reading:'p9-gae/td-residuals'};
 acknowledgeReading(data.course,b,optional.id);
 acknowledgeReading(data.course,b,optional.id);
 assert.deepEqual(b.course.readings,[optional.id]);
 assert.deepEqual(b.course.resume,{kind:'reading',reading:'p9-gae/td-residuals'});
 assert.equal(courseContinue(data.course,b).url,'readings/p9-gae/td-residuals.html');
 const before=structuredClone(b);
 assert.throws(()=>acknowledgeReading(data.course,b,'missing/reading'),/Unknown authored reading/);
 assert.deepEqual(b,before);
});
