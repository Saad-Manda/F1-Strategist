import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {randomGenerator} from '../site/labs/assets/experiments/foundation-models.js';
import {tdUpdate,epsilonProbabilities,selectAction,sarsaTarget,binIndex,tableSize,representationCeiling,trainBandit,trainShortcut,trainBins} from '../site/labs/assets/experiments/tabular-models.js';
const fixture=id=>JSON.parse(readFileSync(new URL(`../site/labs/downloads/${id}/fixtures.json`,import.meta.url)));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);

test('masked TD arithmetic and termination versus truncation',()=>{
 const f=fixture('p4-td');
 for(const [terminal,truncated,key] of [[false,false,'ongoing'],[false,true,'ongoing'],[true,false,'terminal'],[true,true,'terminal']]){
  const actual=tdUpdate(f.q,f.reward,f.next_values,f.legal,f.alpha,f.gamma,terminal,truncated);
  for(const property of ['target','error','value'])close(actual[property],f[key][property]);
 }
 assert.equal(tdUpdate(2,1,[],[],0.25,0.5,true).target,1);
 assert.equal(tdUpdate(-3,-1,[-8,-2,99],[true,true,false],1,1,false).target,-3);
 assert.throws(()=>tdUpdate(2,1,[8],[false],0.25,0.5,false));
 assert.throws(()=>tdUpdate(2,1,[8],[true],-1,0.5,false));
});
test('epsilon probabilities include greedy exploration, masks, ties, and exact interval boundaries',()=>{
 const f=fixture('p4-explore');
 assert.deepEqual(epsilonProbabilities(f.q,f.legal,0.2),f.epsilon_02);
 assert.deepEqual(epsilonProbabilities(f.q,f.legal,1),f.epsilon_1);
 assert.deepEqual(epsilonProbabilities([3,3,99],f.legal,0),f.tie);
 assert.equal(selectAction(f.q,f.legal,0.2,()=>0.899),0);assert.equal(selectAction(f.q,f.legal,0.2,()=>0.9),1);
 assert.equal(selectAction([99,2],[false,true],0,()=>0),1);
 assert.throws(()=>selectAction([1],[true],0,()=>1));assert.throws(()=>epsilonProbabilities([1],[false],0));
 for(const seed of [7,31,89]){const rng=randomGenerator(seed);let zero=0;for(let i=0;i<10000;i++)zero+=selectAction([1,1],[true,true],0,rng)===0;assert.ok(Math.abs(zero/10000-0.5)<0.02);}
});
test('sampled SARSA target and policy expectation are distinct from max target',()=>{
 const f=fixture('p4-sarsa');
 assert.equal(sarsaTarget(f.risk_q,1),f.sampled_slip_target);assert.equal(Math.max(...f.risk_q),f.q_learning_target);
 for(const [epsilon,value] of [[0.2,f.epsilon_02_behaviour],[0.6,f.epsilon_06_behaviour]]){
  const p=epsilonProbabilities(f.risk_q,[true,true],epsilon);close(p.reduce((s,p,i)=>s+p*f.risk_q[i],0),value);
 }
});
test('bin equality convention, endpoints, nonuniform edges, and dense counts',()=>{
 const f=fixture('p4-bins');for(const [x,b] of f.witnesses)assert.equal(binIndex(x,f.split_edges),b);
 assert.equal(binIndex(0.49,[0,1]),binIndex(0.51,[0,1]));assert.equal(binIndex(0.45,[0,0.45,0.5,0.55,1]),1);
 assert.deepEqual(tableSize([4,4,4]),f.size);assert.equal(tableSize([8,8,8]).entries/tableSize([4,4,4]).entries,8);
 assert.equal(tableSize([12,5,10,3,3,2,8,2],6).states,172800);
 assert.equal(representationCeiling([0,1]),0.5);assert.equal(representationCeiling([0,0.5,1]),1);close(representationCeiling([0,0.7,1]),0.8);
 for(const edges of [[0,0.5,0.5,1],[0,0.8,0.5,1],[0.1,1]])assert.throws(()=>binIndex(0.5,edges));
 assert.throws(()=>binIndex(1.1,[0,1]));assert.throws(()=>tableSize([0]));
});
test('seeded browser comparisons reproduce and expose valid sampled counts without win gates',()=>{
 for(const seed of [7,31,89]){
  const bandit=trainBandit(seed,200,0.2);assert.deepEqual(bandit,trainBandit(seed,200,0.2));
  assert.equal(bandit.visits.reduce((a,b)=>a+b),200);assert.equal(bandit.visits[2],0);assert.equal(bandit.evalVisits.reduce((a,b)=>a+b),200);
  for(const algorithm of ['q-learning','sarsa']){const r=trainShortcut(seed,200,0.2,0.1,algorithm);assert.deepEqual(r,trainShortcut(seed,200,0.2,0.1,algorithm));assert.ok(r.slips>=0&&r.slips<=200);assert.ok(r.evaluationMean>=-10&&r.evaluationMean<=6);}
  const coarse=trainBins(seed,200,[0,1]);assert.equal(coarse.evaluationMean,0.5);assert.equal(coarse.ceiling,0.5);
  assert.deepEqual(trainBins(seed,200,[0,0.5,1]),trainBins(seed,200,[0,0.5,1]));
 }
 assert.throws(()=>trainBandit(7,0,0.2));
});
