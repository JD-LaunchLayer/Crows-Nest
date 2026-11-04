import {readFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const threeURL = new URL('../vendor/three.module.js', import.meta.url).href;
const source = (await readFile(new URL('../world.js', import.meta.url), 'utf8')).replace("import * as T from '/vendor/three.module.js';", '').replace("import {installTouchControls} from '/mobile_controls.js';", '').replace("import {createSky} from '/sky.js';", '').replace("import {createJournal} from '/journal.js';", '').replace("import {buildVillage,VILLAGE} from '/village.js';", '').replace("import {createPlayer} from '/music_player.js';", '').replace("import {createLifeView} from '/life_view.js';", '').replace("import {createDiary} from '/diary_view.js';", '');
let prefix = "import * as RealThree from THREE_URL;\nimport assert from 'node:assert/strict';\nconst elements=new Map();\nfunction element(){return {clientWidth:1000,clientHeight:800,children:[],textContent:'',append(...x){this.children.push(...x)},prepend(...x){this.children.unshift(...x)},replaceChildren(){this.children=[]},remove(){},getContext(){return {fillRect(){},fillText(){}}}}}\nglobalThis.document={getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id)},createElement(){return element()},addEventListener(){},pointerLockElement:null};\nglobalThis.devicePixelRatio=1;globalThis.addEventListener=()=>{};globalThis.requestAnimationFrame=()=>{};globalThis.setInterval=()=>{};\nclass MockRenderer{constructor(){this.domElement=element();this.shadowMap={}}setPixelRatio(){}setSize(){}render(){}}\nconst T={...RealThree,WebGLRenderer:MockRenderer};\nconst testState={decisions:1,paused:false,daylight:0,action:'read',location:'library',clock:{date:'Wed 28 Oct',time:'23:00',timezone:'Europe/London'},runtime:{status:'Reading'},last_seconds:2,last_error:'',reason:'I want to read.',energy:80,materials:4,skills:{archery:2,craft:1},current_intention:'Read about trees.',memories:[],wishes:[],projects:[],emotions:{joy:50},appraisals:[],long_term:[],creations:[],pending:{decision:{reading_spot:'chair'},remaining:900,duration:900,reading:{title:'Tree',url:'https://en.wikipedia.org/wiki/Tree'}}};\nglobalThis.fetch=async()=>({ok:true,json:async()=>structuredClone(testState)});\n".replace("THREE_URL", JSON.stringify(threeURL));
const villageSource=await readFile(new URL('../village.js', import.meta.url), 'utf8');
const villageObject=villageSource.slice(villageSource.indexOf('export const VILLAGE = ')+'export const VILLAGE = '.length,villageSource.indexOf('\n};\n')+2);
prefix='const VILLAGE='+villageObject+';\nconst buildVillage=()=>{};const createPlayer=()=>({follow(){},play(){},setEnabled(){},enabled:false});const createLifeView=()=>({update(){}});const createDiary=()=>({update(){},open(){},toggle(){}});const createJournal=()=>({update(){}});const createSky=()=>({update:()=>({sun:{altitude:0},moon:{altitude:0}}),frame(){}});\n'+prefix;
const fixtureJSON=execFileSync('python3',['-c',"import world_state,json;s={'materials':1,'creations':[{'id':1,'name':'Test carving','shape':'orb'}],'location':'library'};print(json.dumps(world_state.ensure(s)))"],{cwd:fileURLToPath(new URL('..',import.meta.url)),encoding:'utf8'});
prefix='const fixtureBuiltWorld='+fixtureJSON+';\n'+prefix;
const interactionJSON=execFileSync('python3',['-c',"import world_state,life,interactions,json;s={'materials':2,'creations':[],'location':'workbench'};world_state.ensure(s);life.ensure(s);interactions.ensure(s);d={'verb':'shape','creation_name':'My piece','interaction_params':{'material':'wood','shape':'box','mass_kg':1,'width_m':.2,'depth_m':.2,'support':'bench','passes':'light'}};interactions.prepare(s,d);r=interactions.execute(s,d,1800);d={'verb':'place_on','object_id':r['object_id'],'other_id':'workbench','interaction_params':{'part_id':'top'}};interactions.prepare(s,d);interactions.execute(s,d,180);print(json.dumps(s['built_world']))"],{cwd:fileURLToPath(new URL('..',import.meta.url)),encoding:'utf8'});
prefix='const fixtureInteractedWorld='+interactionJSON+';\n'+prefix;
let tail = "await refresh();\nlet testTime=performance.now();\nfunction advance(seconds){for(let i=0;i<Math.ceil(seconds/.05);i++){testTime+=50;frame(testTime)}}\nadvance(35);\nassert.equal(anim.pose,'reading');assert.equal(anim.book,true);assert.equal(heldBook.visible,true);assert.equal(shelfBook.visible,false);assert.equal(anim.seated,1);\nassert.ok(crow.position.distanceTo(new T.Vector3(LIB.seat.x,-.28,LIB.seat.z))<.05);\nassert.ok(legs.every(x=>Math.abs(x.rotation.x+Math.PI/2)<.02));\nassert.ok(fits(-11,7));assert.ok(!fits(-8.5,7));assert.ok(!fits(-7.5,10));\n$('find').onclick();assert.ok(fits(camera.position.x,camera.position.z));\nconst snapshot=crow.position.clone();s.paused=true;advance(3);assert.ok(crow.position.distanceTo(snapshot)<.01);s.paused=false;\ntestState.decisions=2;testState.action='explore';testState.location='woods';testState.pending={remaining:1200,duration:1200};await refresh();\nadvance(50);assert.equal(anim.book,false);assert.equal(shelfBook.visible,true);assert.equal(anim.seated,0);assert.equal(anim.returning,false);assert.equal(anim.pose,'explore');assert.ok(crow.position.distanceTo(stations.woods)<.1);\nconsole.log('PASS: real Three.js scene construction; book pickup; sitting pose; pause; book return; exit and next activity; doorway/collision; Find Crow position.');\n\ntestState.decisions=3;testState.action='read';testState.location='library';testState.pending={decision:{reading_spot:'standing'},remaining:900,duration:900};await refresh();advance(55);\nassert.equal(anim.pose,'readingStanding');assert.equal(anim.seated,0);assert.equal(anim.book,true);\ntestState.decisions=4;testState.pending.decision.reading_spot='floor';await refresh();advance(65);\nassert.equal(anim.pose,'readingFloor');assert.equal(anim.floor,1);assert.equal(anim.seated,1);\ntestState.decisions=5;testState.action='explore';testState.location='woods';testState.pending={remaining:1200,duration:1200};await refresh();advance(60);\nassert.equal(anim.pose,'explore');assert.equal(anim.floor,0);assert.equal(anim.book,false);assert.ok(crow.position.distanceTo(stations.woods)<.1);\nconsole.log('PASS: chair is optional; standing and floor reading execute only when selected, with clean book return.');\n";
tail+="\ntestState.built_world=fixtureBuiltWorld;await refresh();\nassert.equal(shellReplaced,true);assert.ok(worldMeshes.has('library'));assert.ok(worldMeshes.has('carving-1'));\nassert.equal(fits(-8.3,13),false);\nfixtureBuiltWorld.objects.library.parts=fixtureBuiltWorld.objects.library.parts.filter(p=>p.id!=='back');fixtureBuiltWorld.objects.library.revision++;\nfixtureBuiltWorld.objects['carving-1'].x=-10;fixtureBuiltWorld.objects['carving-1'].z=8;fixtureBuiltWorld.objects['carving-1'].revision++;\nfixtureBuiltWorld.trees['tree-0'].stage='felled';fixtureBuiltWorld.trees['tree-0'].stock=0;\nawait refresh();assert.equal(fits(-8.3,13),true);assert.equal(worldMeshes.get('carving-1').group.position.x,-10);\nassert.equal(treeMeshes.get('tree-0').group.visible,false);assert.equal(treeMeshes.get('tree-0').log.visible,false);assert.ok(treeMeshes.get('tree-0').stump);\nconsole.log('PASS: saved geometry replaces library shell; wall removal updates collision; moved carving and felled-tree stump render from authoritative state.');\n";
tail+="\ntestState.ecology_view={trees:{'tree-1':{species:'oak',cover:0,colour:'#9a7a3a'},'tree-2':{species:'oak',cover:.8,colour:'#9a7a3a'}},plants:[{id:'bramble-1',species:'bramble',x:2,z:-22}]};await refresh();\nassert.equal(plantGroup.children.length,1);assert.equal(treeMeshes.get('tree-1').crowns[0].material.color.getHexString(),'6d6150');assert.equal(treeMeshes.get('tree-2').crowns[0].material.color.getHexString(),'9a7a3a');\n";
tail+=`\n
testState.built_world=fixtureInteractedWorld;testState.twin={};testState.decisions=30;
testState.action='interact';testState.location='workbench';
testState.pending={decision:{action:'interact',verb:'sit',object_id:'library_chair'},posture:{verb:'sit',x:-9.1,z:9.3,height:.49},remaining:900,duration:900};
await refresh();advance(.5);
assert.equal(furnitureReplaced,true);assert.equal(chair.parent,null);assert.ok(legacyBed.every(m=>m.parent===null));
assert.ok(worldMeshes.has('workbench')&&worldMeshes.has('library_chair'));
assert.equal(anim.pose,'objectSit');assert.equal(anim.seated,1);assert.ok(Math.abs(crow.position.y+.28)<.01);
const worked=Object.values(fixtureInteractedWorld.objects).find(o=>o.kind==='workpiece');
const rendered=worldMeshes.get(worked.id).group.children[0];
assert.ok(Math.abs(rendered.position.y-worked.parts[0].height/2-1.315)<.001);
fixtureInteractedWorld.objects.library_chair.x=-5;fixtureInteractedWorld.objects.library_chair.z=4;
testState.decisions=31;testState.action='read';testState.location='library';
testState.pending={decision:{action:'read',reading_spot:'chair'},remaining:900,duration:900};
await refresh();advance(100);
assert.equal(LIB.seat.x,-5);assert.equal(LIB.seat.z,4);assert.equal(anim.pose,'reading');
assert.ok(crow.position.distanceTo(new T.Vector3(-5,-.28,4))<.05);
testState.decisions=32;testState.action='interact';testState.location='cabin';
testState.pending={decision:{action:'interact',verb:'lie',object_id:'cabin_bed'},posture:{verb:'lie',x:-11.5,z:-10.3,height:.55},remaining:900,duration:900};
await refresh();advance(.5);assert.equal(anim.pose,'objectLie');assert.ok(Math.abs(crow.rotation.x+Math.PI/2)<.01);
testState.decisions=33;testState.action='inspect';testState.pending={decision:{action:'inspect',object_id:'workbench'},remaining:60,duration:60};
await refresh();advance(.5);assert.equal(crow.rotation.x,0);
console.log('PASS: ledger furnishings replace static props once; supported object heights; explicit sitting/lying; moved chair reading; clean posture exit.');
`;
tail+=`
// v0.33.2: he goes by the lanes, never via the middle of the green, and a reload into reading places him once.
delete testState.twin;
const seg=(p,a,b)=>{const dx=b.x-a.x,dz=b.z-a.z,l=dx*dx+dz*dz||1e-9,t=Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.z-a.z)*dz)/l));return Math.hypot(p.x-a.x-t*dx,p.z-a.z-t*dz);};
const trips=[['cabin','rest'],['library','read'],['cafe','browse'],['shop','trade'],['range','practise'],['garden','garden'],['library','read'],['woods','explore'],['cabin','rest']];
let n=40;
for(const [loc,act] of trips){
 testState.decisions=++n;testState.action=act;testState.location=loc;testState.pending={decision:{action:act,reading_spot:'standing'},remaining:900,duration:900};
 await refresh();
 const plan=[crow.position.clone(),...anim.steps.filter(x=>x.kind==='walk').map(x=>x.point.clone())];
 assert.ok(!plan.slice(1).some(p=>Math.hypot(p.x,p.z)<.01),'no waypoint at the middle of the green: '+loc);
 let pathMin=Infinity;for(let i=1;i<plan.length;i++)pathMin=Math.min(pathMin,seg(new T.Vector3(0,0,0),plan[i-1],plan[i]));
 let seen=Infinity;for(let i=0;i<1600;i++){testTime+=50;frame(testTime);seen=Math.min(seen,Math.hypot(crow.position.x,crow.position.z));}
 assert.ok(seen>=.5||pathMin<1,'he passed through the middle of the green going to '+loc+' ('+seen.toFixed(2)+')');
}
testState.decisions=++n;testState.action='read';testState.location='library';testState.pending={decision:{action:'read',reading_spot:'standing'},remaining:900,duration:900};
initialized=false;anim.key=null;await refresh();
assert.equal(anim.snap,false,'the reload flag is cleared after reading');
assert.ok(Math.hypot(crow.position.x-LIB.aisle.x,crow.position.z-LIB.aisle.z)<.05,'a reload into reading places him in the aisle');
console.log('PASS v0.33.2: walks go by the lanes, never via the middle of the green; a reload into reading places him once.');
`;
await import('data:text/javascript;base64,'+Buffer.from(prefix+source+tail).toString('base64'));
