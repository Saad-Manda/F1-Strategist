import test from 'node:test';
import assert from 'node:assert/strict';
import {MATRIX,team,shapedReturn,shapingRoutes,laneExpected,laneSamples,expectedPayoff,bestResponses,snapshot,addSnapshot,poolProbabilities,pairedScores,lifecycle} from '../site/labs/assets/experiments/multiagent-models.js';
import {randomGenerator} from '../site/labs/assets/experiments/foundation-models.js';
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-10,`${a} != ${b}`);
test('simultaneous team rewards and IDLE counterfactuals differ',()=>{
 assert.deepEqual(team(1,1),{reward:3,differences:[2,1],terminated:true});
 for(let a=0;a<2;a++)for(let b=0;b<2;b++){const v=team(a,b);close(v.differences[0],v.reward-team(0,b).reward);close(v.differences[1],v.reward-team(a,0).reward);}
 assert.throws(()=>team(2,0));
});
test('shaping preserves routes only under matched discount and boundary assumptions',()=>{
 const rows=shapingRoutes();assert.deepEqual(rows.map(r=>r.base),[3,4,0]);assert.deepEqual(rows.map(r=>r.bonus),[3,4,5]);assert.deepEqual(rows.map(r=>r.shaped),[1,2,-2]);
 for(const gamma of [0,.3,.5,1])for(const end of [0,10])for(const r of shapingRoutes(gamma,end))close(r.shift,-2+r.boundary);
 for(const gamma of [0,.5,1]){const rewards=[1,-2,5],p=[3,8,-1,7],base=rewards.reduce((s,r,i)=>s+gamma**i*r,0);close(shapedReturn(rewards,p,gamma),base-3+gamma**3*7);}
 assert.notEqual(shapingRoutes(.5,0,1)[1].shift,-2);assert.ok(shapingRoutes(1,10)[2].shaped>shapingRoutes(1,10)[1].shaped);
 assert.throws(()=>shapedReturn([1],[2],1));
});
test('mechanics and opponent-distribution changes have distinct witnesses',()=>{
 close(laneExpected(.2),.6);close(laneExpected(.8),-.6);close(laneExpected(.8,false),1);
 for(const seed of [7,19,31]){const on=laneSamples(.8,true,10000,randomGenerator(seed)),off=laneSamples(.8,false,10000,randomGenerator(seed));close(on.occupation,off.occupation);close(off.cross,1);close(on.cross,1-2*on.occupation);assert.ok(Math.abs(on.occupation-.8)<.02);}
 assert.throws(()=>laneExpected(1.1));
});
test('RPS exact payoffs and best responses match independent modular winner rule',()=>{
 for(let i=0;i<3;i++)for(let j=0;j<3;j++)assert.equal(MATRIX[i][j],i===j?0:(i-j+3)%3===1?1:-1);
 close(expectedPayoff([0,1,0],[.5,.25,.25]),.25);
 for(let j=0;j<3;j++){const pure=[0,1,2].map(i=>Number(i===j));close(expectedPayoff([1/3,1/3,1/3],pure),0);assert.deepEqual(bestResponses(pure),[(j+1)%3]);}
 assert.throws(()=>expectedPayoff([1,1,1],[1,0,0]));
});
test('pool snapshots are independent frozen values and bounded retention is separate',()=>{
 const learner=[.2,.3,.5],saved=snapshot(learner);learner.splice(0,3,1,0,0);assert.deepEqual(saved,[.2,.3,.5]);assert.ok(Object.isFrozen(saved));assert.throws(()=>saved[0]=1);
 let pool=[];for(const p of [[1,0,0],[0,1,0],[0,0,1]])pool=addSnapshot(pool,p,2);assert.deepEqual(pool,[[0,1,0],[0,0,1]]);
 poolProbabilities([1,2,3]).forEach((p,i)=>close(p,[1/6,1/3,1/2][i]));assert.throws(()=>poolProbabilities([0,1]));
});
test('ID pairing survives reordered rows and lifecycle preserves hidden commitments',()=>{
 assert.deepEqual(pairedScores([{id:'s0',score:2},{id:'s1',score:8}],[{id:'s1',score:7},{id:'s0',score:1}]),[{id:'s0',difference:1},{id:'s1',difference:1}]);
 assert.throws(()=>pairedScores([{id:'s0',score:2}],[{id:'s1',score:1}]));
 assert.equal(lifecycle('parallel',0).done,true);assert.match(lifecycle('aec',1).observation,/hidden/);
 assert.equal(lifecycle('aec',2).action,'None');assert.equal(lifecycle('aec',3).action,'None');assert.equal(lifecycle('aec',3).done,true);
});
