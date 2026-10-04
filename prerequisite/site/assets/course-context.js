// Pure context validation and navigation. No learner storage or arbitrary return URLs.
export const steps = ['theory', 'browser', 'python'];
export function readingTarget(resource, lesson) {
  return resource.route + `?lesson=${encodeURIComponent(lesson)}&step=theory` + (resource.anchor ? `#${resource.anchor}` : '');
}
export function resolveCourseContext(course, route, search, hash = '') {
  const query = new URLSearchParams(search);
  if (['lesson', 'step', 'module'].some(key => query.getAll(key).length > 1)) return null;
  const lessonId = query.get('lesson'), step = query.get('step'), moduleId = query.get('module');
  const resources = new Map(course.resources.map(r => [r.id, r]));
  if (moduleId !== null) {
    if (lessonId !== null || step !== null) return null;
    const module = course.modules.find(m => m.id === moduleId);
    if (!module) return null;
    const readings = module.projectCheckpoint.required.map(id => resources.get(id));
    const index = readings.findIndex(r => r?.route === route);
    if (index < 0) return null;
    return {kind: 'checkpoint', module, resource:readings[index], return: module.projectCheckpoint.route,
      title: module.projectCheckpoint.preparationLabel,
      next: index + 1 < readings.length ? `${readings[index + 1].route}?module=${encodeURIComponent(module.id)}` : module.projectCheckpoint.route,
      nextLabel: index + 1 < readings.length ? `Read project bridge: ${readings[index + 1].title}` : 'Return to project checkpoint'};
  }
  const lesson = course.lessons.find(l => l.id === lessonId);
  const module = lesson && course.modules.find(m => m.id === lesson.module);
  if (!lesson || !module || !steps.includes(step)) return null;
  const index = course.lessons.indexOf(lesson);
  const after = lesson.id === module.lessons.at(-1) ? module.projectCheckpoint.route : course.lessons[index + 1]?.route;
  const afterLabel = lesson.id === module.lessons.at(-1) ? module.projectCheckpoint.preparationLabel : `Next lesson: ${course.lessons[index + 1]?.title}`;
  if (step === 'theory') {
    const required = lesson.required.map(id => resources.get(id));
    const optional = lesson.optional.map(id => resources.get(id));
    if (![...required, ...optional].some(r => r?.route === route)) return null;
    const exact = required.findIndex(r => r.route === route && (r.anchor ? `#${r.anchor}` : '') === hash);
    const current = exact >= 0 ? exact : required.findIndex(r => r.route === route);
    const resource = current >= 0 ? required[current] : optional.find(r => r.route === route);
    const nextReading = current >= 0 && required[current + 1];
    return {kind:'lesson', lesson, module, step, resource, return:lesson.route + '#theory',
      next: current < 0 ? lesson.route + '#theory' : nextReading ? readingTarget(nextReading, lesson.id) : `${lesson.lab}?lesson=${encodeURIComponent(lesson.id)}&step=browser#challenge`,
      nextLabel: current < 0 ? 'Return to required theory' : nextReading ? `Read theory: ${nextReading.title}` : 'Open browser lab'};
  }
  if (route !== lesson.lab) return null;
  return {kind:'lesson', lesson, module, step, return:lesson.route + '#theory',
    next: step === 'browser' ? `${lesson.lab}?lesson=${encodeURIComponent(lesson.id)}&step=python#implement` : after,
    nextLabel: step === 'browser' ? 'Practice in Python' : afterLabel};
}
