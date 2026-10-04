import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolveCourseContext, readingTarget } from '../site/assets/course-context.js';

const course = JSON.parse(readFileSync(new URL('../site/assets/course-registry.json', import.meta.url), 'utf8'));
const resource = id => course.resources.find(r => r.id === id);
const lesson = id => course.lessons.find(l => l.id === id);

test('ordered theory moves through exact required sections, then the browser lab', () => {
  for (const l of course.lessons) {
    l.required.forEach((id, i) => {
      const r = resource(id);
      const context = resolveCourseContext(course, r.route, `?lesson=${l.id}&step=theory`, r.anchor ? `#${r.anchor}` : '');
      assert.equal(context.return, l.route + '#theory');
      assert.equal(context.next, i + 1 < l.required.length ? readingTarget(resource(l.required[i + 1]), l.id) : `${l.lab}?lesson=${l.id}&step=browser#challenge`);
      assert.equal(context.resource.id, id);
    });
  }
});

test('a shared MDP page retains the invoking lesson and its section boundary', () => {
  const route = 'phase-1-rl-prerequisites/02-markov-decision-processes.html';
  const state = resolveCourseContext(course, route, '?lesson=p1-state&step=theory');
  const returns = resolveCourseContext(course, route, '?lesson=p1-return&step=theory');
  assert.notEqual(state.resource.id, returns.resource.id);
  assert.equal(state.return, 'lessons/p1-state.html#theory');
  assert.equal(returns.return, 'lessons/p1-return.html#theory');
  assert.equal(returns.resource.heading, 'Return and the discount factor');
  assert.match(returns.resource.instruction, /Stop before "Action masking"/);
});

test('browser moves to local Python; module ends prioritize project preparation', () => {
  for (const l of course.lessons) {
    const browser = resolveCourseContext(course, l.lab, `?lesson=${l.id}&step=browser`);
    assert.equal(browser.next, `${l.lab}?lesson=${l.id}&step=python#implement`);
    const python = resolveCourseContext(course, l.lab, `?lesson=${l.id}&step=python`);
    const m = course.modules.find(m => m.id === l.module);
    if (l.id === m.lessons.at(-1)) assert.equal(python.next, m.projectCheckpoint.route);
    else assert.equal(python.next, course.lessons[course.lessons.indexOf(l) + 1].route);
  }
});

test('checkpoint bridges advance within their module and return to the checkpoint', () => {
  for (const m of course.modules) {
    m.projectCheckpoint.required.forEach((id, i, ids) => {
      const context = resolveCourseContext(course, resource(id).route, `?module=${m.id}`);
      assert.equal(context.return, m.projectCheckpoint.route);
      assert.equal(context.next, i + 1 < ids.length ? `${resource(ids[i + 1]).route}?module=${m.id}` : m.projectCheckpoint.route);
    });
  }
});

test('missing, duplicate, mixed, unknown, unrelated and unsafe context retains reference mode', () => {
  const route = resource(lesson('p1-loop').required[0]).route;
  for (const search of ['', '?lesson=unknown&step=theory', '?lesson=p1-loop&step=unknown',
    '?lesson=p9-ppo&step=theory', '?lesson=p1-loop&step=browser', '?lesson=p1-loop&step=theory&module=foundations',
    '?lesson=p1-loop&lesson=p1-state&step=theory', '?module=unknown', '?module=foundations']) {
    assert.equal(resolveCourseContext(course, route, search), null, search);
  }
  assert.equal(resolveCourseContext(course, '../private.html', '?lesson=p1-loop&step=theory'), null);
  const valid = resolveCourseContext(course, route, '?lesson=p1-loop&step=theory&return=https://evil.example');
  assert.equal(valid.return, 'lessons/p1-loop.html#theory');
});
