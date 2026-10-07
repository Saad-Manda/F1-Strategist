// R1 contracts. R2 uses fresh preview progress; R7 activates learner migration.
import {validateProgress, PROGRESS_KEY} from '../labs/assets/storage.js?v=reading-20261006-r8';
import {validateCourseV2} from './course-model-v2.js?v=reading-20261006-r8';

export const COURSE_KEY_V2 = 'rl-course:v2';
export const LEGACY_COURSE_KEY = 'rl-course:v1';
export const JOURNAL_KEY = 'rl-course:transaction:v2';
export const BACKUP_KEY = 'rl-course:migration-backup:v1';
export const MIGRATION_MESSAGE = 'The course was reorganized. Your lab work was retained; revised readings may need review. You can export your retained progress.';
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const equal = (a,b) => JSON.stringify(a) === JSON.stringify(b);
const clone = v => structuredClone(v);
const knownLabs = course => course.lessons.flatMap(l => l.practice ? [l.practice.labId] : []);
function ids(values, allowed) {
  if (!Array.isArray(values) || values.some(v => typeof v !== 'string' || !allowed.includes(v)) || new Set(values).size !== values.length) throw new Error('Unknown or duplicate progress IDs.');
  return [...values];
}
function exactKeys(record, allowed) {
  if (!object(record) || Object.keys(record).some(k => !allowed.includes(k))) throw new Error('Invalid progress fields.');
}
export const emptyCourseV2 = () => ({version:2, readings:[], browser:[], checks:{}, resume:null, migration:null});
const blankLabs = () => ({version:1,labs:{}});

export function validateLegacyCourse(data, snapshot) {
  const course = snapshot.course;
  exactKeys(data, ['version','readings','browser','checks','resume']);
  if (data.version !== 1 || !object(data.checks)) throw new Error('Invalid legacy course progress.');
  const result = {version:1, readings:ids(data.readings, course.resources.map(r => r.id)), browser:ids(data.browser, course.lessons.map(l => l.id)), checks:{}, resume:null};
  for (const [key,values] of Object.entries(data.checks)) {
    const module = course.modules.find(m => m.id === key);
    if (!module) throw new Error('Unknown legacy checkpoint.');
    result.checks[key] = ids(values, module.projectCheckpoint.checks.map(c => c.id));
  }
  if (data.resume !== null) {
    const r = data.resume;
    if (!object(r)) throw new Error('Invalid legacy resume.');
    if (r.kind === 'checkpoint') {
      exactKeys(r,['kind','module']);
      if (!course.modules.some(m => m.id === r.module)) throw new Error('Unknown legacy module.');
    } else if (r.kind === 'lesson') {
      exactKeys(r,['kind','lesson','step','resource']);
      const lesson = course.lessons.find(l => l.id === r.lesson);
      if (!lesson || !['theory','browser','python'].includes(r.step) ||
          (r.resource !== undefined && (r.step !== 'theory' || !lesson.required.includes(r.resource)))) throw new Error('Invalid legacy lesson resume.');
    } else throw new Error('Unknown legacy resume kind.');
    result.resume = clone(r);
  }
  return result;
}

export function validateCourseProgressV2(data, course) {
  exactKeys(data,['version','readings','browser','checks','resume','migration']);
  if (data.version !== 2 || !object(data.checks)) throw new Error('Invalid v2 course progress.');
  const result = {version:2, readings:ids(data.readings,course.readings.map(r => r.id)), browser:ids(data.browser,knownLabs(course)), checks:{}, resume:null, migration:null};
  for (const [key,values] of Object.entries(data.checks)) {
    const module = course.modules.find(m => m.id === key);
    if (!module) throw new Error('Unknown v2 checkpoint.');
    result.checks[key] = ids(values,module.projectCheckpoint.checks.map(c => c.id));
  }
  if (data.migration !== null) {
    exactKeys(data.migration,['fromVersion','noticePending']);
    if (data.migration.fromVersion !== 1 || typeof data.migration.noticePending !== 'boolean') throw new Error('Invalid migration notice.');
    result.migration = clone(data.migration);
  }
  if (data.resume !== null) {
    const r = data.resume;
    if (!object(r)) throw new Error('Invalid v2 resume.');
    if (r.kind === 'reading') {
      exactKeys(r,['kind','reading']);
      if (!course.readings.some(reading => reading.id === r.reading)) throw new Error('Unknown resume reading.');
    } else if (r.kind === 'lesson') {
      exactKeys(r,['kind','lesson','step']);
      const lesson = course.lessons.find(l => l.id === r.lesson);
      if (!lesson?.practice || !['browser','python'].includes(r.step)) throw new Error('Invalid practice resume.');
    } else if (r.kind === 'checkpoint') {
      exactKeys(r,['kind','module']);
      if (!course.modules.some(m => m.id === r.module)) throw new Error('Unknown resume module.');
    } else throw new Error('Unknown v2 resume kind.');
    result.resume = clone(r);
  }
  return result;
}

