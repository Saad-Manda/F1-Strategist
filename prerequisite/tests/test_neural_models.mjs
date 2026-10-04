import test from 'node:test';
import assert from 'node:assert/strict';
import {linearStep,fifo,doubleTarget,dueling,priorities,weightedLoss,drawCounts} from '../site/labs/assets/experiments/neural-models.js';
import {randomGenerator} from '../site/labs/assets/experiments/foundation-models.js';
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-10,`${a} != ${b}`);
test('mean loss gradients and SGD match hand witness and finite differences',()=>{
 const v=linearStep(.25,[0,0],[0,0],.1);close(v.loss,.3125);
 assert.deepEqual(v.gb,[-.25,-.75]);assert.deepEqual(v.gw,[-.0625,-.1875]);
 const h=1e-5;
 for(let i=0;i<2;i++){const a=[0,0],b=[0,0];a[i]=h;b[i]=-h;close((linearStep(.25,a,[0,0],0).loss-linearStep(.25,b,[0,0],0).loss)/(2*h),v.gw[i]);}
 close(v.bias[0],.025);close(v.weight[1],.01875);
 assert.throws(()=>linearStep(NaN,[0,0],[0,0],.1));
});
test('FIFO is bounded and does not mutate old buffer',()=>{
 let b=[];for(let i=0;i<6;i++)b=fifo(b,i);assert.deepEqual(b,[2,3,4,5]);
 const previous=b;fifo(b,6);assert.deepEqual(previous,[2,3,4,5]);assert.throws(()=>fifo([],1,0));
});
test('Double selection, legal masking, terminal handling, dueling invariance',()=>{
 const v=doubleTarget([5,4,100],[1,7,99],[true,true,false],1,.5);assert.deepEqual(v,{selected:0,double:1.5,vanilla:4.5});
 assert.deepEqual(doubleTarget([5],[7],[false],1,.5,true),{selected:null,double:1,vanilla:1});
 assert.throws(()=>doubleTarget([5],[7],[false],1,.5));
 assert.deepEqual(dueling(2,[1,3]),[1,3]);assert.deepEqual(dueling(2,[11,13]),[1,3]);
});
test('raw priority probabilities and global normalized weighted loss',()=>{
 const v=priorities([1,4,9],.5,1);v.probabilities.forEach((p,i)=>close(p,[1/6,1/3,1/2][i]));
 v.weights.forEach((w,i)=>close(w,[1,.5,1/3][i]));close(weightedLoss([1,4,9],v.weights),2);
 const uniform=priorities([1,4,9],0,1);assert.deepEqual(uniform.weights,[1,1,1]);uniform.probabilities.forEach(p=>close(p,1/3));
 assert.throws(()=>priorities([0,1],.5,1));assert.throws(()=>weightedLoss([1,2],[1]));
});
test('seeded categorical sampling is reproducible with declared frequency tolerance',()=>{
 const p=priorities([1,4,9],.5,1).probabilities;
 for(const seed of [7,19,31]){const counts=drawCounts(p,10000,randomGenerator(seed));assert.deepEqual(counts,drawCounts(p,10000,randomGenerator(seed)));counts.forEach((n,i)=>assert.ok(Math.abs(n/10000-p[i])<.02));}
 assert.throws(()=>drawCounts([.5,.5],10,()=>1));
});
