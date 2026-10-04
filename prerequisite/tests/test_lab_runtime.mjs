import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createProgressStore, validateProgress, PROGRESS_KEY } from '../site/labs/assets/storage.js';
import { resetChain, stepChain, seededActionGenerator } from '../site/labs/assets/experiments/chain-model.js';

const fixtures = JSON.parse(fs.readFileSync(new URL('../site/labs/downloads/p1-loop/fixtures.json', import.meta.url)));
const memory = () => {
  const values = new Map();
  return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) };
};
test('browser model matches independent scripted fixtures and boundaries', () => {
  for (const name of ['right_right', 'left_boundary', 'cap_one']) {
    const fixture = fixtures[name];
    let state = resetChain(name === 'cap_one' ? 1 : 6);
    const rows = fixture.actions.map(action => (state = stepChain(state, action)));
    for (const [field, key] of [['position','observations'],['reward','rewards'],['terminated','terminated'],['truncated','truncated']]) {
      assert.deepEqual(rows.map(row => row[field]), fixture[key]);
    }
    assert.equal(state.total, fixture.total);
    if (state.terminated || state.truncated) assert.throws(() => stepChain(state, 1));
  }
  assert.throws(() => resetChain(0));
  assert.throws(() => stepChain(resetChain(), 3));
});
test('seeded action reset reproduces its own trace', () => {
  const first = seededActionGenerator(7), second = seededActionGenerator(7);
  assert.deepEqual(Array.from({length:20},first), Array.from({length:20},second));
});
test('progress survives reload with only explicitly requested help', () => {
  const storage = memory();
  const first = createProgressStore(['p1-loop'], storage);
  assert.equal(first.get('p1-loop').solution, false);
  first.set('p1-loop', {status:'attempted',attempts:1,prediction:'terminal',hints:1,explanation:'My trace ended at the goal.'});
  const restored = createProgressStore(['p1-loop'], storage);
  assert.equal(restored.get('p1-loop').hints, 1);
  assert.equal(restored.get('p1-loop').solution, false);
  assert.equal(restored.get('p1-loop').explanation, 'My trace ended at the goal.');
});
test('blocked or corrupt storage falls back without losing the session', () => {
  const blocked = {getItem(){throw new Error('blocked');},setItem(){throw new Error('blocked');}};
  const store = createProgressStore(['p1-loop'], blocked);
  store.set('p1-loop', {status:'attempted',attempts:1});
  assert.equal(store.get('p1-loop').attempts, 1);
  assert.match(store.warning, /session/);
  assert.equal(JSON.parse(store.export()).labs['p1-loop'].attempts, 1);
  const storage = memory(); storage.setItem(PROGRESS_KEY, '{bad');
  const recovered = createProgressStore(['p1-loop'], storage);
  assert.match(recovered.warning, /unreadable/);
  assert.equal(recovered.get('p1-loop').status, 'not-started');
});
test('imports reject invalid/unknown records and retain previous progress', () => {
  const store = createProgressStore(['p1-loop'], memory());
  store.set('p1-loop', {attempts:2,status:'attempted'});
  const previous = store.export();
  assert.throws(() => store.import('{invalid'));
  assert.throws(() => store.import(JSON.stringify({version:1,labs:{unknown:{}}})));
  assert.throws(() => store.import(JSON.stringify({version:1,labs:{'p1-loop':{hints:999}}})));
  assert.equal(store.export(), previous);
  assert.throws(() => validateProgress({version:1,labs:{'p1-loop':{status:'completed'}}}, ['p1-loop']));
});
test('export/import and reset isolate the lab record', () => {
  const store = createProgressStore(['p1-loop','p1-state'], memory());
  store.set('p1-loop', {status:'completed',verified:true,explanation:'I ran the local checks.'});
  store.set('p1-state', {status:'attempted',attempts:1});
  const other = createProgressStore(['p1-loop','p1-state'], memory());
  other.import(store.export());
  assert.equal(other.get('p1-loop').status,'completed');
  other.reset('p1-loop');
  assert.equal(other.get('p1-loop').solution,false);
  assert.equal(other.get('p1-state').attempts,1);
});
