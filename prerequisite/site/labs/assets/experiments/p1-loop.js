import { resetChain, stepChain, seededActionGenerator } from './chain-model.js';
const panel = document.querySelector('#chain-controls');
const cap = document.querySelector('#step-cap');
const seed = document.querySelector('#random-seed');
const status = document.querySelector('#experiment-status');
const rows = document.querySelector('#trace-body');
let state = resetChain();
let timer = null;
let sample = seededActionGenerator(7);

function stop() {
  if (timer !== null) clearInterval(timer);
  timer = null;
  document.querySelector('#run-random').textContent = 'Run seeded random agent';
}
function render() {
  for (const node of document.querySelectorAll('[data-position]')) {
    const active = Number(node.dataset.position) === state.position;
    node.classList.toggle('current', active);
    if (active) node.setAttribute('aria-current', 'step'); else node.removeAttribute('aria-current');
  }
  document.querySelector('#chain-observation').textContent = state.position;
  document.querySelector('#chain-total').textContent = state.total;
  document.querySelector('#chain-flags').textContent = `terminated=${state.terminated}, truncated=${state.truncated}`;
  const done = state.terminated || state.truncated;
  for (const button of document.querySelectorAll('[data-action], #run-random')) button.disabled = done;
  if (done) stop();
}
function advance(action) {
  const previous = state.position;
  state = stepChain(state, action);
  const row = document.createElement('tr');
  for (const value of [state.steps, previous, action === 0 ? 'LEFT' : 'RIGHT', state.position, state.reward, state.total, state.terminated, state.truncated]) {
    const cell = document.createElement('td');
    cell.textContent = value;
    row.append(cell);
  }
  rows.append(row);
  status.textContent = state.terminated ? 'Reached position 2. The task terminated; reset for a new episode.'
    : state.truncated ? `Collection stopped after ${state.cap} steps at position ${state.position}. The task itself is not finished.`
      : `Agent chose ${action === 0 ? 'LEFT' : 'RIGHT'}. Environment returned observation ${state.position}, reward ${state.reward}.`;
  render();
}
function reset() {
  stop();
  const limit = Number(cap.value);
  const value = Number(seed.value);
  if (!Number.isInteger(value) || value < 0 || value > 4294967295) {
    status.textContent = 'Seed must be a whole number from 0 to 4294967295.';
    return;
  }
  try { state = resetChain(limit); } catch (error) { status.textContent = error.message; return; }
  sample = seededActionGenerator(value);
  rows.replaceChildren();
  status.textContent = `Reset returned observation 0 and fresh info. Step limit ${limit}; random seed ${value}.`;
  render();
}
for (const button of document.querySelectorAll('[data-action]')) {
  button.addEventListener('click', () => { stop(); advance(Number(button.dataset.action)); });
}
document.querySelector('#reset-chain').addEventListener('click', reset);
document.querySelector('#run-random').addEventListener('click', () => {
  if (timer !== null) { stop(); return; }
  document.querySelector('#run-random').textContent = 'Pause random agent';
  timer = setInterval(() => advance(sample()), 650);
});
document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
panel.hidden = false;
render();
