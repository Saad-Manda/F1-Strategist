import {returns, branchValues, backward, expectedValue, advance, WEATHER, randomGenerator, sampleNext, switchStep} from './foundation-models.js?v=reading-20261006-r8';

const $ = id => document.getElementById(id);
const num = id => {
  if (!$(id).value.trim()) throw new Error('Enter a value for each numeric control.');
  return Number($(id).value);
};
const fmt = value => Number(value.toFixed(6)).toString();
function row(target, cells) {
  const tr = document.createElement('tr');
  for (const value of cells) { const td = document.createElement('td'); td.textContent = value; tr.append(td); }
  $(target).append(tr);
}
function listen(id, event, action) {
  $(id).addEventListener(event, () => {
    try { action(); $('experiment-error').textContent = ''; }
    catch (error) { $('experiment-error').textContent = error.message; }
  });
}
let reset;
switch (document.body.dataset.labId) {
  case 'p1-state': {
    let mode, done, steps;
    const observation = () => $('encoder').value === 'broken' ? 0 : mode;
    const status = () => { $('switch-status').textContent = `Hidden mode ${mode}; agent observation ${observation()}; terminated=${done}.`;
      $('flip').disabled = $('claim').disabled = done; };
    reset = () => { mode = num('initial-mode'); done = false; steps = 0; $('switch-trace').replaceChildren(); status(); };
    const step = action => { if (done) return; const before = mode, obs = observation(); const next = switchStep(mode, action); mode = next.mode; done = next.terminated;
      row('switch-trace', [++steps, action, before, obs, next.reward, observation(), done]); status(); };
    listen('flip', 'click', () => step('FLIP')); listen('claim', 'click', () => step('CLAIM'));
    listen('initial-mode', 'change', reset); listen('encoder', 'change', reset);
    listen('seeded-switch','click', () => { $('initial-mode').value = randomGenerator(num('switch-seed'))() < 0.5 ? '0' : '1'; reset(); });
    break;
  }
  case 'p1-return': {
    let tail, next;
    const rewards = [2, -1, 4];
    const render = () => {
      const gamma = num('gamma'), start = num('return-start'), result = returns(rewards, gamma);
      $('return-total').textContent = `γ = ${fmt(gamma)}; G${start} = ${fmt(result[start])}; all returns = [${result.map(fmt).join(', ')}].`;
      $('return-weights').replaceChildren();
      rewards.forEach((reward, t) => { if (t >= start) row('return-weights', [t, reward, fmt(gamma ** (t - start)), fmt(reward * gamma ** (t - start))]); });
      tail = 0; next = 2; $('reverse-trace').replaceChildren(); $('reverse-step').disabled = false;
    };
    reset = () => { $('gamma').value = '0.5'; $('return-start').value = '0'; render(); };
    listen('gamma', 'input', render); listen('return-start', 'change', render);
    listen('reverse-step', 'click', () => {
      if (next < 0) return;
      const previous = tail; tail = rewards[next] + num('gamma') * tail;
      const li = document.createElement('li'); li.textContent = `G${next} = ${rewards[next]} + ${fmt(num('gamma'))} × ${fmt(previous)} = ${fmt(tail)}`;
      $('reverse-trace').append(li); next--; $('reverse-step').disabled = next < 0;
    }); break;
  }
  case 'p1-values': {
    const render = () => {
      const gamma = num('gamma'), p = num('policy-p'), v = branchValues(gamma, p);
      $('value-table').replaceChildren();
      row('value-table', ['DIRECT', 'Yes', 3, 0, fmt(v.direct), fmt(1-p), fmt((1-p)*v.direct)]);
      row('value-table', ['VIA', 'Yes', 1, fmt(gamma*4), fmt(v.via), fmt(p), fmt(p*v.via)]);
      row('value-table', ['Illegal stored entry', 'No', '—', '—', 99, 0, 'Excluded']);
      $('value-summary').textContent = `γ = ${fmt(gamma)}; π(VIA) = ${fmt(p)}; Vπ(A) = ${fmt(v.policy)}; V*(A) = ${fmt(v.optimal)}. B has value 4.`;
    };
    reset = () => { $('gamma').value = '1'; $('policy-p').value = '0.5'; render(); };
    listen('gamma','input',render); listen('policy-p','input',render); break;
  }
  case 'p35-backward': {
    let shown = 0, rows;
    const render = () => {
      $('backward-table').replaceChildren();
      rows.slice(0,shown+1).forEach(r => row('backward-table',[r.h,fmt(r.B),r.direct ?? '—',r.via === null ? '—' : fmt(r.via),fmt(r.A),r.action]));
      $('backup-step').disabled = shown >= rows.length - 1;
      $('backward-summary').textContent = `γ = ${fmt(num('gamma'))}; showing h = 0 through ${shown} of H = ${num('horizon')}.`;
    };
    const restart = () => { const computed = backward(num('horizon'),num('gamma')); rows = computed; shown = 0; render(); };
    reset = () => { $('horizon').value = '2'; $('gamma').value = '1'; restart(); };
    listen('horizon','input',restart); listen('gamma','input',restart);
    listen('backup-step','click', () => { backward(num('horizon'),num('gamma')); if (shown < rows.length - 1) shown++; render(); }); break;
  }
  case 'p35-stochastic': {
    let p;
    const render = () => {
      const risky = expectedValue([[p,10],[1-p,-2]]);
      $('lottery-table').replaceChildren(); row('lottery-table',['WIN',fmt(p),10,fmt(p*10)]); row('lottery-table',['LOSS',fmt(1-p),-2,fmt((1-p)*-2)]);
      const decision = Math.abs(risky-2)<1e-10 ? 'Tie' : risky>2 ? 'RISKY wins' : 'SAFE wins';
      $('lottery-summary').textContent = `p = ${fmt(p)}; Q(RISKY) = ${fmt(risky)}; Q(SAFE) = 2. ${decision}.`;
    };
    reset = () => { p = 0.25; $('win-p').value='0.25'; $('custom-win').value='0.25'; $('custom-loss').value='0.75'; $('row-status').textContent=''; render(); };
    listen('win-p','input', () => { p = num('win-p'); render(); });
    listen('tie-p','click', () => { p=1/3; $('win-p').value=String(p); render(); });
    listen('check-row','click', () => { $('row-status').textContent=''; const value = expectedValue([[num('custom-win'),10],[num('custom-loss'),-2]]); $('row-status').textContent=`Valid row; expected value = ${fmt(value)}.`; }); break;
  }
  case 'p35-markov': {
    let distribution, state, random, step, dryCount, cap;
    const show = () => {
      $('weather-summary').textContent = `Step ${step}/${cap}; exact distribution [${distribution.map(fmt).join(', ')}]; sample ${state===0?'DRY':'WET'}; terminated=false, truncated=${step>=cap}.`;
      $('weather-step').disabled = $('weather-many').disabled = step >= cap;
    };
    const tick = () => {
      randomGenerator(num('weather-seed'));
      const requestedCap=num('weather-cap');
      if (!Number.isInteger(requestedCap)||requestedCap<1||requestedCap>100)throw new Error('Collection cap must be an integer from 1 to 100.');
      if (step>=cap) return;
      distribution=advance(distribution); state=sampleNext(state,random); step++; if(state===0)dryCount++;
      row('weather-table',[step,fmt(distribution[0]),fmt(distribution[1]),state===0?'DRY':'WET',fmt(dryCount/step),step>=cap]); show();
    };
    const restart = () => {
      const newCap=num('weather-cap');
      if (!Number.isInteger(newCap)||newCap<1||newCap>100)throw new Error('Collection cap must be an integer from 1 to 100.');
      const rng=randomGenerator(num('weather-seed'));
      cap=newCap; random=rng; state=num('weather-start'); distribution=state===0?[1,0]:[0,1]; step=0; dryCount=0;
      $('weather-table').replaceChildren();
      const scores=WEATHER[state];
      $('foresight-summary').textContent=`Separate one-step prediction task from ${state===0?'DRY':'WET'}: NONE score ${scores[0]}, UMBRELLA score ${scores[1]}; attainable best expectation ${Math.max(...scores)}; perfect-foresight bound 1. Stationary distribution [0.6, 0.4].`;
      show();
    };
    reset = () => { $('weather-start').value='0'; $('weather-seed').value='7'; $('weather-cap').value='10'; restart(); };
    listen('weather-start','change',restart);
    for(const id of ['weather-seed','weather-cap'])listen(id,'input',restart);
    listen('weather-step','click',tick); listen('weather-many','click',()=>{while(step<cap)tick();}); break;
  }
  default: throw new Error('Unknown foundation lab.');
}
listen('reset-experiment','click',reset);
reset(); $('experiment-controls').hidden=false;
