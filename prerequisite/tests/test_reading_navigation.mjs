import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {previewContinue,moduleReady,projectHandoff} from '../site/assets/reading-navigation.js';
import {emptyCourseV2} from '../site/assets/course-progress-v2.js';
const course=JSON.parse(fs.readFileSync(new URL('../content/course-registry.json',import.meta.url)));
const m=course.modules[0];
const fresh=()=>({course:emptyCourseV2(),labs:{version:1,labs:{}},retainedLegacy:null});
const finishLesson=(b,l)=>{
  b.course.readings.push(...l.required);
  if(l.practice){b.course.browser.push(l.practice.labId);b.labs.labs[l.practice.labId]={status:'completed'};}
};
test('Continue traverses every core reading, independent practice, theory-only lesson and application',()=>{
  const course=JSON.parse(fs.readFileSync(new URL('../content/course-registry.json',import.meta.url)));
  for(const r of course.readings)if(r.module!=='foundations')r.status='planned';
  const b=fresh();
  for(const id of m.lessons){
    const l=course.lessons.find(l=>l.id===id);
    for(const r of l.required){assert.equal(previewContinue(course,b).url,course.readings.find(r2=>r2.id===r).route);b.course.readings.push(r);}
    if(l.practice){
      assert.match(previewContinue(course,b).url,/step=browser/);b.course.browser.push(l.practice.labId);
      assert.match(previewContinue(course,b).url,/step=python/);b.labs.labs[l.practice.labId]={status:'completed'};
    }
  }
  for(const id of m.applications){assert.equal(previewContinue(course,b).url,course.readings.find(r=>r.id===id).route);b.course.readings.push(id);}
  assert.equal(previewContinue(course,b).url,m.projectCheckpoint.route);
  b.course.checks[m.id]=m.projectCheckpoint.checks.map(c=>c.id);
  assert.equal(moduleReady(course,b,m.id),true);
  assert.equal(previewContinue(course,b).url,'roadmap.html#phase-2');
  assert.equal(b.course.readings.includes('p1-values/bellman-fixed-points'),false);
});
test('checklist alone cannot certify preparation; revoking practice returns Continue to it',()=>{
  const b=fresh();b.course.checks[m.id]=m.projectCheckpoint.checks.map(c=>c.id);
  assert.equal(moduleReady(course,b,m.id),false);
  for(const id of m.lessons)finishLesson(b,course.lessons.find(l=>l.id===id));
  b.course.readings.push(...m.applications);
  assert.equal(moduleReady(course,b,m.id),true);
  b.labs.labs['p1-state'].status='attempted';
  assert.equal(moduleReady(course,b,m.id),false);
  assert.match(previewContinue(course,b).url,/p1-state.*step=python/);
});

test('R4 Continue traverses all three authored modules and stops at the next project stage',()=>{
  const course=JSON.parse(fs.readFileSync(new URL('../content/course-registry.json',import.meta.url)));
  for(const r of course.readings)if(r.module==='neural-value-learning')r.status='planned';
  const b=fresh();
  for(const module of course.modules.slice(0,3)){
    for(const id of module.lessons){
      const lesson=course.lessons.find(l=>l.id===id);
      for(const id of lesson.required){
        assert.equal(previewContinue(course,b).url,course.readings.find(r=>r.id===id).route);
        b.course.readings.push(id);
      }
      if(lesson.practice){
        assert.match(previewContinue(course,b).url,/step=browser/);
        b.course.browser.push(lesson.practice.labId);
        assert.match(previewContinue(course,b).url,/step=python/);
        b.labs.labs[lesson.practice.labId]={status:'completed'};
      }
    }
    for(const id of module.applications){
      assert.equal(previewContinue(course,b).url,course.readings.find(r=>r.id===id).route);
      b.course.readings.push(id);
    }
    assert.equal(previewContinue(course,b).url,module.projectCheckpoint.route);
    assert.equal(moduleReady(course,b,module.id),false);
    b.course.checks[module.id]=module.projectCheckpoint.checks.map(c=>c.id);
    assert.equal(moduleReady(course,b,module.id),true);
  }
  assert.equal(previewContinue(course,b).url,'roadmap.html#phase-5');
  assert.equal(projectHandoff(course,'planning').url,'roadmap.html#phase-4');
  assert.equal(projectHandoff(course,'tabular-learning').url,'roadmap.html#phase-5');
  assert.equal(b.course.readings.some(id=>course.readings.find(r=>r.id===id).role==='further-depth'),false);
  const tabular=course.modules[2];
  const application=tabular.applications[0];
  b.course.readings=b.course.readings.filter(id=>id!==application);
  assert.equal(moduleReady(course,b,tabular.id),false);
  assert.equal(previewContinue(course,b).url,course.readings.find(r=>r.id===application).route);
});

