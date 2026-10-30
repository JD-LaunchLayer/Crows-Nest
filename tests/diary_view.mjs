import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../diary_view.js',import.meta.url),'utf8');
const {createDiary}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
class Element{constructor(){this.children=[];this.text='';this.hidden=true;this.style={};}append(...x){this.children.push(...x);}replaceChildren(){this.children=[];this.text='';}set textContent(v){this.text=String(v);this.children=[];}get textContent(){return this.text+this.children.map(x=>x.textContent).join('');}}
const elements=new Map(),document={pointerLockElement:null,createElement:()=>new Element(),createTextNode:t=>({textContent:t}),getElementById(id){if(!elements.has(id))elements.set(id,new Element());return elements.get(id);}};
const diary=createDiary({document}),get=id=>document.getElementById(id).textContent;
const state={decisions:5,action:'observe',pending:{start:'x'},clock:{date:'Fri 30 Oct',time:'14:55:32'},twin:{started_virtual:'2026-10-29'},
 affect:{valence:-.2,arousal:.1},body:{reserve:30,stomach:0,hydration:80,sleep_debt:5,exertion:0},current_intention:'Find which plants grow on trees',
 next_step:'Look at the ivy again',memories:[{id:1,kind:'started',action:'observe'},{id:2,kind:'experience',event:'Observed ivy flowers with wasps.'}],
 diary:[{at:'2026-10-30T10:00',text:'Pleased to see the insects.',source_id:2}],interests:{ivy:4,'woodland period':-2},
 personality_notes:[{text:'I return to living things.'}],wishes:[{text:'A field guide',status:'expressed'}]};
diary.update(state);
assert.ok(get('diaryNow').includes('watching the woodland')&&get('diaryNow').includes('a little low')&&get('diaryNow').includes('hungry'));
assert.ok(get('diaryNow').includes('time-lapse twin')&&get('diaryBadge').includes('TWIN')&&get('diaryDate').includes('twin clock'));
assert.ok(get('diaryThoughts').includes('Pleased to see the insects.')&&get('diaryThoughts').includes('Observed ivy flowers'));
assert.ok(get('diaryInterests').includes('ivy · drawn to')&&get('diaryInterests').includes('put off by'));
assert.ok(get('diarySelf').includes('I return to living things.'));
diary.toggle();assert.equal(document.getElementById('diary').hidden,false);diary.open(false);assert.equal(document.getElementById('diary').hidden,true);
console.log('PASS: journal summary from saved values; twin labelling; reflections linked to events; interests; self-observations; open/close.');
