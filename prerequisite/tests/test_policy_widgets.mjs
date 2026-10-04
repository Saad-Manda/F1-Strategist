// Control-level regression checks; real-browser layout QA remains separate.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
class Element {
 constructor(value=''){this.value=value;this.children=[];this.events={};this.hidden=true;this.checked=false;this.textContent='';this.selectedOptions=[{textContent:'Boundary'}];this.style={};}
 append(x){this.children.push(x);} replaceChildren(...xs){this.children=xs;} setAttribute(){}
 addEventListener(name,handler){this.events[name]=handler;} fire(name){assert.ok(this.events[name],`Missing ${name} handler`);this.events[name]();}
}
async function mount(lab,values){
 const elements=new Map(Object.entries(values).map(([id,v])=>[id,new Element(v)]));
 const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
 globalThis.document={body:{dataset:{labId:lab}},getElementById:get,createElement:()=>new Element(),createElementNS:()=>new Element()};
 globalThis.fetch=async()=>({ok:true,json:async()=>JSON.parse(await readFile(new URL('../site/labs/fixtures/p9-ppo-integration.json',import.meta.url),'utf8'))});
 await import(`../site/labs/assets/experiments/policy.js?lab=${lab}`);
 return get;
}
const cells=(get,id)=>get(id).children.map(tr=>tr.children.map(td=>td.textContent));
test('REINFORCE control applies preview and reset restores original witness',async()=>{
 const get=await mount('p9-reinforce',{'logit-a':'0','logit-b':'0','pg-action':'0','pg-return':'2','pg-rate':'.1'});
 assert.equal(get('experiment-controls').hidden,false);assert.equal(cells(get,'pg-table')[0][5],'0.549834');
 get('pg-update').fire('click');assert.equal(Number(get('logit-a').value),.1);assert.equal(cells(get,'pg-table')[0][2],'0.549834');
 get('reset-experiment').fire('click');get('pg-return').value='-2';get('pg-return').fire('input');assert.equal(cells(get,'pg-table')[0][5],'0.450166');
});
test('baseline controls expose action-dependence and poor-baseline variance',async()=>{
 const get=await mount('p9-advantage',{'baseline':'5','baseline-form':'state'});
 assert.match(get('variance-status').textContent,/variances: 0\./);
 get('baseline').value='-5';get('baseline').fire('input');assert.match(get('variance-status').textContent,/variances: 50\./);
 get('baseline-form').value='action';get('baseline-form').fire('change');assert.match(get('advantage-status').textContent,/\[0.25,-0.25\]/);
});
test('GAE reveals reverse steps, changes boundaries and resets disclosure',async()=>{
 const get=await mount('p9-gae',{'gae-lambda':'1','gae-boundary':'terminal','gae-source':'final'});
 get('gae-reverse').fire('click');assert.equal(cells(get,'gae-table')[1][7],'1');assert.equal(cells(get,'gae-table')[0][7],'Reveal reverse step');
 get('gae-reverse').fire('click');assert.equal(cells(get,'gae-table')[0][7],'2.3');
 get('gae-boundary').value='truncated';get('gae-boundary').fire('input');assert.equal(cells(get,'gae-table')[0][7],'Reveal reverse step');
 get('gae-reverse').fire('click');get('gae-reverse').fire('click');assert.equal(cells(get,'gae-table')[0][7],'4.73');
 get('gae-source').value='reset';get('gae-source').fire('input');get('gae-reverse').fire('click');assert.equal(cells(get,'gae-table')[1][7],'91');
});
test('PPO steps can overshoot clip interval; moving-old bug hides drift',async()=>{
 const get=await mount('p9-ppo',{'ppo-ratio':'1.3','ppo-sign':'1','ppo-epsilon':'.2'});
 assert.match(get('ppo-status').textContent,/objective 1.2/);
 get('ppo-policy-step').fire('click');get('ppo-policy-step').fire('click');
 assert.match(get('ppo-policy-status').textContent,/old P\(A\)=0.5/);assert.match(get('ppo-policy-status').textContent,/clip fraction=1/);
 const before=get('ppo-policy-status').textContent;get('ppo-policy-step').fire('click');
 assert.equal(get('ppo-policy-status').textContent.replace('Steps 3','Steps 2'),before);
 get('reset-experiment').fire('click');get('old-policy-bug').checked=true;
 get('ppo-policy-step').fire('click');get('ppo-policy-step').fire('click');get('ppo-policy-step').fire('click');
 assert.match(get('ppo-policy-status').textContent,/ratio=1;/);assert.match(get('ppo-policy-status').textContent,/exact KL\(old‖new\)=0;/);assert.ok(parseFloat(get('ppo-policy-status').textContent.match(/original rollout KL=([\d.]+)/)[1])>0);
});
