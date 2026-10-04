// Exact teaching calculations; no hidden training or Python execution.
const finite=x=>Number.isFinite(x);
const vector=a=>Array.isArray(a)&&a.length&&a.every(finite);
const unit=x=>finite(x)&&x>=0&&x<=1;
export function linearStep(x,weight,bias,rate){
  if(!unit(x)||!unit(rate)||!vector(weight)||!vector(bias)||weight.length!==2||bias.length!==2)throw new Error('Invalid linear inputs.');
  const labels=[x,1-x],prediction=weight.map((w,i)=>x*w+bias[i]);
  const gb=prediction.map((p,i)=>p-labels[i]),gw=gb.map(g=>g*x);
  return {labels,prediction,gb,gw,loss:gb.reduce((s,g)=>s+g*g,0)/2,weight:weight.map((w,i)=>w-rate*gw[i]),bias:bias.map((b,i)=>b-rate*gb[i])};
}
export function fifo(buffer,item,capacity=4){
  if(!Number.isInteger(capacity)||capacity<1)throw new Error('Positive integer capacity required.');
  return [...buffer,item].slice(-capacity);
}
export function doubleTarget(online,target,legal,reward,gamma,terminated=false){
  if(!vector(online)||!vector(target)||online.length!==target.length||legal.length!==online.length||!legal.every(v=>typeof v==='boolean')||!finite(reward)||!unit(gamma))throw new Error('Invalid target inputs.');
  if(terminated)return {selected:null,double:reward,vanilla:reward};
  const indices=legal.flatMap((v,i)=>v?[i]:[]);
  if(!indices.length)throw new Error('No legal successor action.');
  const selected=indices.reduce((best,i)=>online[i]>online[best]?i:best,indices[0]);
  return {selected,double:reward+gamma*target[selected],vanilla:reward+gamma*Math.max(...indices.map(i=>target[i]))};
}
export function dueling(value,advantage){
  if(!finite(value)||!vector(advantage))throw new Error('Finite value and advantages required.');
  const mean=advantage.reduce((s,a)=>s+a,0)/advantage.length;
  return advantage.map(a=>value+a-mean);
}
export function priorities(raw,alpha,beta){
  if(!vector(raw)||raw.some(p=>p<=0)||!unit(alpha)||!unit(beta))throw new Error('Positive finite priorities; alpha/beta in [0,1].');
  const masses=raw.map(p=>p**alpha),total=masses.reduce((s,p)=>s+p,0),probabilities=masses.map(p=>p/total);
  const unnormalized=probabilities.map(p=>(raw.length*p)**(-beta)),max=Math.max(...unnormalized);
  return {masses,probabilities,weights:unnormalized.map(w=>w/max)};
}
export function weightedLoss(losses,weights){
  if(!vector(losses)||!vector(weights)||losses.length!==weights.length||losses.some(l=>l<0)||weights.some(w=>!unit(w)))throw new Error('Invalid per-item losses/weights.');
  return losses.reduce((s,l,i)=>s+l*weights[i],0)/losses.length;
}
export function drawCounts(probabilities,draws,rng){
  if(!vector(probabilities)||probabilities.some(p=>p<0)||Math.abs(probabilities.reduce((s,p)=>s+p,0)-1)>1e-10||!Number.isInteger(draws)||draws<1)throw new Error('Invalid sampling request.');
  const counts=probabilities.map(()=>0);
  for(let i=0;i<draws;i++){
    const u=rng();if(!finite(u)||u<0||u>=1)throw new Error('RNG must return [0,1).');
    let c=0,index=probabilities.length-1;
    for(let j=0;j<probabilities.length;j++){c+=probabilities[j];if(u<c){index=j;break;}}
    counts[index]++;
  }
  return counts;
}
