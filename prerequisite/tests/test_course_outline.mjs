import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { outlinePosition, lessonNumber } from '../site/assets/course-outline.js';
const course=JSON.parse(readFileSync(new URL('../site/assets/course-registry.json',import.meta.url),'utf8'));

test('course numbering stays sequential across the nonsequential project phases',()=>{
 assert.equal(lessonNumber(course,'p1-loop'),'1.1');assert.equal(lessonNumber(course,'p35-backward'),'2.1');
 assert.equal(lessonNumber(course,'p9-ppo'),'7.4');assert.equal(lessonNumber(course,'unknown'),null);
});
test('shared readings identify the invoking lesson and the exact assigned section',()=>{
 for(const lesson of course.lessons)for(const id of lesson.required){
  const resource=course.resources.find(r=>r.id===id);
  const position=outlinePosition(course,resource.route,`?lesson=${lesson.id}&step=theory`,resource.anchor?'#'+resource.anchor:'');
  assert.equal(position.lesson,lesson.id);assert.equal(position.reading,id);assert.equal(position.step,'theory');
 }
});
test('direct reference visits and invalid context avoid inventing an invoking lesson',()=>{
 const route='phase-1-rl-prerequisites/02-markov-decision-processes.html';
 for(const query of ['', '?lesson=unknown&step=theory', '?lesson=p1-state&lesson=p1-return&step=theory','?lesson=p9-ppo&step=theory']){
  const position=outlinePosition(course,route,query);assert.equal(position.module,'foundations');assert.equal(position.lesson,undefined);assert.equal(position.reference,route);
 }
});
test('guides, lab steps, bridge readings and checkpoints retain their distinct positions',()=>{
 assert.equal(outlinePosition(course,'lessons/p1-loop.html','','#python').step,'python');
 const l=course.lessons[0];assert.equal(outlinePosition(course,l.lab,`?lesson=${l.id}&step=python`,'#implement').step,'python');
 const m=course.modules[0],r=course.resources.find(r=>r.id===m.projectCheckpoint.required[0]);
 const bridge=outlinePosition(course,r.route,'?module='+m.id);assert.equal(bridge.bridge,r.id);assert.equal(bridge.checkpoint,true);assert.equal(bridge.lesson,undefined);
 assert.deepEqual(outlinePosition(course,m.route,'','#project-checkpoint'),{module:m.id,checkpoint:true});
 assert.deepEqual(outlinePosition(course,'library.html'),{});
});