const meaningFields = ['id','phase','route','mode','model','objective','browser','localTask','acceptance','dependencies'];
export function validateMigrationMap(mapping, snapshot, course, labs) {
  validateCourseV2(course,labs);
  if (!object(mapping) || mapping.version !== 1 || mapping.fromCourseVersion !== 1 || mapping.toCourseVersion !== 2 || typeof mapping.reviewedOn !== 'string' || !mapping.reviewedOn.trim()) throw new Error('Invalid migration map.');
  const sameInventory = (records, keys, expected) => {
    if (!Array.isArray(records) || records.some(r => !object(r) || typeof r.reason !== 'string' || !r.reason.trim())) throw new Error('Missing reviewed migration decisions.');
    const actual = records.map(r => keys.map(k => r[k]).join('|'));
    if (new Set(actual).size !== actual.length || !equal(actual.sort(),expected.sort())) throw new Error('Incomplete or duplicate migration decisions.');
  };
  sameInventory(mapping.readings,['oldId'],snapshot.course.resources.map(r => r.id));
  sameInventory(mapping.practice,['oldLesson'],snapshot.course.lessons.map(l => l.id));
  sameInventory(mapping.checklists,['oldModule','oldCheck'],snapshot.course.modules.flatMap(m => m.projectCheckpoint.checks.map(c => `${m.id}|${c.id}`)));
  for (const decision of mapping.readings) {
    ids(decision.newIds,course.readings.map(r => r.id));
    if (!['unread','equivalent'].includes(decision.decision) || (decision.decision === 'unread' && decision.newIds.length) ||
        (decision.decision === 'equivalent' && (!decision.newIds.length || decision.newIds.some(k => course.readings.find(r => r.id === k).status !== 'authored')))) throw new Error('Unreviewed reading equivalence.');
  }
  for (const decision of mapping.practice) {
    const old = snapshot.labs.labs.find(l => l.id === decision.labId);
    const lab = labs.labs.find(l => l.id === decision.labId);
    const lesson = course.lessons.find(l => l.id === decision.newLesson);
    if (decision.decision !== 'retain' || decision.oldLesson !== decision.labId || !old || !lab || lesson?.practice?.labId !== decision.labId ||
        meaningFields.some(k => !equal(old[k],lab[k]))) throw new Error('Changed/unmapped practice meaning.');
  }
  for (const decision of mapping.checklists) {
    const old = snapshot.course.modules.find(m => m.id === decision.oldModule)?.projectCheckpoint.checks.find(c => c.id === decision.oldCheck);
    const current = course.modules.find(m => m.id === decision.newModule)?.projectCheckpoint.checks.find(c => c.id === decision.newCheck);
    if (decision.decision !== 'retain' || !old || !current || old.text !== current.text || current.text !== decision.text) throw new Error('Changed checklist meaning.');
  }
  if (!Array.isArray(mapping.resume) || new Set(mapping.resume.map(r => r.oldLesson)).size !== mapping.resume.length ||
      !equal(mapping.resume.map(r => r.oldLesson).sort(),snapshot.course.lessons.map(l => l.id).sort()) ||
      mapping.resume.some(r => !course.modules.some(m => m.id === r.module) ||
        (r.newLesson !== null && !course.lessons.some(l => l.id === r.newLesson && l.module === r.module)))) throw new Error('Invalid resume translation map.');
  return mapping;
}

export function lessonProgressV2(course, data, labs, key) {
  const lesson = course.lessons.find(l => l.id === key);
  if (!lesson) throw new Error('Unknown lesson.');
  const missing = lesson.required.filter(r => !data.readings.includes(r));
  const labId = lesson.practice?.labId;
  const browser = !labId || data.browser.includes(labId);
  const record = labId && labs.labs[labId];
  const python = !labId || Boolean(record?.status === 'completed' && record.verified && record.explanation.trim());
  return {missing, browser, python, complete:!missing.length && browser && python,
    step:missing.length ? 'theory' : !browser ? 'browser' : !python ? 'python' : null};
}
export function unfinishedStep(course, data, labs, {lessonId=null, moduleId=null} = {}) {
  const modules = moduleId ? course.modules.filter(m => m.id === moduleId) : course.modules;
  const byId = new Map(course.readings.map(r => [r.id,r]));
  const reading = key => ({kind:'reading',reading:key,url:byId.get(key).route});
  const forLesson = lesson => {
    const state = lessonProgressV2(course,data,labs,lesson.id);
    if (state.missing.length) return reading(state.missing[0]);
    if (state.step) return {kind:'lesson',lesson:lesson.id,step:state.step,
      url:`${lesson.practice.route}?lesson=${lesson.id}&step=${state.step}#${state.step === 'browser' ? 'challenge' : 'implement'}`};
    return null;
  };
  const requested = course.lessons.find(l => l.id === lessonId && modules.some(m => m.id === l.module));
  if (requested) {
    const target = forLesson(requested);
    if (target) return target;
  }
  for (const module of modules) {
    for (const key of module.lessons) {
      const target = forLesson(course.lessons.find(l => l.id === key));
      if (target) return target;
    }
    const application = module.applications.find(key => !data.readings.includes(key));
    if (application) return reading(application);
    if (module.projectCheckpoint.checks.some(c => !(data.checks[module.id] || []).includes(c.id))) return {kind:'checkpoint',module:module.id,url:module.projectCheckpoint.route};
  }
  return {kind:'review',url:'roadmap.html'};
}

