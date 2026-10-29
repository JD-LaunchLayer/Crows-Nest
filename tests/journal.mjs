import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../journal.js',import.meta.url),'utf8');
const {createJournal}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.ownText='';this.hidden=false;}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=[...children];this.ownText='';}
 set textContent(value){this.ownText=String(value);this.children=[];}
 get textContent(){return this.ownText+this.children.map(child=>child.textContent).join('');}
}
const elements=new Map(),document={createElement:tag=>new Element(tag),getElementById(id){if(!elements.has(id))elements.set(id,new Element());return elements.get(id);}};
const $=id=>document.getElementById(id),all=(parent,tag)=>parent.children.flatMap(child=>[...(child.tag===tag?[child]:[]),...all(child,tag)]);
const record={id:10,at:'2026-10-29T10:00:00Z',title:'Wood grain',url:'https://en.wikipedia.org/wiki/Wood_grain',query:'wood grain',question:'How are the fibres arranged?',intention:'Inspect some material.',reason:'I have a question.',mode:'lookup',status:'processed',summary:'The excerpt describes fibre arrangement.',lesson:'I need to inspect the piece.',answer_status:'partial',next_step:'Inspect the piece.',processed_chars:30};
const calls=[];
const journal=createJournal({document,apiFetch:async url=>{calls.push(url);if(url==='/api/reading/10')return{ok:true,json:async()=>({text:'A real saved source excerpt is longer than this.',journal:record})};return{ok:true,json:async()=>({items:[{...record,id:5,title:'Earlier reading',url:'javascript:alert(1)',summary:''}],total:2})};}});
const state={reading_count:2,reading_log:[record],action:'read',next_step:'Inspect the piece.',pending:{decision:{action:'read',research_question:record.question,reading_mode:'lookup'},reading:{title:'Wood grain'},start:record.at}};
journal.update(state);
assert.ok($('activityDetails').textContent.includes(record.question));assert.ok($('nextStep').textContent.includes('Tentative next step'));
assert.ok($('readingLog').textContent.includes(record.summary));assert.ok($('readingLog').textContent.includes('His assessment: partly answered'));
assert.equal(all($('readingLog'),'a')[0].href,record.url);
const card=$('readingLog').children[0];journal.update(state);assert.equal($('readingLog').children[0],card); // Preserve open panels between polls.
await all(card,'button')[0].onclick();assert.deepEqual(calls,['/api/reading/10']);
let pre=all($('readingLog'),'pre')[0];assert.equal(pre.hidden,false);assert.ok(pre.textContent.includes('30 characters'));assert.ok(!pre.textContent.includes('longer than this.'));
await $('olderReading').onclick();assert.equal(calls[1],'/api/reading?before=10');
assert.ok($('readingLog').textContent.includes('Earlier reading'));assert.equal(all($('readingLog'),'a').length,1); // Unsafe source URL is plain text.
assert.equal($('olderReading').hidden,true);assert.ok($('readingLogStatus').textContent.includes('2 of 2'));
assert.equal(all($('readingLog'),'pre')[0].hidden,false);
journal.update({...state,next_step:'',pending:{decision:{action:'construct',plan_id:7,object_id:'library'},start:record.at},built_world:{objects:{library:{name:'Reading cabin'}},plans:[{id:7,name:'An opening',minutes:30,work_done_minutes:10,status:'in_progress',bill:{wood:3}}]}});
assert.ok($('activityDetails').textContent.includes('Reading cabin'));assert.ok($('activityDetails').textContent.includes('10/30 minutes'));
assert.ok($('activityDetails').textContent.includes('3 kg wood'));assert.equal($('nextStep').textContent,'Crow has not chosen a next step yet.');
console.log('PASS: observer detail, tentative next step, attributed source/notes, lazy exact excerpt, stable polling, older history, safe links, construction target/material detail.');
