import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {returns, branchValues, backward, expectedValue, advance, WEATHER, randomGenerator, sampleNext, switchStep} from '../site/labs/assets/experiments/foundation-models.js';

const fixture = id => JSON.parse(readFileSync(new URL(`../site/labs/downloads/${id}/fixtures.json`,import.meta.url)));
const close = (a,b) => assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);

test('switch histories expose observation aliasing',()=>{
  const f=fixture('p1-state');
  assert.equal(switchStep(0,'CLAIM').reward,f.claim_reward);
  assert.equal(switchStep(switchStep(0,'FLIP').mode,'CLAIM').reward,f.flip_claim_reward);
  assert.equal(switchStep(0,'FLIP').terminated,false);
  assert.equal(switchStep(1,'CLAIM').terminated,true);
  assert.throws(()=>switchStep(2,'CLAIM'));
});
test('returns match hand arithmetic and independent forward powers',()=>{
  const f=fixture('p1-return');
  for(const [gamma,result] of Object.entries(f.returns)) assert.deepEqual(returns(f.rewards,Number(gamma)),result);
  for(const gamma of [0,0.17,0.8,1]) {
    const r=[1,-4,0,7,-2];
    returns(r,gamma).forEach((value,t)=>close(value,r.slice(t).reduce((sum,reward,k)=>sum+gamma**k*reward,0)));
  }
  assert.deepEqual(returns([],0.5),[]);
  assert.throws(()=>returns([1],-1)); assert.throws(()=>returns([NaN],0.5));
});
test('policy expectation differs from legal optimality',()=>{
  const f=fixture('p1-values');
  for(const [gamma,expected] of [[0.5,f.gamma_half],[1,f.gamma_one]]) {
    const v=branchValues(gamma,0.5); close(v.policy,expected[0]);close(v.optimal,expected[1]);
  }
  assert.equal(branchValues(1,0).policy,3);assert.equal(branchValues(1,1).policy,5);
  assert.throws(()=>branchValues(1,-0.1));
});
test('backward induction matches exhaustive action paths and horizon witnesses',()=>{
  const f=fixture('p35-backward');
  assert.deepEqual(backward(2,1).map(r=>r.A),f.horizon_values);
  const paths=(s,h)=>s==='T'||h===0?[[]]:(s==='A'?[['T',3],['B',1]]:[['T',4]]).flatMap(([next,r])=>paths(next,h-1).map(tail=>[r,...tail]));
  for(const gamma of [0,0.25,0.5,0.75,1]) for(const h of [0,1,2,3,5]) {
    const rows=backward(h,gamma);
    for(const state of ['A','B'])close(rows[h][state],Math.max(...paths(state,h).map(path=>path.reduce((sum,r,k)=>sum+gamma**k*r,0))));
  }
  assert.equal(backward(1,1)[1].action,'DIRECT'); assert.equal(backward(2,1)[2].action,'VIA');
  assert.throws(()=>backward(1.5,1));assert.throws(()=>backward(2,NaN));
});
test('lottery expectations and invalid probability rows',()=>{
  const f=fixture('p35-stochastic');
  for(const [p,value] of [[0.25,1],[0.5,4],[1/3,2],[0,-2],[1,10]])close(expectedValue([[p,f.win_reward],[1-p,f.loss_reward]]),value);
  for(const outcomes of [[],[[0.4,10],[0.4,-2]],[[-0.1,10],[1.1,-2]],[[1,Infinity]]])assert.throws(()=>expectedValue(outcomes));
});
test('weather arithmetic, stationarity, categorical boundaries and seeded sampling',()=>{
  const f=fixture('p35-markov');
  advance(advance([1,0])).forEach((p,i)=>close(p,f.two_step[i]));
  advance(f.stationary).forEach((p,i)=>close(p,f.stationary[i]));
  assert.equal(sampleNext(0,()=>0.799),0);assert.equal(sampleNext(0,()=>0.8),1);
  assert.throws(()=>sampleNext(0,()=>1));
  const a=randomGenerator(7),b=randomGenerator(7);
  assert.deepEqual(Array.from({length:20},()=>sampleNext(0,a)),Array.from({length:20},()=>sampleNext(0,b)));
  for(const state of [0,1])for(const seed of [7,31,89]){
    const rng=randomGenerator(seed);
    const frequency=Array.from({length:10000},()=>sampleNext(state,rng)).filter(s=>s===0).length/10000;
    assert.ok(Math.abs(frequency-WEATHER[state][0])<0.02);
  }
  assert.throws(()=>advance([1,0],[[0.4,0.4],[0.3,0.7]]));assert.throws(()=>randomGenerator(-1));
});
