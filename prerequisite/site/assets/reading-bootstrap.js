// Fail visibly when a stale document/module graph cannot load the current store.
try {await import('./reading-shell.js?v=reading-20261006-r8');}
catch {
  const status=document.querySelector('#reading-status');
  status.textContent='Course files changed or could not load. Reload this page before saving. Static Next links and Python downloads remain available.';
  const reload=document.createElement('button');reload.textContent='Reload course';
  reload.addEventListener('click',()=>location.reload());status.after(reload);
}
