import { createProgressStore } from './storage.js';
const controls = document.querySelector('#catalog-controls');
const phaseFilter = document.querySelector('#phase-filter');
const modeFilter = document.querySelector('#mode-filter');
const count = document.querySelector('#filter-count');
const empty = document.querySelector('#empty-results');
const cards = [...document.querySelectorAll('[data-lab-id]')];
const phases = [...document.querySelectorAll('[data-phase-section]')];

function filterCatalog() {
  let visible = 0;
  for (const card of cards) {
    card.hidden = (phaseFilter.value !== 'all' && card.dataset.phase !== phaseFilter.value)
      || (modeFilter.value !== 'all' && card.dataset.mode !== modeFilter.value);
    if (!card.hidden) visible += 1;
  }
  for (const phase of phases) {
    phase.hidden = ![...phase.querySelectorAll('[data-lab-id]')].some(card => !card.hidden);
  }
  count.textContent = `${visible} of ${cards.length} labs`;
  empty.hidden = visible !== 0;
}

// Prerequisite/sidebar links should reveal their target even after filtering.
function revealTarget() {
  let hash;
  try { hash = decodeURIComponent(location.hash.slice(1)); } catch { return; }
  const target = document.getElementById(hash);
  if (!target || !target.closest('[data-phase-section]')) return;
  phaseFilter.value = 'all';
  modeFilter.value = 'all';
  filterCatalog();
  target.scrollIntoView({ block: 'start' });
}

controls.hidden = false;
phaseFilter.addEventListener('change', filterCatalog);
modeFilter.addEventListener('change', filterCatalog);
window.addEventListener('hashchange', revealTarget);
document.addEventListener('click', event => {
  const link = event.target.closest('a[href^="#"]');
  if (link && link.hash === location.hash) revealTarget();
});
filterCatalog();
revealTarget();
function showProgress() {
  const store = createProgressStore(cards.map(card => card.dataset.labId));
  for (const node of document.querySelectorAll('[data-progress-state]')) {
    node.textContent = ({'not-started':'Not started',attempted:'Attempted',completed:'Completed'})[store.get(node.dataset.progressState).status];
  }
}
window.addEventListener('pageshow', showProgress);
document.addEventListener('visibilitychange', () => { if (!document.hidden) showProgress(); });
showProgress();
