export const PROGRESS_KEY = 'rl-labs:v1';
const blank = () => ({ attempts: 0, prediction: '', explanation: '', status: 'not-started', hints: 0, solution: false, verified: false });

export function validateProgress(data, knownIds) {
  if (!data || data.version !== 1 || !data.labs || Array.isArray(data.labs) || typeof data.labs !== 'object') {
    throw new Error('This is not a version 1 RL lab progress file.');
  }
  const labs = {};
  for (const [id, record] of Object.entries(data.labs)) {
    if (!knownIds.includes(id) || !record || typeof record !== 'object') throw new Error('Unknown lab or invalid record.');
    const r = { ...blank(), ...record };
    if (!Number.isInteger(r.attempts) || r.attempts < 0 || r.attempts > 1000000
      || !Number.isInteger(r.hints) || r.hints < 0 || r.hints > 3
      || typeof r.solution !== 'boolean' || typeof r.verified !== 'boolean'
      || !['not-started', 'attempted', 'completed'].includes(r.status)
      || typeof r.prediction !== 'string' || r.prediction.length > 100
      || typeof r.explanation !== 'string' || r.explanation.length > 6000
      || (r.status === 'completed' && (!r.verified || !r.explanation.trim()))) {
      throw new Error('A progress record contains invalid values.');
    }
    labs[id] = Object.fromEntries(Object.keys(blank()).map(key => [key, r[key]]));
  }
  return { version: 1, labs };
}

export function createProgressStore(knownIds, suppliedStorage) {
  let storage;
  let data = { version: 1, labs: {} };
  let warning = '';
  let writable = true;
  const listeners = new Set();
  function changed() { for (const listener of listeners) listener(); }
  try {
    storage = suppliedStorage === undefined ? window.localStorage : suppliedStorage;
    if (!storage) throw new Error('Storage unavailable');
    const raw = storage.getItem(PROGRESS_KEY);
    if (raw) data = validateProgress(JSON.parse(raw), knownIds);
  } catch {
    writable = false;
    warning = 'Saved progress is unavailable or unreadable. You can still use the lab and export this session.';
  }
  function save() {
    try {
      if (!storage || !writable) throw new Error('Storage unavailable');
      storage.setItem(PROGRESS_KEY, JSON.stringify(data));
      warning = '';
    } catch {
      warning = 'Progress is kept for this session only. Export it before leaving this page.';
    }
  }
  return {
    get warning() { return warning; },
    get(id) { return { ...blank(), ...data.labs[id] }; },
    set(id, patch) {
      data = validateProgress({ version: 1, labs: { ...data.labs, [id]: { ...this.get(id), ...patch } } }, knownIds);
      save();
      changed();
    },
    export() { return JSON.stringify(data, null, 2); },
    import(raw) {
      if (raw.length > 200000) throw new Error('Progress file is too large.');
      const incoming = validateProgress(JSON.parse(raw), knownIds);
      data = incoming;
      writable = true;
      save();
      changed();
    },
    reset(id) { delete data.labs[id]; save(); changed(); },
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    refresh() {
      try { data = validateProgress(JSON.parse(storage.getItem(PROGRESS_KEY) || '{"version":1,"labs":{}}'), knownIds); warning = ''; writable = true; }
      catch { writable = false; warning = 'Saved progress is unavailable or unreadable. Export this session before leaving.'; }
      changed();
    },
    replaceValidated(incoming) { data = validateProgress(incoming, knownIds); warning = ''; writable = true; changed(); }
  };
}

// The course UI and lab controls share the same live records, including blocked storage.
const shared = new WeakMap();
export function getSharedProgressStore(knownIds) {
  const owner = window;
  const key = [...knownIds].sort().join('|');
  if (!shared.has(owner)) shared.set(owner, new Map());
  const records = shared.get(owner);
  if (!records.has(key)) records.set(key, createProgressStore(knownIds));
  return records.get(key);
}
