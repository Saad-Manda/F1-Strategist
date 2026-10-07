import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {canonicalRoute, validateCourseV2, readingContext, resolveContextV2, resolveRelocation, validateRelocations} from '../site/assets/course-model-v2.js';
import {COURSE_KEY_V2, LEGACY_COURSE_KEY, JOURNAL_KEY, BACKUP_KEY, emptyCourseV2, validateCourseProgressV2,
  validateMigrationMap, migrateLegacy, validateBundleV2, exportBundleV2, lessonProgressV2, unfinishedStep,
  migrationNoticeSeen, prepareStoredProgress, commitProgress, recoverTransaction, withProgressLock} from '../site/assets/course-progress-v2.js';
import {PROGRESS_KEY} from '../site/labs/assets/storage.js';

const read = relative => JSON.parse(fs.readFileSync(new URL(relative,import.meta.url),'utf8'));
const course = read('../content/course-registry.json');
const snapshot = read('../curriculum/legacy-v1-identities.json');
const mapping = read('../content/progress-migration.json');
const relocations = read('../content/route-relocations.json');
const labs = read('../site/labs/assets/lab-registry.json');
const copy = value => structuredClone(value);
const legacyCourse = () => ({version:1,readings:[],browser:[],checks:{},resume:null});
const legacyLabs = () => ({version:1,labs:{'p1-loop':{attempts:3,prediction:'4',explanation:'I verified the ending flags.',
  status:'completed',hints:2,solution:true,verified:true}}});
const migrate = (old = legacyCourse(), labData = legacyLabs(), c = course, m = mapping) => migrateLegacy(old,labData,c,snapshot,m,labs);
const parseBundle = (raw,c=course,m=mapping) => validateBundleV2(raw,c,snapshot,m,labs);
const commit = (storage,bundle) => commitProgress(storage,bundle,course,snapshot,mapping,labs);
class MemoryStorage {
  constructor(entries = {}) { this.values = new Map(Object.entries(entries)); this.operations = 0; this.failAt = 0; this.blocked = false; this.failKey = null; }
  getItem(key) { return this.values.get(key) ?? null; }
  fault(key) { this.operations++; if (this.blocked || this.operations === this.failAt || key === this.failKey) throw new Error('Injected storage failure'); }
  setItem(key,value) { this.fault(key); this.values.set(key,value); }
  removeItem(key) { this.fault(key); this.values.delete(key); }
}
const priorStorage = () => new MemoryStorage({[LEGACY_COURSE_KEY]:JSON.stringify(legacyCourse()),[PROGRESS_KEY]:JSON.stringify(legacyLabs())});

