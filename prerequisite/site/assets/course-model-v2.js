// Inactive until the R7 switch. Pure model/navigation contract, no storage access.
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const id = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;
const readingId = /^[a-z][a-z0-9-]*\/[a-z][a-z0-9-]*$/;
export function canonicalRoute(kind, key) {
  if (typeof key !== 'string' || !(kind === 'reading' || kind === 'application' ? readingId : id).test(key)) throw new Error('Invalid semantic identity.');
  const prefix = {reading:'readings', application:'applications', lesson:'lessons', module:'modules'}[kind];
  if (!prefix) throw new Error('Unknown route kind.');
  return `${prefix}/${key}.html`;
}
export function validateCourseV2(course, labs) {
  if (!object(course) || course.schemaVersion !== 2) throw new Error('Unsupported v2 course schema.');
  const maps = {};
  for (const name of ['modules', 'lessons', 'readings', 'projectStages']) {
    if (!Array.isArray(course[name]) || !course[name].length || course[name].some(r => !object(r))) throw new Error(`Invalid ${name}.`);
    if (name === 'projectStages') continue;
    const pattern = name === 'readings' ? readingId : id;
    if (course[name].some(r => typeof r.id !== 'string' || !pattern.test(r.id))) throw new Error(`Invalid ${name} IDs.`);
    maps[name] = new Map(course[name].map(r => [r.id, r]));
    if (maps[name].size !== course[name].length) throw new Error(`Duplicate ${name} IDs.`);
  }
  const list = (r, field, known, required = false) => {
    const values = r[field];
    if (!Array.isArray(values) || (required && !values.length) || values.some(k => typeof k !== 'string' || !known.has(k)) || new Set(values).size !== values.length) throw new Error(`Invalid ${field} membership: ${r.id}.`);
    return values;
  };
  const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const route = (r, kind) => { if (r.route !== canonicalRoute(kind, r.id)) throw new Error(`Noncanonical route: ${r.id}.`); };
  const labMap = new Map(labs.labs.map(l => [l.id, l]));
  if (!equal(course.modules.map(m => m.phase).sort(), labs.phases.map(p => p.id).sort())) throw new Error('Invalid phase mappings.');
  const membership = [], lessonOrder = [], sequence = [];
  for (const module of course.modules) {
    route(module, 'module');
    if (['title','objective'].some(k => typeof module[k] !== 'string' || !module[k].trim())) throw new Error('Missing module title/objective.');
    const owned = list(module, 'lessons', maps.lessons, true);
    if (!equal(owned, course.lessons.filter(l => l.module === module.id).map(l => l.id))) throw new Error('Malformed lesson ownership.');
    lessonOrder.push(...owned);
    for (const key of owned) {
      const lesson = maps.lessons.get(key);
      for (const [field, role] of [['required','core'], ['optional','further-depth']]) {
        const values = list(lesson, field, maps.readings, field === 'required');
        for (const readingKey of values) {
          const reading = maps.readings.get(readingKey);
          if (reading.module !== module.id || reading.lesson !== key || reading.role !== role) throw new Error('Malformed reading ownership/role.');
        }
        membership.push(...values); sequence.push(...values);
      }
    }
    const apps = list(module, 'applications', maps.readings, true);
    for (const key of apps) {
      const reading = maps.readings.get(key);
      if (reading.module !== module.id || reading.lesson !== null || reading.role !== 'application') throw new Error('Malformed application ownership.');
    }
    membership.push(...apps); sequence.push(...apps);
    const checkpoint = module.projectCheckpoint;
    if (!object(checkpoint) || checkpoint.route !== module.route + '#project-checkpoint' || !equal(checkpoint.required, apps) ||
        !Array.isArray(checkpoint.checks) || !checkpoint.checks.length || checkpoint.checks.some(c => !object(c) || !id.test(c.id) || typeof c.text !== 'string' || !c.text.trim()) ||
        new Set(checkpoint.checks.map(c => c.id)).size !== checkpoint.checks.length) throw new Error('Invalid checkpoint.');
  }
  if (!equal(lessonOrder, course.lessons.map(l => l.id))) throw new Error('Invalid lesson order.');
  if (membership.length !== maps.readings.size || new Set(membership).size !== membership.length) throw new Error('Each reading needs one sequence.');
  const practice = [];
  for (const lesson of course.lessons) {
    route(lesson, 'lesson');
    if (typeof lesson.title !== 'string' || !lesson.title.trim()) throw new Error('Missing lesson title.');
    if (!maps.modules.has(lesson.module)) throw new Error('Unknown owning module.');
    const prereqs = list(lesson, 'prerequisites', maps.lessons);
    if (prereqs.some(k => course.lessons.indexOf(maps.lessons.get(k)) >= course.lessons.indexOf(lesson))) throw new Error('Future/cyclic lesson prerequisite.');
    if (lesson.practice === null) continue;
    const lab = object(lesson.practice) && labMap.get(lesson.practice.labId);
    if (!lab || lesson.practice.route !== 'labs/' + lab.route || maps.modules.get(lesson.module).phase !== lab.phase) throw new Error('Invalid practice mapping.');
    practice.push(lab.id);
  }
  if (!equal(practice.sort(), [...labMap.keys()].sort())) throw new Error('Every lab needs exactly one practice mapping.');
  const taught = new Set();
  for (const key of sequence) {
    const reading = maps.readings.get(key);
    if (list(reading, 'requires', maps.readings).some(k => !taught.has(k))) throw new Error('Unmet/further-depth prerequisite.');
    if (reading.role !== 'further-depth') taught.add(key);
  }
  for (const reading of course.readings) {
    if (['kind','anchor','heading','through','instruction'].some(k => Object.hasOwn(reading,k))) throw new Error('Legacy section-assignment fields are not v2 readings.');
    const kind = reading.role === 'application' ? 'application' : 'reading';
    route(reading, kind);
    if (reading.source !== 'content/' + canonicalRoute(kind, reading.id) || !['core','further-depth','application'].includes(reading.role) ||
        !['planned','authored'].includes(reading.status) || typeof reading.title !== 'string' || !reading.title.trim() ||
        typeof reading.goal !== 'string' || !reading.goal.trim() || !equal(reading.teaches,[reading.id]) || !Number.isInteger(reading.minutes) || reading.minutes < 1 || reading.minutes > 60) throw new Error('Invalid reading metadata/source.');
  }
  if (!equal(course.projectStages.map(s => s.phase), ['0','0.5','1','2','3','3.5','4','5','6','7','8','9']) ||
      course.projectStages.some(s => s.module !== (course.modules.find(m => m.phase === s.phase)?.id ?? null))) throw new Error('Invalid project roadmap.');
  return course;
}
export function readingContext(course, key) {
  const reading = course.readings.find(r => r.id === key);
  if (!reading) return null;
  const module = course.modules.find(m => m.id === reading.module);
  const lesson = course.lessons.find(l => l.id === reading.lesson);
  const sequence = !lesson ? module.applications : reading.role === 'core' ? lesson.required : lesson.optional;
  const index = sequence.indexOf(key);
  const byId = new Map(course.readings.map(r => [r.id,r]));
  let next, nextLabel;
  if (index + 1 < sequence.length) {
    const following = byId.get(sequence[index + 1]); next = following.route; nextLabel = 'Continue to ' + following.title;
  } else if (reading.role === 'application') {
    next = module.projectCheckpoint.route; nextLabel = 'Continue to project checkpoint';
  } else if (reading.role === 'further-depth') {
    next = lesson.route; nextLabel = 'Return to lesson';
  } else if (lesson.practice) {
    next = `${lesson.practice.route}?lesson=${lesson.id}&step=browser#challenge`; nextLabel = 'Continue to Browser lab';
  } else {
    const position = module.lessons.indexOf(lesson.id);
    next = position + 1 < module.lessons.length ? course.lessons.find(l => l.id === module.lessons[position + 1]).route : byId.get(module.applications[0]).route;
    nextLabel = position + 1 < module.lessons.length ? 'Continue to next lesson' : 'Continue to project application';
  }
  return {reading:key, module:module.id, lesson:reading.lesson, role:reading.role, moduleNumber:course.modules.indexOf(module)+1,
    lessonNumber:lesson ? module.lessons.indexOf(lesson.id)+1 : null, position:index+1, total:sequence.length,
    previous:index ? byId.get(sequence[index-1]).route : null, next, nextLabel, acknowledge:['core','application'].includes(reading.role)};
}
export function resolveContextV2(course, route, search = '') {
  const query = new URLSearchParams(search);
  if (['lesson','module','step'].some(k => query.getAll(k).length > 1)) return null;
  const reading = course.readings.find(r => r.route === route);
  if (!reading) return null;
  if ((query.has('lesson') && query.get('lesson') !== reading.lesson) ||
      (query.has('module') && query.get('module') !== reading.module) ||
      (query.has('step') && query.get('step') !== 'theory')) return null;
  return readingContext(course, reading.id);
}
export function resolveRelocation(relocations, oldUrl) {
  if (typeof oldUrl !== 'string') return null;
  return relocations.routes.find(r => r.oldUrl === oldUrl) ?? null;
}
export function validateRelocations(relocations, course, snapshot) {
  if (!object(relocations) || relocations.version !== 1 || typeof relocations.reviewedOn !== 'string' || !relocations.reviewedOn.trim() ||
      !Array.isArray(relocations.routes) || relocations.routes.some(r => !object(r))) throw new Error('Invalid reviewed relocations.');
  const knownOld = new Set(snapshot.course.resources.map(r => r.id));
  const oldUrls = relocations.routes.map(r => r.oldUrl);
  if (oldUrls.length !== knownOld.size || new Set(oldUrls).size !== oldUrls.length || oldUrls.some(k => !knownOld.has(k))) throw new Error('Incomplete/unknown relocation identities.');
  const allowed = new Set([...course.readings.map(r => r.route),...course.modules.map(m => m.route),...course.modules.map(m => 'glossary.html#' + m.id)]);
  for (const relocation of relocations.routes) {
    const module = course.modules.find(m => m.id === relocation.module);
    const targets = relocation.targets;
    if (!module || relocation.fallback !== module.route || typeof relocation.reason !== 'string' || !relocation.reason.trim() ||
        !Array.isArray(targets) || !targets.length || targets.some(t => !allowed.has(t)) || new Set(targets).size !== targets.length ||
        relocation.kind !== (targets.length === 1 ? 'redirect' : 'choices')) throw new Error('Invalid canonical relocation targets.');
  }
  return relocations;
}
