const finite=x=>Number.isFinite(x);
const unit=x=>finite(x)&&x>=0&&x<=1;
const action=(x,n)=>{if(!Number.isInteger(x)||x<0||x>=n)throw new Error('Invalid action.');};
export const MATRIX=[[0,-1,1],[1,0,-1],[-1,1,0]];
export function distribution(p){if(!Array.isArray(p)||p.length!==3||p.some(x=>!unit(x))||Math.abs(p.reduce((s,x)=>s+x,0)-1)>1e-10)throw new Error('Three normalized nonnegative probabilities required.');return [...p];}
export function team(a,b){action(a,2);action(b,2);return {reward:2*a+b,differences:[2*a,b],terminated:true};}
export function shapedReturn(rewards,potentials,gamma,shapingGamma=gamma){
 if(potentials.length!==rewards.length+1||[...rewards,...potentials].some(x=>!finite(x))||!unit(gamma)||!unit(shapingGamma))throw new Error('Invalid route or discount.');
 return rewards.reduce((s,r,i)=>s+gamma**i*(r+shapingGamma*potentials[i+1]-potentials[i]),0);
}
export function shapingRoutes(gamma=1,end=0,shapingGamma=gamma){
 return [['DIRECT',[3],[2,0],[3]],['VIA+FINISH',[0,4],[2,1,0],[0,4]],['VIA+WAIT',[0,0],[2,1,end],[0,5]]].map(([name,rewards,potentials,bonus])=>{
  const base=rewards.reduce((s,r,i)=>s+gamma**i*r,0),shaped=shapedReturn(rewards,potentials,gamma,shapingGamma);
  return {name,base,bonus:bonus.reduce((s,r,i)=>s+gamma**i*r,0),shaped,shift:shaped-base,boundary:gamma**rewards.length*potentials.at(-1)};
 });
}
export function laneExpected(p,blocking=true){if(!unit(p)||typeof blocking!=='boolean')throw new Error('Invalid opponent probability or mechanic.');return blocking?1-2*p:1;}
export function laneSamples(p,blocking,count,rng){
 laneExpected(p,blocking);if(!Number.isInteger(count)||count<1)throw new Error('Positive count required.');
 let occupied=0;for(let i=0;i<count;i++){const u=rng();if(!unit(u)||u===1)throw new Error('RNG must return [0,1).');occupied+=u<p?1:0;}
 return {occupation:occupied/count,cross:blocking?1-2*occupied/count:1,wait:0};
}
export function expectedPayoff(policy,opponent){distribution(policy);distribution(opponent);return policy.reduce((s,p,i)=>s+p*MATRIX[i].reduce((r,v,j)=>r+v*opponent[j],0),0);}
export function bestResponses(opponent){distribution(opponent);const v=MATRIX.map(row=>row.reduce((s,r,i)=>s+r*opponent[i],0));return v.flatMap((x,i)=>Math.abs(x-Math.max(...v))<1e-12?[i]:[]);}
export function snapshot(policy){return Object.freeze(distribution(policy));}
export function addSnapshot(pool,policy,capacity){if(!Number.isInteger(capacity)||capacity<1)throw new Error('Positive integer capacity required.');return [...pool,snapshot(policy)].slice(-capacity);}
export function poolProbabilities(weights){if(!weights.length||weights.some(w=>!finite(w)||w<=0))throw new Error('Positive finite weights required.');const max=Math.max(...weights),scaled=weights.map(w=>w/max),total=scaled.reduce((s,w)=>s+w,0);return scaled.map(w=>w/total);}
export function pairedScores(a,b){
 const index=rows=>{const map=new Map();for(const r of rows){if(typeof r.id!=='string'||!r.id||!finite(r.score)||map.has(r.id))throw new Error('Unique scenario IDs and finite scores required.');map.set(r.id,r.score);}if(!map.size)throw new Error('Nonempty scores required.');return map;};
 const left=index(a),right=index(b);if(left.size!==right.size||[...left.keys()].some(k=>!right.has(k)))throw new Error('Scenario coverage differs.');
 return [...left.keys()].sort().map(id=>({id,difference:left.get(id)-right.get(id)}));
}
export function lifecycle(api,phase){
 if(!['parallel','aec'].includes(api)||!Number.isInteger(phase)||phase<0)throw new Error('Invalid lifecycle.');
 if(api==='parallel')return phase===0?{selected:'A,B',observation:'Both see start 0',action:'A=PAPER, B=ROCK',reward:'A=+1, B=−1',boundary:'Both terminated; live agents=[]',done:true}:{done:true};
 const rows=[
  {selected:'A',observation:'0 (no opponent choice)',action:'PAPER',reward:'0',boundary:'Pending commitment; no joint transition'},
  {selected:'B',observation:'0 (A choice hidden)',action:'ROCK',reward:'A=+1, B=−1',boundary:'Joint transition resolves; both terminated'},
  {selected:'A (terminated)',observation:'Terminal 1',action:'None',reward:'A=+1 delivered by last()',boundary:'Remove selected dead A'},
  {selected:'B (terminated)',observation:'Terminal 1',action:'None',reward:'B=−1 delivered by last()',boundary:'Remove selected dead B; agents=[]',done:true}
 ];
 return rows[phase]??{done:true};
}