test('R5 Continue covers neural practice and applications before the Phase 6 handoff',()=>{
  const course=JSON.parse(fs.readFileSync(new URL('../content/course-registry.json',import.meta.url)));
  for(const r of course.readings)if(['multiple-agents','self-play','policy-gradients'].includes(r.module))r.status='planned';
  const b=fresh();
  for(const module of course.modules.slice(0,3)){
    for(const id of module.lessons)finishLesson(b,course.lessons.find(l=>l.id===id));
    b.course.readings.push(...module.applications);
    b.course.checks[module.id]=module.projectCheckpoint.checks.map(c=>c.id);
  }
  const module=course.modules[3];
  for(const id of module.lessons){
    const lesson=course.lessons.find(l=>l.id===id);
    for(const reading of lesson.required){
      assert.equal(previewContinue(course,b).url,course.readings.find(r=>r.id===reading).route);
      b.course.readings.push(reading);
    }
    assert.match(previewContinue(course,b).url,/step=browser/);
    b.course.browser.push(lesson.practice.labId);
    assert.match(previewContinue(course,b).url,/step=python/);
    b.labs.labs[lesson.practice.labId]={status:'completed'};
  }
  for(const id of module.applications){
    assert.equal(previewContinue(course,b).url,course.readings.find(r=>r.id===id).route);
    b.course.readings.push(id);
  }
  assert.equal(previewContinue(course,b).url,module.projectCheckpoint.route);
  assert.equal(moduleReady(course,b,module.id),false);
  b.course.checks[module.id]=module.projectCheckpoint.checks.map(c=>c.id);
  assert.equal(moduleReady(course,b,module.id),true);
  assert.equal(previewContinue(course,b).url,'roadmap.html#phase-6');
  assert.equal(b.course.readings.includes('p5-network/adam-moments'),false);
  b.labs.labs['p5-per'].status='attempted';
  assert.equal(moduleReady(course,b,module.id),false);
  assert.match(previewContinue(course,b).url,/p5-per.*step=python/);
});

test('R6 full course Continue covers advanced applications and every practice identity',()=>{
  const b=fresh();
  for(const module of course.modules){
    for(const id of module.lessons){
      const lesson=course.lessons.find(l=>l.id===id);
      for(const id of lesson.required){
        assert.equal(previewContinue(course,b).url,course.readings.find(r=>r.id===id).route);
        b.course.readings.push(id);
      }
      if(lesson.practice){
        assert.match(previewContinue(course,b).url,/step=browser/);
        b.course.browser.push(lesson.practice.labId);
        assert.match(previewContinue(course,b).url,/step=python/);
        b.labs.labs[lesson.practice.labId]={status:'completed'};
      }
    }
    for(const id of module.applications){
      assert.equal(previewContinue(course,b).url,course.readings.find(r=>r.id===id).route);
      b.course.readings.push(id);
    }
    assert.equal(previewContinue(course,b).url,module.projectCheckpoint.route);
    assert.equal(moduleReady(course,b,module.id),false);
    b.course.checks[module.id]=module.projectCheckpoint.checks.map(c=>c.id);
    assert.equal(moduleReady(course,b,module.id),true);
  }
  assert.equal(previewContinue(course,b).url,'roadmap.html');
  assert.equal(b.course.browser.length,25);
  assert.equal(b.course.readings.some(id=>course.readings.find(r=>r.id===id).role==='further-depth'),false);
  assert.equal(projectHandoff(course,'multiple-agents').url,'roadmap.html#phase-7');
  assert.equal(projectHandoff(course,'self-play').url,'roadmap.html#phase-9');
  const lesson=course.lessons.find(l=>l.id==='p9-probability');
  assert.equal(lesson.practice,null);
  assert.deepEqual(lesson.prerequisites,['p1-probability','p5-network']);
  const allowed=new Set([...course.lessons.filter(l=>!['multiple-agents','self-play'].includes(l.module)).flatMap(l=>l.required)]);
  for(const r of course.readings.filter(r=>r.module==='policy-gradients'&&r.role==='core')){
    assert.ok(r.requires.every(id=>allowed.has(id)));
  }
  b.labs.labs['p9-gae'].status='attempted';
  assert.equal(moduleReady(course,b,'policy-gradients'),false);
  assert.match(previewContinue(course,b).url,/p9-gae.*step=python/);
});
