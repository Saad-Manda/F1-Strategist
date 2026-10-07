import {MATRIX,team,shapingRoutes,laneExpected,laneSamples,expectedPayoff,bestResponses,snapshot,poolProbabilities,pairedScores,lifecycle} from './multiagent-models.js?v=reading-20261006-r8';
import {drawCounts} from './neural-models.js?v=reading-20261006-r8';
import {randomGenerator} from './foundation-models.js?v=reading-20261006-r8';
const $=id=>document.getElementById(id),fmt=x=>Number(x.toFixed(6)).toString();
const num=id=>{if(!$(id).value.trim())throw new Error('Enter a numeric value.');const n=Number($(id).value);if(!Number.isFinite(n))throw new Error('Finite value required.');return n;};
const integer=(id,lo,hi)=>{const n=num(id);if(!Number.isInteger(n)||n<lo||n>hi)throw new Error(`Enter an integer from ${lo} to ${hi}.`);return n;};
function row(id,cells){const tr=document.createElement('tr');for(const value of cells){const td=document.createElement('td');td.textContent=value;tr.append(td);}$(id).append(tr);}
function listen(id,event,action){$(id).addEventListener(event,()=>{try{action();$('experiment-error').textContent='';}catch(e){$('experiment-error').textContent=e.message;}});}
const lab=document.body.dataset.labId;
let reset;
if(lab==='p6-credit'){
 let done=false;
 const render=()=>{$('team-table').replaceChildren();for(let a=0;a<2;a++)for(let b=0;b<2;b++){const v=team(a,b);row('team-table',[a?'HELP':'IDLE',b?'HELP':'IDLE',v.reward,...v.differences]);}};
 reset=()=>{done=false;$('team-a').value=$('team-b').value='1';$('joint-team').disabled=false;$('team-status').textContent='Both observe ready. Commitments resolve together; all table rows are model-known counterfactuals.';render();};
 listen('joint-team','click',()=>{if(done)return;const v=team(num('team-a'),num('team-b'));done=true;$('team-status').textContent=`Joint action resolved: both receive ${v.reward}; differences A=${v.differences[0]}, B=${v.differences[1]}; both terminated=true, truncated=false; live agents=[]. Reset for another round.`;$('joint-team').disabled=true;});
}else if(lab==='p6-shaping'){
 const render=()=>{const g=num('shape-gamma'),end=num('failure-potential');if(Math.abs(end)>10)throw new Error('Terminal potential must be from -10 to 10.');const sg=$('shape-discount').value==='match'?g:1,rows=shapingRoutes(g,end,sg);$('shape-table').replaceChildren();rows.forEach(r=>row('shape-table',[r.name,fmt(r.base),fmt(r.bonus),fmt(r.shaped),fmt(r.shift),fmt(r.boundary)]));const winner=field=>rows.filter(r=>r[field]===Math.max(...rows.map(x=>x[field]))).map(r=>r.name).join(', ');$('shape-status').textContent=`Task γ=${g}, shaping γ=${sg}, failure potential=${end}. Best base: ${winner('base')}; arbitrary bonus: ${winner('bonus')}; shaped: ${winner('shaped')}. Matching discounts require shift=−2+boundary; zero endpoints give a constant shift.`;};
 reset=()=>{$('shape-gamma').value='1';$('shape-discount').value='match';$('failure-potential').value='0';render();};
 listen('shape-gamma','input',render);listen('shape-discount','change',render);listen('failure-potential','input',render);
}else if(lab==='p6-opponent'){
 let evidence=null;
 const render=()=>{const p=num('opponent-p'),blocking=$('blocking').value==='on';$('lane-table').replaceChildren();row('lane-table',['CROSS',fmt(laneExpected(p,blocking)),evidence?fmt(evidence.cross):'Not sampled',evidence?fmt(evidence.occupation):'Not sampled']);row('lane-table',['WAIT',0,evidence?0:'Not sampled',evidence?fmt(evidence.occupation):'Not sampled']);$('lane-status').textContent=`Opponent p=${p}; blocking=${blocking}; exact best action=${laneExpected(p,blocking)>0?'CROSS':laneExpected(p,blocking)<0?'WAIT':'tie'}. ${evidence?'1000 one-round samples, browser LCG seed '+integer('opponent-seed',0,4294967295):'No sample evidence for these settings.'}`;};
 reset=()=>{evidence=null;$('opponent-p').value='.2';$('blocking').value='on';$('opponent-seed').value='7';render();};
 for(const id of ['opponent-p','opponent-seed'])listen(id,'input',()=>{evidence=null;render();});listen('blocking','change',()=>{evidence=null;render();});
 listen('lane-draw','click',()=>{evidence=laneSamples(num('opponent-p'),$('blocking').value==='on',1000,randomGenerator(integer('opponent-seed',0,4294967295)));render();});
}else if(lab==='p8-game'){
 const policies={rock:[1,0,0],paper:[0,1,0],scissors:[0,0,1],uniform:[1/3,1/3,1/3],mixed:[.5,.25,.25]};
 const render=()=>{const opponent=policies[$('rps-opponent').value],policy=policies[$('rps-policy').value];$('payoff-table').replaceChildren();['ROCK','PAPER','SCISSORS'].forEach((name,i)=>row('payoff-table',[name,...MATRIX[i],fmt(expectedPayoff(policies[['rock','paper','scissors'][i]],opponent))]));$('game-status').textContent=`Opponent [${opponent.map(fmt)}], learner [${policy.map(fmt)}]; exact payoff=${fmt(expectedPayoff(policy,opponent))}; best responses=${bestResponses(opponent).map(i=>['ROCK','PAPER','SCISSORS'][i]).join(', ')}. Frozen learner coverage vs ROCK/PAPER/SCISSORS: [${MATRIX[0].map((_,j)=>fmt(expectedPayoff(policy,MATRIX[0].map((_,i)=>Number(i===j)))))}].`;};
 reset=()=>{$('rps-opponent').value='rock';$('rps-policy').value='paper';render();};
 for(const id of ['rps-opponent','rps-policy'])listen(id,'change',render);
 listen('response-step','click',()=>{$('rps-policy').value=['rock','paper','scissors'][bestResponses(policies[$('rps-opponent').value])[0]];render();});
}else if(lab==='p8-pool'){
 let learner,pool,ids,next,counts;
 const render=()=>{const weights=pool.map((_,i)=>i+1),p=pool.length?poolProbabilities(weights):[];$('pool-table').replaceChildren();pool.forEach((policy,i)=>row('pool-table',[ids[i],`[${policy.map(fmt)}]`,weights[i],fmt(p[i]),counts?counts[i]:'Not drawn']));$('coverage-table').replaceChildren();for(const [name,policy] of [['Current learner',learner],['PAPER',[0,1,0]],['Uniform',[1/3,1/3,1/3]]])row('coverage-table',[name,...[0,1,2].map(j=>fmt(expectedPayoff(policy,[0,1,2].map(i=>Number(i===j)))))]);$('pool-status').textContent=`Learner [${learner.map(fmt)}]; ${pool.length} saved opponents. Storage=${$('pool-storage').value}; capacity=${integer('pool-capacity',1,6)}; recency weights oldest→newest [${weights}]. ${counts?'1000 draws, browser LCG seed 7.':'Save before sampling.'}`;$('pool-sample').disabled=!pool.length;};
 reset=()=>{learner=[.2,.3,.5];pool=[];ids=[];next=0;counts=null;$('pool-storage').value='copy';$('pool-capacity').value='3';render();};
 listen('save-opponent','click',()=>{const cap=integer('pool-capacity',1,6);pool=[...pool,$('pool-storage').value==='copy'?snapshot(learner):learner].slice(-cap);ids=[...ids,next++].slice(-cap);counts=null;render();});
 listen('mutate-policy','click',()=>{learner.splice(0,3,1,0,0);render();});
 listen('pool-storage','change',()=>{learner=[.2,.3,.5];pool=[];ids=[];next=0;counts=null;render();});
 listen('pool-capacity','input',()=>{const cap=integer('pool-capacity',1,6);pool=pool.slice(-cap);ids=ids.slice(-cap);counts=null;render();});
 listen('pool-sample','click',()=>{counts=drawCounts(poolProbabilities(pool.map((_,i)=>i+1)),1000,randomGenerator(7));render();});
}else if(lab==='p8-audit'){
 let phase=0;
 const renderPairs=()=>{const a=[{id:'s0',score:2},{id:'s1',score:8}],b=[{id:'s1',score:7},{id:'s0',score:1}],correct=$('audit-pairing').value==='ids';const pairs=correct?pairedScores(a,b):a.map((r,i)=>({id:r.id,difference:r.score-b[i].score}));$('audit-table').replaceChildren();a.forEach((r,i)=>{const other=correct?b.find(v=>v.id===r.id):b[i];row('audit-table',[r.id,r.score,other.id,other.score,pairs[i].difference]);});const mean=pairs.reduce((s,r)=>s+r.difference,0)/2,variance=pairs.reduce((s,r)=>s+(r.difference-mean)**2,0)/2;$('audit-status').textContent=`Differences [${pairs.map(r=>r.difference)}]; mean=${mean}; population variance=${variance}. Defined shuffled-pairing statistic: squared paired difference, mean ${pairs.reduce((s,r)=>s+r.difference**2,0)/2} vs ID-matched 1. This two-row illustration is not a significance test or evidence of no learning. 8×128 vector steps=1024 joint transitions.`;};
 const resetCycle=()=>{phase=0;$('lifecycle-table').replaceChildren();$('lifecycle-step').disabled=false;$('lifecycle-status').textContent='Reset: A and B observe 0. AEC pending commitments remain hidden; actual local API checks are in the Python pack.';};
 reset=()=>{$('audit-pairing').value='ids';$('lifecycle-api').value='parallel';renderPairs();resetCycle();};
 listen('audit-pairing','change',renderPairs);listen('lifecycle-api','change',resetCycle);
 listen('lifecycle-step','click',()=>{const api=$('lifecycle-api').value,v=lifecycle(api,phase);row('lifecycle-table',[phase+1,v.selected,v.observation,v.action,v.reward,v.boundary]);phase++;$('lifecycle-step').disabled=Boolean(v.done);$('lifecycle-status').textContent=`${api.toUpperCase()} · ${v.boundary}. ${v.done?'Round ended. Reset or change API to replay.':'Advance to next selected agent.'}`;});
}
if(reset){listen('reset-experiment','click',reset);reset();$('experiment-controls').hidden=false;}
