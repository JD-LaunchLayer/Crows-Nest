import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../life_view.js',import.meta.url),'utf8');
const {createLifeView}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
class Element{constructor(){this.children=[];this.text='';}append(...x){this.children.push(...x);}replaceChildren(){this.children=[];this.text='';}set textContent(v){this.text=String(v);this.children=[];}get textContent(){return this.text+this.children.map(x=>x.textContent).join('');}}
const elements=new Map(),document={createElement:()=>new Element(),getElementById(id){if(!elements.has(id))elements.set(id,new Element());return elements.get(id);}};
const view=createLifeView({document}),get=id=>document.getElementById(id).textContent;
const trial={intention:'Test a shape.',goal_met:false,hypothesis:'This might work.',parameters:{support:'hand',passes:'deep'},predicted_success:true,expected_error_mm:3,actual_error_mm:17,target_error_mm:6,adjustment:'Try a lighter pass.',object_id:'carving-1',source_id:7};
const state={body:{reserve:30,stomach:0,hydration:25,sleep_debt:9,exertion:.7},provisions:{pantry:24,berries:8,water_litres:40},appraisals:[{meaning:'The result surprised me.',concern:'Test a shape.'}],practical:{trials:[trial],methods:[{id:'hand:deep:along',successes:0,attempts:1,best_error_mm:17,shapes:[]}]},suspended_work:[]};
view.update(state);assert.ok(get('bodySignals').includes('hunger'));assert.ok(get('bodySignals').includes('thirst'));assert.ok(get('bodySignals').includes('sleepiness'));
assert.ok(get('experiments').includes('He predicted: success'));assert.ok(get('experiments').includes('Measured width error: 17 mm'));assert.ok(get('testedMethods').includes('No successful trial'));
assert.ok(get('affectContext').includes('Test a shape.'));
state.suspended_work=[{id:3,pending:{decision:{intention:'Continue my object.'},remaining:1200}}];view.update(state);assert.ok(get('experiments').includes('20 minutes remain'));
state.pending={decision:{action:'craft',intention:'A second test.',attempt:{hypothesis:'Support might help.',target_error_mm:6,expected_error_mm:4}}};view.update(state);assert.ok(get('experiments').includes('Result pending'));
state.mind={life:[{id:1,text:'Wasps visit ivy flowers.',strength:.9,previous:[{text:'old'}]}],skills:[],world:[],forgotten:[{text:'Lost detail.'}]};state.model_spend={usd:.012,total_usd:.5,fallbacks:1};state.runtime={model_usage:{choose_action:{provider:'anthropic',model:'claude-haiku-5-5'}}};view.update(state);
assert.ok(get('mind').includes('Wasps visit ivy flowers. (revised)'));assert.ok(get('mind').includes('Lost detail.'));assert.ok(get('modelSpend').includes('Claude claude-haiku-5-5'));assert.ok(get('modelSpend').includes('1 fallbacks'));
console.log('PASS: held memories with revisions and forgetting; model and spend line; bodily signals, supplies, current prediction, measured outcomes, tentative correction, tested-method evidence and paused work remain read-only.');