export function migrateLegacy(courseData, labData, course, snapshot, mapping, labs) {
  validateMigrationMap(mapping,snapshot,course,labs);
  const old = courseData === null ? null : validateLegacyCourse(courseData,snapshot);
  const retainedLabs = validateProgress(labData,snapshot.labs.labs.map(l => l.id));
  const currentLabs = validateProgress(retainedLabs,knownLabs(course));
  const data = emptyCourseV2();
  data.migration = {fromVersion:1,noticePending:true};
  if (old) {
    for (const decision of mapping.readings) if (decision.decision === 'equivalent' && old.readings.includes(decision.oldId)) data.readings.push(...decision.newIds);
    data.readings = [...new Set(data.readings)];
    for (const decision of mapping.practice) if (old.browser.includes(decision.oldLesson)) data.browser.push(decision.labId);
    for (const decision of mapping.checklists) if ((old.checks[decision.oldModule] || []).includes(decision.oldCheck)) {
      data.checks[decision.newModule] ??= []; data.checks[decision.newModule].push(decision.newCheck);
    }
    const previous = old.resume;
    const targetMap = previous?.kind === 'lesson' && mapping.resume.find(r => r.oldLesson === previous.lesson);
    let target;
    if (previous?.kind === 'lesson' && previous.step === 'theory' && previous.resource) {
      const decision = mapping.readings.find(r => r.oldId === previous.resource);
      const nextReading = decision?.newIds.find(key => !data.readings.includes(key));
      if (nextReading) target = {kind:'reading',reading:nextReading};
    }
    target ??= unfinishedStep(course,data,currentLabs,{lessonId:targetMap?.newLesson ?? null,
      moduleId:targetMap?.module ?? (previous?.kind === 'checkpoint' ? previous.module : null)});
    const {url,...resume} = target;
    data.resume = resume.kind === 'review' ? null : resume;
  } else {
    const {url,...resume} = unfinishedStep(course,data,currentLabs);
    data.resume = resume.kind === 'review' ? null : resume;
  }
  return {course:validateCourseProgressV2(data,course),labs:currentLabs,retainedLegacy:{course:old,labs:retainedLabs}};
}

export function validateBundleV2(raw, course, snapshot, mapping, labs) {
  validateCourseV2(course,labs);
  if (typeof raw !== 'string' || raw.length > 1000000) throw new Error('Progress file is too large.');
  const value = JSON.parse(raw);
  if (!object(value)) throw new Error('Invalid progress file.');
  if (value.format === 'rl-course-progress' && value.version === 2) {
    exactKeys(value,['format','version','course','labs','retainedLegacy']);
    const data = validateCourseProgressV2(value.course,course);
    const labData = validateProgress(value.labs,knownLabs(course));
    let retainedLegacy = null;
    if (value.retainedLegacy !== null) {
      exactKeys(value.retainedLegacy,['course','labs']);
      retainedLegacy = {course:value.retainedLegacy.course === null ? null : validateLegacyCourse(value.retainedLegacy.course,snapshot),
        labs:validateProgress(value.retainedLegacy.labs,snapshot.labs.labs.map(l => l.id))};
    }
    return {course:data,labs:labData,retainedLegacy};
  }
  if (value.format === 'rl-course-progress' && value.version === 1) {
    exactKeys(value,['format','version','course','labs']);
    return migrateLegacy(value.course,value.labs,course,snapshot,mapping,labs);
  }
  if (value.format !== undefined || value.course !== undefined) throw new Error('Unsupported progress bundle.');
  return migrateLegacy(null,value,course,snapshot,mapping,labs);
}
export function exportBundleV2(bundle) {
  return JSON.stringify({format:'rl-course-progress',version:2,...clone(bundle)},null,2);
}
export function migrationNoticeSeen(data, course) {
  const next = validateCourseProgressV2(data,course);
  if (next.migration) next.migration.noticePending = false;
  return next;
}

