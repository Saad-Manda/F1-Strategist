import {tdUpdate, epsilonProbabilities, selectAction, sarsaTarget, binIndex, tableSize, representationCeiling, trainBandit, trainShortcut, trainBins} from './tabular-models.js';
import {randomGenerator} from './foundation-models.js';
const $=id=>document.getElementById(id);
const num=id=>{if(!$(id).value.trim())throw new Error('Enter a value in each numeric control.');return Number($(id).value);};
const fmt=x=>Number(x.toFixed(6)).toString();
function row(id,cells,header=false){const tr=document.createElement('tr');for(const value of cells){const cell=document.createElement(header?'th':'td');cell.textContent=value;tr.append(cell);}$(id).append(tr);}
function listen(id,event,action){$(id).addEventListener(event,()=>{try{action();$('experiment-error').textContent='';}catch(error){$('experiment-error').textContent=error.message;}});}
function integer(id,lo,hi){const n=num(id);if(!Number.isInteger(n)||n<lo||n>hi)throw new Error(`${id} must be an integer from ${lo} to ${hi}.`);return n;}
const lab=document.body.dataset.labId;
let reset;
if(lab==='p4-td'){
  let current=2;
  const calculation=()=>tdUpdate(current,1,[4,8,99],[$('legal-four').checked,$('legal-eight').checked,false],num('alpha'),num('gamma'),$('boundary').value==='terminated',$('boundary').value==='truncated');
  const render=()=>{
    $('td-preview').textContent='No valid preview until the transition inputs are valid.';
    $('q-snapshot').replaceChildren();
    row('q-snapshot',['S',[fmt(current),0].join(', '),'Selected action only']);row('q-snapshot',['N','4, 8, 99',`${$('legal-four').checked}, ${$('legal-eight').checked}, false`]);
    const v=calculation();
    const buggy=tdUpdate(current,1,[4,8,99],[true,true,true],num('alpha'),num('gamma'),v.terminated,v.truncated);
    $('td-preview').textContent=`Current Q=${fmt(current)}; target=${fmt(v.target)}; error=${fmt(v.error)}; proposed Q=${fmt(v.value)}. Mask-ignoring bug target=${fmt(buggy.target)}. terminated=${v.terminated}, truncated=${v.truncated}.`;
  };
  reset=()=>{current=2;$('alpha').value='0.25';$('gamma').value='0.5';$('boundary').value='ongoing';$('legal-four').checked=$('legal-eight').checked=true;$('td-trace').replaceChildren();render();};
  for(const id of ['alpha','gamma'])listen(id,'input',render);
  for(const id of ['boundary','legal-four','legal-eight'])listen(id,'change',render);
  listen('apply-update','click',()=>{const v=calculation();row('td-trace',[fmt(current),fmt(v.target),fmt(v.error),fmt(num('alpha')),fmt(num('gamma')),fmt(v.value),v.terminated,v.truncated]);current=v.value;render();});
}else{
  const defaults=()=>{$('epsilon').value='0.2';$('alpha').value='0.1';$('run-seed').value='7';$('episodes').value='1000';$('comparison-body').replaceChildren();$('run-settings').textContent='';$('run-summary').textContent='';};
  let render, extraReset=()=>{};
  if(lab==='p4-explore'){
    render=()=>{
      const p=epsilonProbabilities([0.6,0.1,99],[true,true,false],num('epsilon'));
      $('explore-policy').replaceChildren();['A','B','C'].forEach((name,i)=>row('explore-policy',[name,[0.6,0.1,99][i],i<2?'Yes':'No',i<2?[0.4,0.8][i]:'—',fmt(p[i]),[1,0,0][i]]));
    };
  }else if(lab==='p4-sarsa'){
    let pending=null,rng=randomGenerator(7);
    const status=()=>{$('sarsa-status').textContent=(pending===null?'No committed action. Choose a witness or sample once.':`Committed ${pending===0?'careful':'slip'}; SARSA target ${sarsaTarget([6,-10],pending)}; Q-learning target 6.`)+' Witness RNG seed 7; Reset clears it and the pending action.';$('execute-next').disabled=$('resample-next').disabled=pending===null;};
    render=()=>{const p=epsilonProbabilities([6,-10],[true,true],num('epsilon'));$('sarsa-expectation').textContent=`ε=${fmt(num('epsilon'))}; careful probability=${fmt(p[0])}; slip probability=${fmt(p[1])}; risk behaviour value=${fmt(p[0]*6+p[1]*-10)}; safe=3; greedy risk=6. Worked Q values [6,−10] are fixed.`;};
    const commit=action=>{pending=action;status();};
    const execute=bug=>{if(pending===null)return;const used=pending,executed=bug?selectAction([6,-10],[true,true],num('epsilon'),rng):used;row('sarsa-trace',[used===0?'careful':'slip',sarsaTarget([6,-10],used),6,executed===0?'careful':'slip',executed===0?6:-10,used===executed?'Yes':'No — action replaced']);pending=null;status();};
    listen('force-careful','click',()=>commit(0));listen('force-slip','click',()=>commit(1));listen('sample-next','click',()=>{if(pending!==null)throw new Error('Execute or reset the pending action before sampling again.');commit(selectAction([6,-10],[true,true],num('epsilon'),rng));});
    listen('execute-next','click',()=>execute(false));listen('resample-next','click',()=>execute(true));
    extraReset=()=>{pending=null;rng=randomGenerator(7);$('sarsa-trace').replaceChildren();status();};
  }else if(lab==='p4-bins'){
    const edges=()=>{const pieces=$('edges').value.split(',');if(pieces.some(p=>!p.trim()))throw new Error('Enter comma-separated numeric edges.');const result=pieces.map(Number);binIndex(0,result);return result;};
    render=()=>{
      const e=edges(),x=num('observation-x');$('bin-witnesses').replaceChildren();[0,0.49,0.5,0.51,1].forEach(value=>row('bin-witnesses',[value,binIndex(value,e),value<0.5?'LEFT':'RIGHT']));
      $('bin-status').textContent=`x=${fmt(x)} → bin ${binIndex(x,e)}; ${e.length-1} ${e.length===2?'bin':'bins'}; uniform-x representation ceiling=${fmt(representationCeiling(e))}.`;
      const d=integer('dimensions',1,8),b=integer('axis-bins',1,20),size=tableSize(Array(d).fill(b)),doubled=tableSize(Array(d).fill(2*b));
      $('table-size').textContent=`${b} bins × ${d} dimensions × 2 actions: ${size.states} states, ${size.entries} entries, ${size.bytes} float64 payload bytes. Doubling every axis: ${doubled.entries} entries (${2**d}×). Container overhead excluded.`;
    };
    listen('edges','input',render);listen('observation-x','input',render);for(const id of ['dimensions','axis-bins'])listen(id,'input',render);
    for(const [id,e] of [['coarse-bins','0,1'],['fine-bins','0,0.5,1'],['nonuniform-bins','0,0.45,0.5,0.55,1']])listen(id,'click',()=>{$('edges').value=e;render();});
    extraReset=()=>{$('edges').value='0,1';$('observation-x').value='0.49';$('dimensions').value='3';$('axis-bins').value='4';};
  }else throw new Error('Unknown tabular lab.');
  const describe=()=>{
    const seed=integer('run-seed',0,4294967295);
    $('run-settings').textContent=`Training: ${integer('episodes',1,5000)} ${lab==='p4-sarsa'?'two-step':'one-step'} episodes/seed, ε=${fmt(num('epsilon'))}, α=${fmt(num('alpha'))}, γ=${lab==='p4-sarsa'?1:0}. Evaluation: frozen Q, ε=0; ${lab==='p4-bins'?'1000 paired midpoint observations':'200 fresh episodes per seed'}. Independent policy/environment streams; seeds [${[seed,(seed+1)>>>0,(seed+2)>>>0].join(', ')}]. ${lab==='p4-sarsa'?'Q order: START [shortcut,detour], RISK [careful,slip], SAFE [finish]. ':''}Browser LCG and Python RNG paths differ.`;
  };
  reset=()=>{defaults();extraReset();render();describe();};
  const invalidate=()=>{$('comparison-body').replaceChildren();$('run-summary').textContent='Settings changed. Run the comparisons again.';describe();};
  listen('epsilon','input',()=>{render();invalidate();});listen('alpha','input',invalidate);
  for(const id of ['episodes','run-seed'])listen(id,'input',invalidate);
  listen('run-comparison','click',()=>{
    describe();const seed=integer('run-seed',0,4294967295),episodes=integer('episodes',1,5000),epsilon=num('epsilon'),alpha=num('alpha');
    $('comparison-head').replaceChildren();$('comparison-body').replaceChildren();const groups={};
    row('comparison-head',['Variant','Seed','Training mean','Greedy eval mean',lab==='p4-explore'?'A/B/C visits':lab==='p4-sarsa'?'Training slips':'Representation ceiling','Final Q table'],true);
    for(let offset=0;offset<3;offset++){
      const runSeed=(seed+offset)>>>0;
      const variants=lab==='p4-explore'?[['ε=0 baseline',()=>trainBandit(runSeed,episodes,0,alpha)],['Chosen ε',()=>trainBandit(runSeed,episodes,epsilon,alpha)]]:lab==='p4-sarsa'?[['Q-learning',()=>trainShortcut(runSeed,episodes,epsilon,alpha,'q-learning')],['SARSA',()=>trainShortcut(runSeed,episodes,epsilon,alpha,'sarsa')]]:[['Coarse',()=>trainBins(runSeed,episodes,[0,1],epsilon,alpha)],['Split',()=>trainBins(runSeed,episodes,[0,0.5,1],epsilon,alpha)],['Nonuniform',()=>trainBins(runSeed,episodes,[0,0.45,0.5,0.55,1],epsilon,alpha)]];
      for(const [name,run] of variants){const result=run();(groups[name]??=[]).push(result);
        const rounded=Array.isArray(result.q)?result.q.map(v=>Array.isArray(v)?v.map(n=>Number(fmt(n))):Number(fmt(v))):Object.fromEntries(Object.entries(result.q).map(([s,values])=>[s,values.map(n=>Number(fmt(n)))]));
        row('comparison-body',[name,runSeed,fmt(result.trainingMean),fmt(result.evaluationMean),result.visits?.join('/')??result.slips??fmt(result.ceiling),JSON.stringify(rounded)]);}
    }
    $('run-summary').textContent=Object.entries(groups).map(([name,runs])=>`${name}: mean training ${fmt(runs.reduce((s,r)=>s+r.trainingMean,0)/runs.length)}, mean greedy evaluation ${fmt(runs.reduce((s,r)=>s+r.evaluationMean,0)/runs.length)}`).join('; ')+'. These are sampled learning results, not correctness gates.';
  });
}
listen('reset-experiment','click',reset);reset();$('experiment-controls').hidden=false;
