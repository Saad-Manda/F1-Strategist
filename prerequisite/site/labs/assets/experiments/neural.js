import {linearStep,fifo,doubleTarget,dueling,priorities,weightedLoss,drawCounts} from './neural-models.js?v=reading-20261006-r8';
import {randomGenerator} from './foundation-models.js?v=reading-20261006-r8';
const $=id=>document.getElementById(id),num=id=>Number($(id).value),fmt=x=>Number(x.toFixed(6)).toString();
function row(id,cells){const tr=document.createElement('tr');for(const value of cells){const td=document.createElement('td');td.textContent=value;tr.append(td);}$(id).append(tr);}
function listen(id,event,action){$(id).addEventListener(event,()=>{try{action();$('experiment-error').textContent='';}catch(e){$('experiment-error').textContent=e.message;}});}
const lab=document.body.dataset.labId;
let reset;
if(lab==='p5-network'){
  let weight=[0,0],bias=[0,0],steps=0;
  const calculation=()=>linearStep(num('x'),weight,bias,num('rate'));
  const render=()=>{const v=calculation();$('network-table').replaceChildren();v.prediction.forEach((p,i)=>row('network-table',[i,fmt(weight[i]),fmt(bias[i]),fmt(p),fmt(v.labels[i]),fmt(v.gw[i]),fmt(v.gb[i])]));$('network-summary').textContent=`SGD steps ${steps}; x=${fmt(num('x'))}; learning rate=${fmt(num('rate'))}; mean loss=${fmt(v.loss)}; sum-loss bug=${fmt(2*v.loss)}. Fixed supervised labels, not DQN targets.`;};
  reset=()=>{weight=[0,0];bias=[0,0];steps=0;$('x').value='.25';$('rate').value='.1';render();};
  for(const id of ['x','rate'])listen(id,'input',render);
  listen('gradient-step','click',()=>{const v=calculation();weight=v.weight;bias=v.bias;steps++;render();});
}else if(lab==='p5-stability'){
  let online,target,buffer,next,counts=null;
  const render=()=>{$('snapshot-summary').textContent=`Online [${online}]; target [${target}]; same storage=${online===target}. Explicit sync copies values; detachment is a separate local Python check.`;$('buffer-summary').textContent=`Capacity 4; retained IDs [${buffer}]; next ID ${next}; uniform probability ${fmt(1/buffer.length)} each.`+(counts?` Draw counts [${counts}] for those IDs; 1000 with-replacement draws, browser LCG seed 7.`:'');};
  const snapshot=()=>{online=[1,2];target=$('snapshot-mode').value==='alias'?online:[...online];render();};
  reset=()=>{$('snapshot-mode').value='copy';buffer=[0,1,2,3];next=4;counts=null;$('fixture-seed').value='7';snapshot();if(fixture)renderFixture();};
  listen('snapshot-mode','change',snapshot);
  listen('change-online','click',()=>{online.splice(0,2,3,4);render();});
  listen('sync-snapshot','click',()=>{target.splice(0,2,...online);render();});
  listen('insert-transition','click',()=>{buffer=fifo(buffer,next++);counts=null;render();});
  listen('sample-buffer','click',()=>{counts=drawCounts(buffer.map(()=>1/buffer.length),1000,randomGenerator(7));render();});
  let fixture=null;
  function renderFixture(){
    const seed=num('fixture-seed'),runs=fixture.runs.filter(r=>r.seed===seed);
    $('fixture-table').replaceChildren();
    for(const run of runs)for(const r of run.checkpoints)row('fixture-table',[run.variant,r.transitions,r.optimizer_steps,fmt(r.td_mse),r.evaluation_return]);
    $('fixture-status').textContent=`Recorded Python CPU runs · seed ${seed} · each variant: 192 transitions / 48 optimizer updates. Return is frozen greedy evaluation; repeated deterministic starts do not estimate uncertainty. No guaranteed winner.`;
    $('fixture-provenance').textContent=JSON.stringify({...fixture,runs:undefined},null,2);
    const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
    svg.setAttribute('viewBox','0 0 560 240');svg.setAttribute('role','img');svg.setAttribute('aria-label',`Recorded TD MSE versus transitions, seed ${seed}. Exact values in table.`);svg.style.width='100%';
    const max=Math.max(...runs.flatMap(r=>r.checkpoints.map(c=>c.td_mse)),1e-9);
    const text=(x,y,label,color='currentColor')=>{const t=document.createElementNS(ns,'text');t.setAttribute('x',x);t.setAttribute('y',y);t.setAttribute('fill',color);t.setAttribute('font-size','12');t.textContent=label;svg.append(t);};
    text(8,15,`TD MSE (linear scale, max ${fmt(max)})`);text(35,210,'32');text(490,210,'192 transitions');
    for(let i=0;i<runs.length;i++){
      const color=['#2ca58d','#8b78db','#d7833b'][i],line=document.createElementNS(ns,'polyline');
      line.setAttribute('points',runs[i].checkpoints.map(c=>`${40+(c.transitions-32)/160*470},${185-c.td_mse/max*155}`).join(' '));line.setAttribute('fill','none');line.setAttribute('stroke',color);line.setAttribute('stroke-width','2');svg.append(line);text(15+i*180,232,runs[i].variant,color);
    }
    $('fixture-chart').replaceChildren(svg);
  }
  listen('fixture-seed','change',()=>{if(fixture)renderFixture();});
  $('fixture-seed').disabled=true;
  fetch(new URL('../../fixtures/p5-stability-ablation.json',import.meta.url)).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();}).then(data=>{
    if(data.schemaVersion!==1||data.runs.length!==9||data.runs.some(r=>r.transitions!==192||r.optimizer_steps!==48||r.checkpoints.length!==6||r.checkpoints.some(c=>!Number.isFinite(c.td_mse)||!Number.isFinite(c.evaluation_return))))throw new Error('Invalid recorded fixture');
    fixture=data;$('fixture-seed').disabled=false;renderFixture();
  }).catch(e=>{$('fixture-status').textContent=`Recorded fixture unavailable: ${e.message}. Snapshot experiments and downloads still work.`;});
}else if(lab==='p5-double-dueling'){
  const render=()=>{const v=doubleTarget([5,4,100],[1,7,99],[true,true,false],1,num('gamma'),$('terminal').checked),advantages=[1+num('offset'),3+num('offset')],q=dueling(2,advantages);$('double-table').replaceChildren();[0,1,2].forEach(i=>row('double-table',[i,i<2?'Yes':'No',[5,4,100][i],[1,7,99][i],i<2?advantages[i]:'Separate two-action dueling witness',i<2?fmt(q[i]):'—']));$('double-summary').textContent=`Online selects ${v.selected===null?'no successor (terminal)':`action ${v.selected}`}; Double target=${fmt(v.double)}; vanilla target=${fmt(v.vanilla)}. Dueling V=2, common offset=${num('offset')}, Q=[${q.map(fmt)}].`;};
  reset=()=>{$('gamma').value='.5';$('offset').value='0';$('terminal').checked=false;render();};
  for(const id of ['gamma','offset'])listen(id,'input',render);listen('terminal','change',render);
}else if(lab==='p5-per'){
  let raw,ids,next,counts,losses;
  const render=()=>{const v=priorities(raw,num('per-alpha'),num('per-beta'));$('priority-table').replaceChildren();raw.forEach((p,i)=>row('priority-table',[ids[i],fmt(p),fmt(v.masses[i]),fmt(v.probabilities[i]),fmt(v.weights[i]),counts?counts[i]:'Not drawn']));$('per-summary').textContent=`α=${num('per-alpha')}; β=${num('per-beta')}; global maximum normalization. Separate squared-loss examples [${losses.map(fmt)}]: weighted mean=${fmt(weightedLoss(losses,v.weights))}. New items inherit ${$('priority-mode').value==='raw'?'raw':'already transformed (bug)'} maximum. Sampling counts are evidence, not exact probabilities.`;
    $('priority-bars').replaceChildren();
    ids.forEach((id,i)=>{const p=document.createElement('p');p.textContent=`ID ${id} · `;for(const [label,value] of [['P(sample)',v.probabilities[i]],['Weight',v.weights[i]]]){const meter=document.createElement('meter');meter.min=0;meter.max=1;meter.value=value;meter.setAttribute('aria-label',`${label} for ID ${id}: ${fmt(value)}`);p.append(document.createTextNode(`${label} `),meter,document.createTextNode(` ${fmt(value)} `));}$('priority-bars').append(p);});
  };
  reset=()=>{raw=[1,4,9];losses=[1,4,9];ids=[0,1,2];next=3;counts=null;$('per-alpha').value='.5';$('per-beta').value='1';$('priority-mode').value='raw';$('td-error').value='-3';render();};
  for(const id of ['per-alpha','per-beta'])listen(id,'input',()=>{counts=null;render();});
  listen('priority-mode','change',render);
  listen('add-priority','click',()=>{const p=Math.max(...raw);raw=fifo(raw,$('priority-mode').value==='raw'?p:p**num('per-alpha'));ids=fifo(ids,next++);losses=fifo(losses,9);counts=null;render();});
  listen('draw-priorities','click',()=>{counts=drawCounts(priorities(raw,num('per-alpha'),num('per-beta')).probabilities,1000,randomGenerator(7));render();});
  listen('update-priority','click',()=>{const error=num('td-error');if(!$('td-error').value.trim()||!Number.isFinite(error)||Math.abs(error)>100)throw new Error('Enter a finite TD error from -100 to 100.');raw[0]=Math.abs(error)+1e-6;losses[0]=error**2;counts=null;render();});
}
if(reset){listen('reset-experiment','click',reset);reset();$('experiment-controls').hidden=false;}