const transactionKeys = [PROGRESS_KEY,COURSE_KEY_V2,BACKUP_KEY];
function restoreValues(storage, before) {
  let restored = true;
  for (const key of transactionKeys) {
    try {
      if (storage.getItem(key) === before[key]) continue;
      if (before[key] === null) storage.removeItem(key); else storage.setItem(key,before[key]);
      if (storage.getItem(key) !== before[key]) throw new Error('Restore verification failed.');
    } catch { restored = false; }
  }
  return restored;
}
export function recoverTransaction(storage) {
  const raw = storage.getItem(JOURNAL_KEY);
  if (raw === null) return false;
  const journal = JSON.parse(raw);
  exactKeys(journal,['version','before']);
  if (journal.version !== 1 || !object(journal.before) || !equal(Object.keys(journal.before).sort(),[...transactionKeys].sort()) ||
      Object.values(journal.before).some(v => v !== null && typeof v !== 'string')) throw new Error('Invalid transaction journal; existing storage was not changed.');
  if (!restoreValues(storage,journal.before)) throw new Error('Interrupted import could not be restored. Retained progress can still be exported; retry when storage is available.');
  storage.removeItem(JOURNAL_KEY);
  if (storage.getItem(JOURNAL_KEY) !== null) throw new Error('Recovery journal could not be cleared.');
  return true;
}
export function prepareStoredProgress(storage, course, snapshot, mapping, labs) {
  // Read-only preparation; the R7 caller must recover an outstanding journal first.
  if (storage.getItem(JOURNAL_KEY) !== null) throw new Error('Recover the interrupted transaction before loading progress.');
  const rawCourse = storage.getItem(COURSE_KEY_V2);
  const rawLabs = storage.getItem(PROGRESS_KEY);
  const labData = rawLabs === null ? blankLabs() : JSON.parse(rawLabs);
  if (rawCourse !== null) {
    const saved = JSON.parse(rawCourse);
    exactKeys(saved,['version','course','retainedLegacy']);
    if (saved.version !== 2) throw new Error('Unsupported saved v2 progress.');
    return validateBundleV2(exportBundleV2({course:saved.course,labs:labData,retainedLegacy:saved.retainedLegacy}),course,snapshot,mapping,labs);
  }
  const legacy = storage.getItem(LEGACY_COURSE_KEY);
  if (legacy !== null || rawLabs !== null) return migrateLegacy(legacy === null ? null : JSON.parse(legacy),labData,course,snapshot,mapping,labs);
  return {course:emptyCourseV2(),labs:blankLabs(),retainedLegacy:null};
}
export function commitProgress(storage, incoming, course, snapshot, mapping, labs) {
  // Validate the entire import before reads that can recover/mutate storage.
  const valid = validateBundleV2(exportBundleV2(incoming),course,snapshot,mapping,labs);
  if (storage.getItem(JOURNAL_KEY) !== null) throw new Error('Recover the interrupted transaction before importing.');
  const before = Object.fromEntries(transactionKeys.map(key => [key,storage.getItem(key)]));
  const after = {
    [PROGRESS_KEY]:JSON.stringify(valid.labs),
    [COURSE_KEY_V2]:JSON.stringify({version:2,course:valid.course,retainedLegacy:valid.retainedLegacy}),
    [BACKUP_KEY]:before[BACKUP_KEY] ?? (valid.retainedLegacy ? JSON.stringify(valid.retainedLegacy) : null),
  };
  try {
    storage.setItem(JOURNAL_KEY,JSON.stringify({version:1,before}));
    if (storage.getItem(JOURNAL_KEY) !== JSON.stringify({version:1,before})) throw new Error('Journal write failed.');
    for (const key of transactionKeys) {
      if (after[key] === null) continue;
      storage.setItem(key,after[key]);
      if (storage.getItem(key) !== after[key]) throw new Error('Progress write verification failed.');
    }
    storage.removeItem(JOURNAL_KEY);
    if (storage.getItem(JOURNAL_KEY) !== null) throw new Error('Journal clear failed.');
  } catch (cause) {
    const restored = restoreValues(storage,before);
    let cleared = false;
    if (restored) try {
      if (storage.getItem(JOURNAL_KEY) !== null) storage.removeItem(JOURNAL_KEY);
      cleared = storage.getItem(JOURNAL_KEY) === null;
    } catch {}
    throw new Error(restored && cleared ? 'Import could not be saved; existing progress retained.' :
      'Import failed and rollback is incomplete. Retain/export the current progress and retry recovery before further writes.', {cause});
  }
  return valid;
}

export async function withProgressLock(locks, operation) {
  if (!locks || typeof locks.request !== 'function') throw new Error('Persistent migration/import needs an exclusive storage lock. Keep/export progress on this page when unavailable.');
  return locks.request('rl-course-progress:v2',{mode:'exclusive'},operation);
}