test('Python manifest and JavaScript agree for every core/optional/application destination', () => {
  const manifest = read('../content/navigation-v2.json');
  validateCourseV2(course,labs);
  for (const r of course.readings) {
    assert.deepEqual(readingContext(course,r.id),manifest[r.route]);
    assert.deepEqual(resolveContextV2(course,r.route),manifest[r.route]);
  }
});
test('direct ownership rejects forged, duplicated and unknown context', () => {
  const route = course.readings[0].route;
  assert.equal(resolveContextV2(course,route,'?lesson=p1-state'),null);
  assert.equal(resolveContextV2(course,route,'?lesson=p1-loop&lesson=p1-loop'),null);
  assert.equal(resolveContextV2(course,route,'?module=planning'),null);
  assert.equal(resolveContextV2(course,route,'?step=browser'),null);
  assert.equal(resolveContextV2(course,'unknown.html'),null);
  assert.equal(canonicalRoute('reading','p1-loop/agent-environment-loop'),route);
  assert.throws(() => canonicalRoute('reading','../../outside'));
});
test('theory-only completion needs core readings and no fabricated practice', () => {
  const data = emptyCourseV2(), lesson = course.lessons.find(l => l.id === 'p1-probability');
  data.readings = [...lesson.required];
  assert.equal(lessonProgressV2(course,data,{version:1,labs:{}},lesson.id).complete,true);
  assert.equal(readingContext(course,lesson.required.at(-1)).next,'lessons/p1-values.html');
  const optional = course.readings.find(r => r.role === 'further-depth');
  assert.equal(readingContext(course,optional.id).acknowledge,false);
});
test('all completed legacy readings stay unread while every lab field and browser acknowledgment survives', () => {
  const old = legacyCourse(); old.readings = snapshot.course.resources.map(r => r.id); old.browser = snapshot.course.lessons.map(l => l.id);
  old.checks = Object.fromEntries(snapshot.course.modules.map(m => [m.id,m.projectCheckpoint.checks.map(c => c.id)]));
  const result = migrate(old);
  assert.deepEqual(result.course.readings,[]);
  assert.deepEqual(result.course.browser,old.browser);
  assert.deepEqual(result.labs,legacyLabs());
  assert.deepEqual(result.retainedLegacy.course,old);
  assert.deepEqual(result.course.checks,old.checks);
  assert.equal(result.course.migration.noticePending,true);
  assert.equal(migrationNoticeSeen(result.course,course).migration.noticePending,false);
  assert.equal(result.course.migration.noticePending,true);
});
test('combined v1 and lab-only imports preserve predictions/help/reflection/verification', () => {
  const old = legacyCourse(); old.readings = [snapshot.course.resources.find(r => r.kind === 'section').id];
  const combined = parseBundle(JSON.stringify({format:'rl-course-progress',version:1,course:old,labs:legacyLabs()}));
  assert.deepEqual(combined,migrate(old));
  const labOnly = parseBundle(JSON.stringify(legacyLabs()));
  assert.deepEqual(labOnly.labs,legacyLabs());
  assert.equal(labOnly.retainedLegacy.course,null);
  assert.equal(labOnly.course.resume.reading,course.lessons[0].required[0]);
});
test('v2 round-trip retains separately validated legacy identities', () => {
  const result = migrate(); result.course.readings.push(course.readings[0].id);
  assert.deepEqual(parseBundle(exportBundleV2(result)),result);
  assert.throws(() => validateCourseProgressV2({...result.course,readings:[snapshot.course.resources[0].id]},course),/Unknown/);
});
test('invalid legacy inputs and corrupt v2 storage are rejected without mutation', () => {
  const storage = priorStorage(), before = new Map(storage.values);
  const result = migrate(); result.retainedLegacy.course.readings = ['unknown.html#unreviewed'];
  assert.throws(() => commit(storage,result));
  assert.deepEqual(storage.values,before); assert.equal(storage.operations,0);
  const badLab = legacyLabs(); badLab.labs['unknown-lab'] = badLab.labs['p1-loop'];
  assert.throws(() => parseBundle(JSON.stringify(badLab)),/Unknown lab/);
  storage.values.set(COURSE_KEY_V2,'{broken');
  const corruptBefore = new Map(storage.values);
  assert.throws(() => prepareStoredProgress(storage,course,snapshot,mapping,labs));
  assert.deepEqual(storage.values,corruptBefore);
});
test('unreviewed completion equivalence and changed lab/checklist meaning are rejected', () => {
  const cPlanned = copy(course); cPlanned.readings[0].status = 'planned';
  const m = copy(mapping); m.readings[0] = {...m.readings[0],decision:'equivalent',newIds:[cPlanned.readings[0].id]};
  assert.throws(() => validateMigrationMap(m,snapshot,cPlanned,labs),/equivalence/);
  const changed = copy(labs); changed.labs[0].acceptance = ['A different calculation.'];
  assert.throws(() => validateMigrationMap(mapping,snapshot,course,changed),/meaning/);
  const c = copy(course); c.modules[0].projectCheckpoint.checks[0].text = 'A newly required concept';
  assert.throws(() => validateMigrationMap(mapping,snapshot,c,labs),/meaning/);
});
test('explicit authored equivalence carries only its reviewed reading targets', () => {
  const c = copy(course), m = copy(mapping), old = legacyCourse();
  c.readings[0].status = 'authored';
  m.readings[0] = {...m.readings[0],decision:'equivalent',newIds:[c.readings[0].id],reason:'Synthetic reviewed exact example for the migration test.'};
  old.readings = [m.readings[0].oldId];
  assert.deepEqual(migrate(old,legacyLabs(),c,m).course.readings,[c.readings[0].id]);
});
test('renamed lessons preserve independent lab identity and translate resume', () => {
  const c = copy(course), m = copy(mapping), old = legacyCourse(), oldId = c.lessons[0].id, newId = 'interaction-basics';
  c.lessons[0].id = newId; c.lessons[0].route = canonicalRoute('lesson',newId); c.modules[0].lessons[0] = newId;
  for (const l of c.lessons) l.prerequisites = l.prerequisites.map(p => p === oldId ? newId : p);
  for (const r of c.readings) if (r.lesson === oldId) r.lesson = newId;
  m.practice[0].newLesson = newId; m.resume[0].newLesson = newId;
  old.browser = [oldId]; old.resume = {kind:'lesson',lesson:oldId,step:'python'};
  const result = migrate(old,legacyLabs(),c,m);
  assert.deepEqual(result.course.browser,['p1-loop']);
  assert.equal(c.lessons[0].practice.labId,'p1-loop');
  assert.equal(result.course.resume.reading,c.lessons[0].required[0]);
  assert.equal(resolveContextV2(c,c.readings[0].route).lesson,newId);
});
test('reordered independent lessons derive new numbering without changing saved lab work', () => {
  const c = copy(course);
  [c.lessons[1],c.lessons[2]] = [c.lessons[2],c.lessons[1]];
  [c.modules[0].lessons[1],c.modules[0].lessons[2]] = [c.modules[0].lessons[2],c.modules[0].lessons[1]];
  validateCourseV2(c,labs);
  assert.equal(readingContext(c,'p1-state/state-observation').lessonNumber,3);
  const old = legacyCourse(); old.resume = {kind:'lesson',lesson:'p1-state',step:'theory'};
  const result = migrate(old,legacyLabs(),c);
  assert.equal(result.course.resume.reading,'p1-state/state-observation');
  assert.deepEqual(result.labs,legacyLabs());
});
test('removed lesson falls back within its module while its lab is remapped once', () => {
  const c = copy(course), m = copy(mapping), old = legacyCourse();
  const removed = c.lessons.find(l => l.id === 'p1-state');
  c.lessons = c.lessons.filter(l => l.id !== removed.id);
  c.modules[0].lessons = c.modules[0].lessons.filter(k => k !== removed.id);
  c.lessons[0].required.push(...removed.required);
  for (const r of c.readings) if (r.lesson === removed.id) r.lesson = c.lessons[0].id;
  for (const l of c.lessons) l.prerequisites = l.prerequisites.filter(k => k !== removed.id);
  c.lessons.find(l => l.id === 'p1-probability').practice = removed.practice;
  m.practice.find(r => r.oldLesson === removed.id).newLesson = 'p1-probability';
  m.resume.find(r => r.oldLesson === removed.id).newLesson = null;
  old.resume = {kind:'lesson',lesson:removed.id,step:'theory'};
  const result = migrate(old,legacyLabs(),c,m);
  assert.equal(result.course.resume.reading,c.lessons[0].required[0]);
  assert.deepEqual(result.labs,legacyLabs());
});
test('reviewed relocation choices cover known old sections and never catch unknown URLs', () => {
  validateRelocations(relocations,course,snapshot);
  const broad = resolveRelocation(relocations,'phase-1-rl-prerequisites/02-markov-decision-processes.html');
  assert.equal(broad.kind,'choices'); assert.ok(broad.targets.length > 1);
  const knownSection = snapshot.course.resources.find(r => r.kind === 'section').id;
  assert.ok(resolveRelocation(relocations,knownSection));
  assert.equal(resolveRelocation(relocations,'unknown/path.html'),null);
  assert.equal(resolveRelocation(relocations,'https://example.com'),null);
  const forged = copy(relocations); forged.routes[0].targets = ['https://example.com'];
  assert.throws(() => validateRelocations(forged,course,snapshot),/canonical relocation/);
});
test('stored migration preparation is read-only and fresh v2 has no migration notice', () => {
  const storage = priorStorage(), before = new Map(storage.values);
  assert.deepEqual(prepareStoredProgress(storage,course,snapshot,mapping,labs),migrate());
  assert.deepEqual(storage.values,before); assert.equal(storage.operations,0);
  const fresh = prepareStoredProgress(new MemoryStorage(),course,snapshot,mapping,labs);
  assert.deepEqual(fresh,{course:emptyCourseV2(),labs:{version:1,labs:{}},retainedLegacy:null});
});
test('successful save preserves v1 bytes, retains original backup and reloads a v2 envelope', () => {
  const storage = priorStorage(), v1 = storage.getItem(LEGACY_COURSE_KEY), result = migrate();
  assert.deepEqual(commit(storage,result),result);
  assert.equal(storage.getItem(LEGACY_COURSE_KEY),v1);
  assert.equal(storage.getItem(JOURNAL_KEY),null);
  const backup = storage.getItem(BACKUP_KEY);
  assert.deepEqual(JSON.parse(backup),result.retainedLegacy);
  assert.deepEqual(prepareStoredProgress(storage,course,snapshot,mapping,labs),result);
  result.course.readings = [course.readings[0].id]; commit(storage,result);
  assert.equal(storage.getItem(BACKUP_KEY),backup);
});
for (let point = 1; point <= 5; point++) test(`failure at transaction operation ${point} restores every original storage value`, () => {
  const storage = priorStorage(), before = new Map(storage.values); storage.failAt = point;
  assert.throws(() => commit(storage,migrate()),/existing progress retained/);
  assert.deepEqual(storage.values,before);
});
test('blocked writes preserve original data and leave the migrated result available for export', () => {
  const storage = priorStorage(), before = new Map(storage.values); storage.blocked = true;
  const result = migrate();
  assert.throws(() => commit(storage,result),/existing progress retained/);
  assert.deepEqual(storage.values,before);
  assert.deepEqual(parseBundle(exportBundleV2(result)),result);
});
test('silent storage write failure is detected and rolled back', () => {
  const storage = priorStorage(), before = new Map(storage.values), set = storage.setItem.bind(storage);
  storage.setItem = (key,value) => { if (key !== COURSE_KEY_V2) set(key,value); };
  assert.throws(() => commit(storage,migrate()),/existing progress retained/);
  assert.deepEqual(storage.values,before);
});
test('failed rollback retains a recovery journal and refuses another import until recovery', () => {
  const storage = priorStorage(), before = new Map(storage.values), set = storage.setItem.bind(storage);
  let labWrites = 0;
  storage.setItem = (key,value) => {
    if (key === COURSE_KEY_V2 || (key === PROGRESS_KEY && ++labWrites > 1)) throw new Error('persistent failure');
    set(key,value);
  };
  const incoming = migrate(); incoming.labs.labs['p1-loop'].attempts = 4;
  assert.throws(() => commit(storage,incoming),/rollback is incomplete/);
  assert.throws(() => recoverTransaction(storage),/could not be restored/);
  assert.ok(storage.getItem(JOURNAL_KEY));
  assert.throws(() => commit(storage,migrate()),/Recover/);
  storage.setItem = set;
  assert.equal(recoverTransaction(storage),true);
  assert.deepEqual(storage.values,before);
});
test('interrupted transactions restore all raw strings, including an existing v2 record/backup', () => {
  const storage = priorStorage(); commit(storage,migrate());
  const before = new Map(storage.values), rawBefore = Object.fromEntries([PROGRESS_KEY,COURSE_KEY_V2,BACKUP_KEY].map(k => [k,storage.getItem(k)]));
  storage.values.set(JOURNAL_KEY,JSON.stringify({version:1,before:rawBefore}));
  storage.values.set(COURSE_KEY_V2,'partial new v2 value'); storage.values.delete(PROGRESS_KEY);
  assert.throws(() => prepareStoredProgress(storage,course,snapshot,mapping,labs),/Recover/);
  assert.equal(recoverTransaction(storage),true);
  assert.deepEqual(storage.values,before); assert.equal(recoverTransaction(storage),false);
});
test('corrupt/forged recovery journals do not mutate existing keys', () => {
  for (const raw of ['{broken',JSON.stringify({version:1,before:{'arbitrary-key':'overwrite'}})]) {
    const storage = priorStorage(); storage.values.set(JOURNAL_KEY,raw); const before = new Map(storage.values);
    assert.throws(() => recoverTransaction(storage)); assert.deepEqual(storage.values,before);
  }
});
test('missing exclusive locks disable persistent transactions and supplied locks serialize operations', async () => {
  await assert.rejects(withProgressLock(null,()=>{}),/exclusive storage lock/);
  let queue = Promise.resolve(), running = 0;
  const locks = {request(name, options, operation) {
    assert.equal(name,'rl-course-progress:v2'); assert.equal(options.mode,'exclusive');
    const next = queue.then(async () => { assert.equal(running++,0); try { return await operation(); } finally { running--; } });
    queue = next.catch(()=>{}); return next;
  }};
  await Promise.all([1,2].map(value => withProgressLock(locks,async () => { await Promise.resolve(); return value; })));
});
