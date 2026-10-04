import { getSharedProgressStore } from './storage.js?v=outline-20261004';
import { loadLabRegistry } from './lab-registry.js';
import { getCourseRuntime } from '../../assets/course-progress-ui.js?v=outline-20261004';

const labId = document.body.dataset.labId;
let knownIds = [labId];
try { knownIds = (await loadLabRegistry()).labs.map(lab => lab.id); }
catch {try {knownIds=(await getCourseRuntime()).course.lessons.map(l=>l.id);}catch { /* The lab remains usable without either registry. */ }}
const store = getSharedProgressStore(knownIds);
const savedStatus = document.querySelector('#saved-status');
const explanation = document.querySelector('#explanation');
const verified = document.querySelector('#verified');
const feedback = document.querySelector('#prediction-feedback');
const hints = [...document.querySelectorAll('[data-hint]')];
const hintButton = document.querySelector('#next-hint');
const solution = document.querySelector('#solution');
const solutionButton = document.querySelector('#reveal-solution');
const progress = document.querySelector('#lab-progress');
const messages = {
  terminal: 'That predicts a true task boundary. Run the sequence and inspect both flags; does the observation also match your prediction?',
  reward: 'Your prediction treats the step reward as the episode total. Record both numbers after each action and compare them.',
  reset: 'Your prediction adds a reset to the environment transition. Inspect the observation returned on arrival before any reset is called.'
};
const predictionInputs = [...document.querySelectorAll('input[name="prediction"]')];
for (const radio of predictionInputs) {
  if (radio.dataset.feedback) messages[radio.value] = radio.dataset.feedback;
}

function render() {
  const record = store.get(labId);
  explanation.value = record.explanation;
  verified.checked = record.verified;
  const selected = predictionInputs.find(radio => radio.value === record.prediction);
  if (selected) selected.checked = true;
  else for (const radio of document.querySelectorAll('input[name="prediction"]')) radio.checked = false;
  hints.forEach((hint, index) => { hint.hidden = index >= record.hints; });
  hintButton.disabled = record.hints >= hints.length;
  hintButton.textContent = record.hints >= hints.length ? 'All hints revealed' : `Request hint ${record.hints + 1} of ${hints.length}`;
  solution.hidden = !record.solution;
  solutionButton.textContent = record.solution ? 'Hide explained solution' : 'Request explained solution';
  solutionButton.setAttribute('aria-expanded', String(record.solution));
  progress.textContent = ({'not-started':'Not started',attempted:'Attempted',completed:'Completed'})[record.status];
  savedStatus.textContent = store.warning || 'Progress stays in this browser. Export it to move it to another browser.';
  feedback.textContent = record.attempts ? `Latest prediction saved. ${messages[record.prediction] || 'You can revise and check your prediction.'}` : '';
  const completion = document.querySelector('#completion-feedback');
  if(record.status !== 'completed' && completion.textContent.startsWith('Completed.')) completion.textContent='';
}
let writing = false;
function set(patch) {
  writing = true;
  try {store.set(labId, patch);} finally {writing = false;}
  savedStatus.textContent = store.warning || 'Progress saved in this browser.';
}
document.querySelector('#prediction-form').addEventListener('submit', event => {
  event.preventDefault();
  const selected = document.querySelector('input[name="prediction"]:checked');
  if (!selected) { feedback.textContent = 'Choose a prediction first.'; return; }
  const previous = store.get(labId);
  set({ prediction: selected.value, attempts: previous.attempts + 1, status: previous.status === 'completed' ? 'completed' : 'attempted' });
  feedback.textContent = messages[selected.value];
  progress.textContent = store.get(labId).status === 'completed' ? 'Completed' : 'Attempted';
});
hintButton.addEventListener('click', () => { set({ hints: store.get(labId).hints + 1 }); render(); });
solutionButton.addEventListener('click', () => { set({ solution: !store.get(labId).solution }); render(); });
function saveReflection() {
  const record = store.get(labId);
  const revoked = record.status === 'completed' && (!verified.checked || !explanation.value.trim());
  set({ explanation: explanation.value, verified: verified.checked,
    status: revoked ? 'attempted' : record.status });
  if (revoked) document.querySelector('#completion-feedback').textContent = 'Completion removed. Add your explanation and confirm local checks before marking this lab complete again.';
  progress.textContent = store.get(labId).status === 'completed' ? 'Completed' : store.get(labId).status === 'attempted' ? 'Attempted' : 'Not started';
}
explanation.addEventListener('input', saveReflection);
verified.addEventListener('change', saveReflection);
document.querySelector('#complete-lab').addEventListener('click', () => {
  if (!verified.checked || !explanation.value.trim()) {
    document.querySelector('#completion-feedback').textContent = 'Confirm your local checks and write your explanation before marking this lab complete.';
    return;
  }
  set({ verified: true, explanation: explanation.value, status: 'completed' });
  document.querySelector('#completion-feedback').textContent = 'Completed. Your explanation and local verification are recorded; using hints does not affect completion.';
  progress.textContent = 'Completed';
});
document.querySelector('#export-progress').textContent = 'Export course and lab progress';
document.querySelector('#reset-progress').textContent = 'Clear this lab’s work (keep course readings)';
document.querySelector('#export-progress').addEventListener('click', async () => {
  let raw;
  try {raw=(await getCourseRuntime()).store.export(store);}
  catch {savedStatus.textContent='Course export unavailable. This backup includes lab work only.';raw=store.export();}
  const url = URL.createObjectURL(new Blob([raw], {type:'application/json'}));
  const link = document.createElement('a');
  link.href = url; link.download = 'rl-course-progress.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
document.querySelector('#import-progress').addEventListener('change', async event => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    if (file.size > 500000) throw new Error('Progress file is too large.');
    const runtime=await getCourseRuntime();runtime.store.import(await file.text(),store); render();
    savedStatus.textContent = store.warning || 'Imported progress replaced the saved progress in this browser.';
  } catch (error) { savedStatus.textContent = `Import failed; existing progress retained. ${error.message}`; }
  event.target.value = '';
});
document.querySelector('#reset-progress').addEventListener('click', () => {
  store.reset(labId); render();
  document.querySelector('#completion-feedback').textContent = '';
});
document.querySelector('#learning-controls').hidden = false;
for (const id of ['help-controls', 'reflection-controls', 'progress-tools']) document.getElementById(id).hidden = false;
render();
store.subscribe(()=>{if(!writing)render();});
