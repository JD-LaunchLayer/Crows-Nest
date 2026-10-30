import * as T from '/vendor/three.module.js';
import {installTouchControls} from '/mobile_controls.js';
import {createSky} from '/sky.js';
import {createJournal} from '/journal.js';
import {createLifeView} from '/life_view.js';
import {createDiary} from '/diary_view.js';
const $=id=>document.getElementById(id),txt=(id,v)=>$(id).textContent=v;
const clientVersion=document.querySelector?.('meta[name="crow-version"]')?.content||null;
let updateRequested=false;
// A LAN access token is kept in this tab, removed from the visible URL, and sent in headers.
const tokenParams=new URLSearchParams(globalThis.location?.hash?.slice(1)||'');
let accessToken=tokenParams.get('token')||globalThis.sessionStorage?.getItem('crow-access-token')||'';
if(tokenParams.has('token')){globalThis.sessionStorage?.setItem('crow-access-token',accessToken);globalThis.history?.replaceState(null,'',globalThis.location.pathname);}
async function apiFetch(url,options={}){return fetch(url,{...options,headers:{...(options.headers||{}),...(accessToken?{'Authorization':'Bearer '+accessToken}:{})}})}
const journal=createJournal({document,apiFetch});
const lifeView=createLifeView({document});const diary=createDiary({document});
const holder=$('view'),scene=new T.Scene();scene.background=new T.Color('#b7c6b0');scene.fog=new T.Fog('#b7c6b0',24,65);
let renderer;try{renderer=new T.WebGLRenderer({antialias:true,powerPreference:'low-power'});}catch(e){txt('loading','3D graphics could not start. Check Firefox hardware acceleration. '+e.message);throw e;}
renderer.setPixelRatio(Math.min(devicePixelRatio,globalThis.matchMedia?.('(pointer:coarse)').matches?1:1.5));renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;holder.prepend(renderer.domElement);
const camera=new T.PerspectiveCamera(65,1,.1,100);camera.position.set(0,1.7,17);camera.rotation.order='YXZ';let yaw=0,pitch=0,s=null,last=performance.now(),initialized=false;
const skyLight=new T.HemisphereLight(0xe4eedb,0x45503c,2);scene.add(skyLight);const sun=new T.DirectionalLight(0xffe4b5,2.4);sun.position.set(-12,25,8);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);Object.assign(sun.shadow.camera,{left:-25,right:25,top:25,bottom:-25,near:1,far:70});scene.add(sun);
const sky=createSky({T,scene,camera,sun,skyLight});
const mats={};function mat(c){return mats[c]??=new T.MeshStandardMaterial({color:c,roughness:1,flatShading:true})}
function mesh(geo,c,x,y,z,parent=scene){const m=new T.Mesh(geo,mat(c));m.position.set(x,y,z);m.castShadow=true;m.receiveShadow=true;parent.add(m);return m}
function box(w,h,d,c,x,y,z,p=scene){return mesh(new T.BoxGeometry(w,h,d),c,x,y,z,p)}
const obstacles=[];function block(x,z,w,d){obstacles.push({x,z,w:w/2+.3,d:d/2+.3})}
const floor=mesh(new T.PlaneGeometry(110,110,1,1),'#74815a',0,-.03,0);floor.rotation.x=-Math.PI/2;floor.castShadow=false;
const stations={cabin:new T.Vector3(-10,0,-6),range:new T.Vector3(10,0,-7),woods:new T.Vector3(13,0,10),workbench:new T.Vector3(0,0,10),library:new T.Vector3(-11,0,5),cafe:new T.Vector3(9,0,-14.2),shop:new T.Vector3(-3,0,-14.2)};
for(const p of Object.values(stations)){const mid=p.clone().multiplyScalar(.5),path=box(1.5,.035,p.length(),'#a39d77',mid.x,0,mid.z);path.rotation.y=Math.atan2(p.x,p.z);path.castShadow=false;}
// Open-front cabin: floor and three walls, so it is possible to look inside.
box(6,.15,5,'#806c4b',-10,.05,-10);box(6,3,.2,'#76644b',-10,1.5,-12.5);box(.2,3,5,'#806c4b',-13,1.5,-10);box(.2,3,5,'#806c4b',-7,1.5,-10);
block(-10,-12.5,6,.2);block(-13,-10,.2,5);block(-7,-10,.2,5);
const roof=mesh(new T.ConeGeometry(4.5,2.5,4),'#4e5540',-10,4,-10);roof.rotation.y=Math.PI/4;
box(1.5,.4,2.6,'#a3a782',-11.5,.35,-10.3);box(1.3,.18,.55,'#d5ccb1',-11.5,.65,-11.1);box(.7,1,.6,'#8c704e',-8.2,.5,-11.5);
// Range target with concentric faces pointing into the clearing.
box(.18,2.5,.18,'#6e593e',10,1.25,-10);for(const [r,col,z] of [[1,'#dfd6b4',-9.9],[.7,'#877249',-9.86],[.45,'#d6c99e',-9.82],[.17,'#935d3e',-9.78]]){mesh(new T.CylinderGeometry(r,r,.07,16),'#'+col.replace('#',''),10,2,z).rotation.x=Math.PI/2;}block(10,-10,2,.5);
// Workbench, reading cabin and a small quiet pond.
box(3,.23,1.4,'#a58c5c',0,1.2,12);for(const x of [-1.2,1.2])for(const z of [11.5,12.5])box(.17,1.2,.17,'#645739',x,.6,z);block(0,12,3,1.4);
// Reading cabin: legacy shell is replaced by persistent world geometry on sync.
const shellStart=scene.children.length,blockStart=obstacles.length;
// Reading cabin: open doorway, low-poly timber shell and shelves.
const LIB={door:new T.Vector3(-11,0,5),aisle:new T.Vector3(-11,0,9.4),shelf:new T.Vector3(-11.8,0,11.4),approach:new T.Vector3(-9.1,0,8.5),seat:new T.Vector3(-9.1,0,9.3),floor:new T.Vector3(-12.0,0,9.1)};
box(7,.12,6,'#8a7756',-11,.01,10);
box(7,3,.18,'#76654d',-11,1.5,13);block(-11,13,7,.18);
box(.18,3,6,'#817057',-14.5,1.5,10);block(-14.5,10,.18,6);
box(.18,3,6,'#817057',-7.5,1.5,10);block(-7.5,10,.18,6);
for(const x of [-13.5,-8.5]){box(2,3,.18,'#89775b',x,1.5,7);block(x,7,2,.18)}
box(3, .5,.2,'#89775b',-11,2.75,7);
// Two pitched roof panels leave the front doorway unobstructed.
for(const side of [-1,1]){const panel=box(4.05,.18,6.8,'#4e5946',-11+side*1.75,3.5,10);panel.rotation.z=-side*.37;}
const legacyShell=scene.children.slice(shellStart);const legacyShellBlocks=obstacles.slice(blockStart);let shellReplaced=false;
let shelfBook=null;
for(const x of [-13.7,-11.8]){
 box(1.65,2.25,.42,'#574a35',x,1.15,12.6);
 for(const y of [.22,.9,1.58,2.23])box(1.72,.07,.58,'#ae8b57',x,y,12.46);
 for(let row=0;row<3;row++)for(let i=0;i<8;i++){
 const book=box(.13,.41+(i%3)*.045,.34,['#8b5546','#667e6d','#b3a16a','#728395'][i%4],x-.65+i*.18,.48+row*.67,12.31);
 if(i===7)book.rotation.z=.12;
 if(x===-11.8&&row===1&&i===4)shelfBook=book;
 }
 block(x,12.55,1.7,.7);
}
// A few little volumes on a second, shorter shelf beside the door.
box(1.1,1.2,.45,'#6d5a3e',-13.5,.6,8.5);block(-13.5,8.5,1.1,.45);
for(let i=0;i<5;i++)box(.14,.45,.33,['#ae8b57','#6e8273'][i%2],-13.87+i*.18,.9,8.55);
// Reading chair, cushion, back and armrests. It faces the clearing (-Z).
const chair=new T.Group();chair.position.copy(LIB.seat);scene.add(chair);
box(.95,.12,.95,'#795d3f',0,.43,0,chair);box(.78,.10,.75,'#8f9a71',0,.53,-.04,chair);
box(.95,.95,.12,'#795d3f',0,.95,.45,chair);box(.73,.68,.08,'#8f9a71',0,1.03,.36,chair);
for(const x of [-.39,.39])for(const z of [-.37,.37])box(.10,.43,.10,'#795d3f',x,.2,z,chair);
for(const x of [-.49,.49]){box(.10,.10,.85,'#9f8055',x,.85,0,chair);box(.08,.38,.08,'#795d3f',x,.65,-.3,chair)}
block(LIB.seat.x,LIB.seat.z,1,1);
// Small side table and warm reading lamp. Only one local light; no extra shadow map.
box(.9,.1,.9,'#94784e',-8.15,.78,9.3);box(.14,.75,.14,'#715a3a',-8.15,.38,9.3);block(-8.15,9.3,.9,.9);
mesh(new T.CylinderGeometry(.18,.22,.06,8),'#6e6043',-8.15,.86,9.3);
box(.045,.55,.045,'#8e805b',-8.15,1.14,9.3);
const lampShade=mesh(new T.ConeGeometry(.32,.42,8,1,true),'#e1c188',-8.15,1.5,9.3);
lampShade.material=new T.MeshStandardMaterial({color:'#e1c188',emissive:'#d39a44',emissiveIntensity:.4,side:T.DoubleSide});
const lamp=new T.PointLight('#ffce84',12,9,2);lamp.position.set(-8.15,1.36,9.3);scene.add(lamp);
mesh(new T.SphereGeometry(.075,8,6),'#fff0c2',-8.15,1.38,9.3);
const rug=box(2.2,.015,2.2,'#766f52',-9.1,.09,9.2);rug.castShadow=false;
const pond=mesh(new T.CylinderGeometry(3,3,.06,13),'#789a91',-18,.01,3);pond.castShadow=false;
const treeMeshes=new Map();let treeNumber=0;
function tree(x,z,h=5){
 const id='tree-'+treeNumber++,group=new T.Group();group.position.set(x,0,z);scene.add(group);
 box(.35,h*.5,.35,'#655b40',0,h*.25,0,group);const crowns=[mesh(new T.ConeGeometry(h*.32,h*.75,5),'#455b3f',0,h*.7,0,group),mesh(new T.ConeGeometry(h*.26,h*.65,5),'#536a47',0,h*.99,0,group)];
 block(x,z,.5,.5);treeMeshes.set(id,{group,crowns,stump:null,log:null,x,z,h});
}
// Seasonal appearance comes from the server's ecology view (real UK date); bare trees show thin branch crowns.
const plantGroup=new T.Group();scene.add(plantGroup);let ecologyKey='';
const PLANT_LOOK={bramble:['#5a4a3e',1.6,.9],bracken:['#8a6a3a',1.3,.8],bluebell:['#4b6a3c',1.4,.12],'wood anemone':['#5e7a48',1,.1],'male fern':['#4a6a3a',1.1,.8],'fly agaric':['#b0302a',.25,.18],'holly seedlings':['#2f4a2c',.5,.3],nettles:['#4d6a3a',1.5,.9],grass:['#6f8a4f',3,.12]};
function syncEcology(view){
 if(!view)return;const key=JSON.stringify(view);if(key===ecologyKey)return;ecologyKey=key;
 for(const [id,t]of Object.entries(view.trees||{})){const visual=treeMeshes.get(id);if(!visual)continue;
  const bare=t.cover<.05;visual.crowns.forEach((c,i)=>{c.material=mat(bare?'#6d6150':t.colour);c.scale.setScalar(bare?.45:.55+.45*t.cover)});}
 while(plantGroup.children.length){const c=plantGroup.children[0];plantGroup.remove(c);c.geometry.dispose()}
 for(const p of view.plants||[]){const look=PLANT_LOOK[p.species];if(!look)continue;const [c,w,h]=look;const m=mesh(new T.DodecahedronGeometry(.5,0),c,p.x,h/2,p.z,plantGroup);m.scale.set(w,h,w);m.castShadow=false;}
}
function syncTrees(world){
 for(const [id,t]of Object.entries(world.trees||{})){
  const visual=treeMeshes.get(id);if(!visual)continue;
  visual.group.visible=t.stage==='standing';
  if(t.stage==='felled'&&!visual.stump){visual.stump=mesh(new T.CylinderGeometry(.2,.25,.4,6),'#8a7350',visual.x,.2,visual.z);visual.log=mesh(new T.CylinderGeometry(.16,.20,visual.h*.65,6),'#856a43',visual.x+.7,.22,visual.z);visual.log.rotation.z=Math.PI/2;}
  if(visual.log){visual.log.visible=t.stock>0;visual.log.scale.y=Math.max(.02,t.stock/t.timber_kg)}
 }
}

for(let i=0;i<65;i++){const a=i*2.39996,r=23+(i%7)*1.1;tree(Math.cos(a)*r,Math.sin(a)*r,4+(i%5)*.65)}
for(const [x,z,h]of [[17,10,5],[15,14,6],[20,12,5],[18,6,4],[-18,-9,5],[-20,-15,6]])tree(x,z,h);
// Small details without textures or outside image services.
for(let i=0;i<65;i++){let a=i*2.4,r=6+(i%11)*1.4;const x=Math.cos(a)*r,z=Math.sin(a)*r;if(Math.abs(x)<2||Math.abs(z)<2)continue;const stone=mesh(new T.DodecahedronGeometry(.13+(i%3)*.06,0),i%4?'#828771':'#b4ac7e',x,.13,z);stone.scale.y=.6;}
function sign(text,x,z){const c=document.createElement('canvas');c.width=512;c.height=96;const q=c.getContext('2d');q.fillStyle='#283b2b';q.fillRect(0,0,512,96);q.fillStyle='#eee5c7';q.font='30px Georgia';q.textAlign='center';q.fillText(text,256,60);const texture=new T.CanvasTexture(c);const m=new T.Sprite(new T.SpriteMaterial({map:texture,depthTest:true}));m.position.set(x,2.9,z);m.scale.set(4,.75,1);scene.add(m)}
sign('THE CABIN',-10,-6);sign('ARCHERY RANGE',10,-7);sign('WORKBENCH',0,11.5);sign('READING CABIN',-11,6.8);sign('WOODLAND',16,12);sign('INTERNET CAFÉ',9,-14);sign('TRADING POST',-3,-14);
// Jointed placeholder elf: hips, knees, shoulders and elbows support sitting and reaching.
const crow=new T.Group();scene.add(crow);
// An original low-poly elf: slate cloak, teal tunic, rust sash, silver hair tied back.
const SKIN='#e2c6a6',TUNIC='#3f6058',CLOAK='#3b4352',SASH='#9c4f2c',TROUSERS='#47443a',BOOTS='#2e2924',HAIR='#d8d3c6';
function cyl(rt,rb,h,c,x,y,z,p,seg=7){return mesh(new T.CylinderGeometry(rt,rb,h,seg),c,x,y,z,p)}
const torso=cyl(.27,.21,.62,TUNIC,0,1.12,0,crow);
cyl(.215,.3,.26,TUNIC,0,.74,0,crow);                       // tunic skirt
mesh(new T.TorusGeometry(.225,.035,4,10),SASH,0,.86,0,crow).rotation.x=Math.PI/2;
box(.1,.2,.03,SASH,.13,.72,.2,crow).rotation.z=-.2;          // sash tail
cyl(.2,.3,.95,CLOAK,0,.95,-.12,crow,6).scale.z=.35;                        // cloak hanging behind
mesh(new T.TorusGeometry(.2,.06,4,10,Math.PI*1.4),CLOAK,0,1.43,-.02,crow).rotation.x=Math.PI/2; // folded hood at the collar
cyl(.07,.08,.16,SKIN,0,1.5,0,crow);                          // neck
const headPivot=new T.Group();headPivot.position.y=1.66;crow.add(headPivot);
mesh(new T.IcosahedronGeometry(.2,1),SKIN,0,.04,0,headPivot).scale.set(.92,1.12,1);
const hair=mesh(new T.SphereGeometry(.215,8,5,0,Math.PI*2,0,Math.PI*.55),HAIR,0,.07,-.025,headPivot);hair.rotation.x=-.25;
mesh(new T.ConeGeometry(.06,.36,5),HAIR,0,-.12,-.2,headPivot).rotation.x=Math.PI*.92;   // tied-back tail
for(const x of [-.2,.2]){const ear=mesh(new T.ConeGeometry(.045,.27,4),SKIN,x,.06,-.01,headPivot);ear.rotation.z=x>0?-1.05:1.05;ear.rotation.x=-.35;}
for(const x of [-.075,.075]){box(.05,.03,.02,'#f4efe2',x,.07,.185,headPivot);box(.022,.026,.02,'#b0782e',x,.07,.193,headPivot);box(.065,.014,.02,'#9b958a',x,.115,.188,headPivot).rotation.z=x>0?-.15:.15;}
mesh(new T.ConeGeometry(.025,.07,4),SKIN,0,.02,.205,headPivot).rotation.x=Math.PI/2;      // nose
box(.07,.012,.01,'#a4705e',0,-.05,.19,headPivot);                                         // mouth
const legs=[],knees=[],arms=[],elbows=[];
for(const x of [-.12,.12]){
 const hip=new T.Group();hip.position.set(x,.76,0);crow.add(hip);legs.push(hip);
 cyl(.085,.075,.36,TROUSERS,0,-.18,0,hip);
 const knee=new T.Group();knee.position.y=-.36;hip.add(knee);knees.push(knee);
 cyl(.075,.07,.3,BOOTS,0,-.15,0,knee);box(.15,.1,.27,BOOTS,0,-.33,.05,knee);
 const shoulder=new T.Group();shoulder.position.set(Math.sign(x)*.33,1.36,0);crow.add(shoulder);arms.push(shoulder);
 cyl(.07,.06,.3,TUNIC,0,-.15,0,shoulder);
 const elbow=new T.Group();elbow.position.y=-.3;shoulder.add(elbow);elbows.push(elbow);
 cyl(.06,.055,.26,'#5b4635',0,-.13,0,elbow);mesh(new T.IcosahedronGeometry(.055,0),SKIN,0,-.29,0,elbow);
}
const heldAxe=new T.Group();box(.055,.55,.055,'#937449',0,0,0,heldAxe);box(.30,.14,.07,'#a8afaa',.10,.21,0,heldAxe);elbows[1].add(heldAxe);heldAxe.position.set(0,-.29,.08);heldAxe.visible=false;
const bow=mesh(new T.TorusGeometry(.47,.025,4,12,Math.PI),'#b09a68',.48,1.14,-.2,crow);bow.rotation.z=-Math.PI/2;
const heldBook=new T.Group();heldBook.position.set(0,1.05,.44);heldBook.rotation.x=.28;crow.add(heldBook);heldBook.visible=false;
for(const x of [-.17,.17]){box(.34,.025,.43,'#79523c',x,0,0,heldBook);box(.30,.045,.39,'#eee4c7',x,.033,0,heldBook)}
const pagePivot=new T.Group();pagePivot.position.y=.065;heldBook.add(pagePivot);box(.31,.004,.38,'#faf0d4',.155,0,0,pagePivot);
const crowTag=new T.Sprite(new T.SpriteMaterial({map:(()=>{const c=document.createElement('canvas');c.width=256;c.height=64;const ctx=c.getContext('2d');ctx.font='36px Georgia';ctx.fillStyle='#fff5d7';ctx.textAlign='center';ctx.fillText('Crow',128,45);return new T.CanvasTexture(c)})(),depthTest:true}));crowTag.position.y=2.3;crowTag.scale.set(1.8,.45,1);crow.add(crowTag);
// Edda Thorne, keeper of the trading post, behind her counter. Shown once the post exists in his world.
const edda=new T.Group();edda.position.set(-3,0,-18.25);edda.visible=false;scene.add(edda);
mesh(new T.CylinderGeometry(.22,.3,1.0,7),'#5d4a6b',0,.55,0,edda);mesh(new T.CylinderGeometry(.24,.2,.5,7),'#7a6a55',0,1.3,0,edda);
mesh(new T.IcosahedronGeometry(.18,1),'#e0bea0',0,1.72,0,edda);mesh(new T.SphereGeometry(.19,8,5,0,Math.PI*2,0,Math.PI*.5),'#9a9a95',0,1.76,-.02,edda);
mesh(new T.SphereGeometry(.1,6,5),'#9a9a95',0,1.78,-.17,edda);
for(const x of [-.06,.06])box(.03,.03,.02,'#3b2f2a',x,1.75,.17,edda);
for(const x of [-.3,.3])mesh(new T.CylinderGeometry(.06,.05,.55,6),'#7a6a55',x,1.22,0,edda);
const eddaTag=new T.Sprite(new T.SpriteMaterial({map:(()=>{const c=document.createElement('canvas');c.width=256;c.height=64;const ctx=c.getContext('2d');ctx.font='32px Georgia';ctx.fillStyle='#fff5d7';ctx.textAlign='center';ctx.fillText('Edda',128,45);return new T.CanvasTexture(c)})(),depthTest:true}));eddaTag.position.y=2.2;eddaTag.scale.set(1.2,.3,1);edda.add(eddaTag);
// Motions are visual only. AI choices, real activity timers and saved outcomes are unchanged.
const anim={steps:[],pose:'idle',elapsed:0,book:false,seated:0,floor:0,desired:null,key:null,returning:false,activeAction:'rest'};
crow.position.copy(stations.cabin);
function walk(point,face=null){return {kind:'walk',point:point.clone(),face}}
function wait(pose,duration,done=null){return {kind:'wait',pose,duration,done,elapsed:0}}
function readingPlan(){
 anim.activeAction='read';
 const spot=anim.desired?.spot||'standing';
 const after=spot==='chair'?[walk(LIB.approach,Math.PI),wait('sit',1.2),wait('reading',Infinity)]:
 spot==='floor'?[walk(LIB.floor,Math.PI),wait('sitfloor',1.2),wait('readingFloor',Infinity)]:
 [walk(LIB.aisle,Math.PI),wait('readingStanding',Infinity)];
 anim.steps=[walk(new T.Vector3(0,0,0)),walk(LIB.door),walk(LIB.aisle),walk(LIB.shelf,0),
 wait('take',1.4,()=>{anim.book=true}),walk(LIB.aisle),...after];
}
// Where an activity actually happens: the chosen area, tree, plant or object, when the decision names one.
const AREA_SPOTS={grove:[15.5,8.5],spring_side:[-15.6,-1.5],clearing:[1.5,2.5]};
// Inside the buildings: at the trading post counter, or on the café terminal stool.
const INSIDE={trade:[-3,-16.4],talk:[-3,-16.4],browse:[10.3,-17.6]};
function targetFor(d){
 if(!d.pending)return null;
 if(INSIDE[d.action])return new T.Vector3(INSIDE[d.action][0],0,INSIDE[d.action][1]);
 if(d.action==='observe'){
  if(AREA_SPOTS[d.area])return new T.Vector3(...[AREA_SPOTS[d.area][0],0,AREA_SPOTS[d.area][1]]);
  const a=Math.atan2(crow.position.z,crow.position.x)||0;return new T.Vector3(Math.cos(a)*20,0,Math.sin(a)*20);
 }
 if(['inspect','gather'].includes(d.action)&&d.objectId){
  const o=s.built_world?.objects?.[d.objectId]||s.built_world?.trees?.[d.objectId]||(s.ecology?.plants||[]).find(p=>p.id===d.objectId);
  if(o){const r=Math.hypot(o.x,o.z)||1;return new T.Vector3(o.x-o.x/r*1.1,0,o.z-o.z/r*1.1)}
 }
 return null;
}
function beginDesired(){
 anim.returning=false;anim.seated=0;anim.floor=0;
 const d=anim.desired;if(!d)return;
 if(d.pending&&d.action==='read'){readingPlan();return}
 anim.activeAction=d.pending?d.action:'idle';
 let place=stations[d.location]||stations.cabin;
 if(d.pending&&['eat','drink'].includes(d.action)){const target=s.built_world?.objects[d.objectId||(d.action==='eat'?'food_store':'spring')];if(target)place=new T.Vector3(target.x,0,target.z-1);}
 if(d.pending&&d.action==='fell_tree'){const tree=s.built_world?.trees[d.objectId];if(tree)place=new T.Vector3(tree.x-.9,0,tree.z);}
 place=targetFor(d)||place;
 // The twin's clock outruns any walk, so its view shows him where he is rather than on the way there.
 if(d.twin){crow.position.copy(place);anim.steps=[wait(d.pending?d.action:'idle',Infinity)];return}
 anim.steps=[walk(new T.Vector3(0,0,0)),walk(place),wait(d.pending?d.action:'idle',Infinity)];
}
function setActivity(data){
 const key=`${data.decisions}:${Boolean(data.pending)}`;if(key===anim.key)return;
 anim.key=key;anim.desired={action:data.action,location:data.location,pending:Boolean(data.pending),spot:data.pending?.decision?.reading_spot||'standing',objectId:data.pending?.decision?.object_id||'',area:data.pending?.decision?.observe_area||'',twin:Boolean(data.twin)};
 if(!initialized){initialized=true;crow.position.copy(stations[data.location]||stations.cabin);}
 if(anim.returning)return;
 if(data.twin){anim.book=false;anim.seated=0;anim.floor=0;anim.activeAction='idle';beginDesired();return}
 if(anim.book){
 anim.returning=true;
 const rise=anim.seated>0?[wait(anim.floor>0?'standfloor':'stand',1.2)]:[];
 anim.steps=[...rise,walk(LIB.aisle),walk(LIB.shelf,0),wait('putback',1.4,()=>{anim.book=false}),walk(LIB.aisle),walk(LIB.door),wait('idle',.1,beginDesired)];
 }else if(anim.activeAction==='read'){
 anim.returning=true;anim.steps=[walk(LIB.aisle),walk(LIB.door),wait('idle',.1,beginDesired)];
 }else beginDesired();
}
const made=new T.Group();scene.add(made);let creationKey='';
function creations(items){const key=JSON.stringify(items);if(key===creationKey)return;creationKey=key;while(made.children.length){const c=made.children[0];made.remove(c);c.geometry.dispose()}for(const [i,obj]of items.slice(-20).entries()){const x=3+(i%5)*.9,z=9+Math.floor(i/5)*1;let geo;switch(obj.shape){case'orb':geo=new T.IcosahedronGeometry(.3,0);break;case'spire':geo=new T.ConeGeometry(.24,.85,5);break;case'bowl':geo=new T.CylinderGeometry(.35,.15,.25,8);break;default:geo=new T.BoxGeometry(.3,.65,.3)}mesh(geo,'#bb9564',x,.45,z,made);}}
const worldMeshes=new Map();let worldObstacleRecords=[];
function syncBuiltWorld(world){
 if(!world)return;syncTrees(world);
 if(!shellReplaced){for(const m of legacyShell){scene.remove(m);m.geometry?.dispose()}for(const b of legacyShellBlocks){const i=obstacles.indexOf(b);if(i>=0)obstacles.splice(i,1)}shellReplaced=true;}
 for(const c of worldObstacleRecords){const i=obstacles.indexOf(c);if(i>=0)obstacles.splice(i,1)}worldObstacleRecords=[];
 for(const [id,record]of worldMeshes)if(!world.objects[id]){scene.remove(record.group);record.group.traverse(m=>m.geometry?.dispose());worldMeshes.delete(id)}
 for(const [id,obj]of Object.entries(world.objects)){
  const key=JSON.stringify(obj);let record=worldMeshes.get(id);
  if(!record||record.key!==key){
   if(record){scene.remove(record.group);record.group.traverse(m=>m.geometry?.dispose())}
   const group=new T.Group();group.position.set(obj.x,0,obj.z);scene.add(group);
   for(const p of obj.parts){let geo;
    if(p.shape==='sphere')geo=new T.SphereGeometry(.5,8,6);
    else if(p.shape==='cone')geo=new T.ConeGeometry(.5,1,6);
    else if(p.shape==='cylinder')geo=new T.CylinderGeometry(.5,.5,1,8);
    else geo=new T.BoxGeometry(1,1,1);
    const m=mesh(geo,p.color,p.x,p.y,p.z,group);m.scale.set(p.width,p.height,p.depth);m.rotation.z=p.rotation_z||0;
   }
   record={key,group};worldMeshes.set(id,record);
  }
  for(const p of obj.parts)if(p.y-p.height/2<1.8&&p.y+p.height/2>.2){const c={x:obj.x+p.x,z:obj.z+p.z,w:p.width/2+.3,d:p.depth/2+.3};obstacles.push(c);worldObstacleRecords.push(c)}
 }
}
function fits(x,z){return Math.abs(x)<31&&Math.abs(z)<31&&!obstacles.some(o=>Math.abs(x-o.x)<o.w&&Math.abs(z-o.z)<o.d)}
const keys=new Set();addEventListener('keydown',e=>{if(['KeyW','KeyA','KeyS','KeyD','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home'].includes(e.code)){e.preventDefault();keys.add(e.code)}if(e.code==='Home'){camera.position.set(0,1.7,17);yaw=0;pitch=0}});addEventListener('keyup',e=>keys.delete(e.code));addEventListener('blur',()=>keys.clear());
renderer.domElement.onclick=()=>{renderer.domElement.requestPointerLock?.()};document.addEventListener('mousemove',e=>{if(document.pointerLockElement!==renderer.domElement)return;yaw-=e.movementX*.002;pitch=T.MathUtils.clamp(pitch-e.movementY*.002,-1.1,1.1)});document.addEventListener('pointerlockerror',()=>txt('help','Mouse capture unavailable. Use WASD to walk and arrow keys to turn.'));
$('find').onclick=()=>{const p=crow.position;if(p.x<-7&&p.x>-15&&p.z>6&&p.z<13){camera.position.set(-11,1.7,8);yaw=Math.atan2(camera.position.x-p.x,camera.position.z-p.z);pitch=-.10;return;}const candidates=[[p.x,p.z+4],[p.x+4,p.z],[p.x-4,p.z],[p.x,p.z-4]];const at=candidates.find(([x,z])=>fits(x,z));if(at){camera.position.set(at[0],1.7,at[1]);yaw=Math.atan2(at[0]-p.x,at[1]-p.z);pitch=-.06}};
$('toggle').onclick=async()=>{const b=$('toggle');b.disabled=true;try{const r=await apiFetch('/api/toggle',{method:'POST',headers:{'X-Crow':'local'}});if(!r.ok)throw Error('Could not change pause state');await refresh()}catch(e){txt('error',e.message)}finally{b.disabled=false}};
const touchInput=typeof $('touchPad').addEventListener==='function'?installTouchControls({canvas:renderer.domElement,pad:$('touchPad'),knob:$('stickKnob'),onLook:(dx,dy)=>{yaw-=dx;pitch=T.MathUtils.clamp(pitch-dy,-1.1,1.1)}}):{forward:0,right:0};
$('mobileFind').onclick=()=>$('find').onclick();
// Tab opens his journal; Escape closes it. The side panel keeps what is happening now.
addEventListener('keydown',e=>{if(e.code==='Tab'){e.preventDefault();diary.toggle()}else if(e.code==='Escape')diary.open(false)});
if($('diaryClose'))$('diaryClose').onclick=()=>diary.open(false);if($('mobileDiary'))$('mobileDiary').onclick=()=>diary.toggle();
$('mobileMenu').onclick=()=>{const opened=document.body.classList.toggle('panel-open');$('mobileMenu').textContent=opened?'Close':'Journal';$('mobileMenu').setAttribute('aria-expanded',String(opened));};
if(globalThis.matchMedia?.('(pointer:coarse)').matches)txt('help','Left thumb: walk · Drag the world: look around');
if($('updateCrow'))$('updateCrow').onclick=async()=>{
 const button=$('updateCrow');button.disabled=true;updateRequested=true;
 txt('updateStatus','Requesting backup and update…');
 try{
  const response=await apiFetch('/api/update',{method:'POST',headers:{'X-Crow':'local'}});
  if(!response.ok)throw Error(await response.text());
  txt('updateStatus','Crow is saving and backing up. This page will reconnect after the restart.');
 }catch(error){updateRequested=false;button.disabled=false;txt('updateStatus',error.message)}
};
function entry(parent,title,detail){const d=document.createElement('div');d.className='entry';d.textContent=title;if(detail){const em=document.createElement('em');em.textContent=detail;d.append(em)}parent.append(d)}
async function refresh(){try{const r=await apiFetch('/api/state');if(!r.ok)throw Error(r.status===401?'Open the full phone link printed by Crow’s terminal to connect.':'Server unavailable');s=await r.json();
if(clientVersion&&s.runtime.version&&clientVersion!==s.runtime.version){globalThis.location?.reload?.();return;}
const maintenance=s.runtime.maintenance||{status:'idle'};if(updateRequested&&maintenance.status==='complete'){globalThis.location?.reload?.();return;}const updating=['checking','backing_up','pulling','restarting'].includes(maintenance.status);
if($('updateCrow')){ $('updateCrow').disabled=updating||!s.maintenance_enabled; $('updateCrow').textContent=updating?'Updating…':'Back up and update';txt('updateStatus',maintenance.message||(s.maintenance_enabled?'Ready. Your private life data stays on the PC.':'Start Crow with --lan from its Git checkout to enable authenticated updates.'));}
if(['complete','up_to_date','failed','interrupted'].includes(maintenance.status))updateRequested=false;
txt('toggle',s.paused?'Begin life':'Pause');txt('clock',`${s.clock.date} · ${s.clock.time} · ${s.twin?'twin clock':s.crow_clock?`Crow's time${s.crow_clock.scale>1?' ('+s.crow_clock.scale+'× speed)':''}`:'UK time'}`);txt('status',s.runtime.status+(s.last_seconds!==null?' · Last choice '+s.last_seconds+'s':''));txt('error',s.last_error);$('toggle').disabled=updating;txt('activity',({eat:'Eating',drink:'Drinking',rest:'Resting',practise:'Practising archery',explore:'Exploring',craft:'Making a carving',read:'Reading Wikipedia',sleep:'Sleeping',observe:'Watching the woodland',reflect:'Reflecting',gather:'Gathering materials',plan:'Preparing a construction plan',construct:'Constructing',move_object:'Carrying and placing an object',inspect:'Inspecting an object',fell_tree:'Felling a tree'})[s.action]);txt('reason',s.reason);$('energy').value=s.energy;txt('resources',`Wood: ${s.materials} kg · Stone: ${s.stone||0} kg · Archery sessions: ${s.skills.archery} · Carvings: ${s.skills.craft}`);txt('intention',s.current_intention||'Crow has not expressed an intention yet.');
setActivity(s);
$('feed').replaceChildren();for(const m of s.memories.slice(-16).reverse())entry($('feed'),m.event,[m.at?new Date(m.at).toLocaleString('en-GB',{timeZone:'Europe/London'}):`Earlier prototype · Day ${m.day} · ${m.time}`,m.intention?'Aim: '+m.intention:'',m.reason?'Why: '+m.reason:'',m.next_step?'Tentative next step: '+m.next_step:''].filter(Boolean).join(' · '));
$('wishes').replaceChildren();for(const w of s.wishes.slice(-10).reverse())entry($('wishes'),w.text,`${w.reason} · First expressed day ${w.day} · ${w.mentions} mention(s)`);if(!s.wishes.length)entry($('wishes'),'No wishes expressed yet.');
$('projects').replaceChildren();for(const p of s.projects.slice(-8).reverse())entry($('projects'),p.title,`${p.status} · ${p.progress}/${p.target} ${p.target_action} sessions`);if(!s.projects.length)entry($('projects'),'No projects chosen yet.');
$('emotions').replaceChildren();if(!s.affect)for(const [name,value]of Object.entries(s.emotions)){const label=document.createElement('div');label.textContent=name.charAt(0).toUpperCase()+name.slice(1);const bar=document.createElement('progress');bar.max=100;bar.value=value;$('emotions').append(label,bar)}
txt('feeling',s.appraisals.length?s.appraisals.at(-1).feeling:'He has not reflected on a completed experience yet.');
$('longterm').replaceChildren();for(const m of s.long_term.slice(-6).reverse())entry($('longterm'),m.interpretation,'Based on: '+m.fact);
$('reading').replaceChildren();const source=s.pending?.reading;if(source){const a=document.createElement('a');a.textContent=source.title;a.href=source.url;a.target='_blank';a.rel='noopener noreferrer';$('reading').append(a)}
const pending=s.pending;txt('remaining',pending?(pending.decision?.action==='read'&&pending.duration===0?`${s.paused?'Paused · ':''}Quick research · finishes after processing the excerpt`:`${s.paused?'Paused · ':''}${Math.ceil(pending.remaining/60)} min remaining · ${Math.round(pending.duration/60)} min session`):s.reflection_pending?'Processing this experience.':'Choosing the next activity.');
journal.update(s);
lifeView.update(s);diary.update(s);edda.visible=Boolean(s.keeper&&s.built_world?.objects?.trading_post);
$('creations').replaceChildren();for(const c of s.creations.slice(-8).reverse())entry($('creations'),c.name,`${c.shape} · Day ${c.day}`);if(s.built_world){syncBuiltWorld(s.built_world)}else{creations(s.creations)}syncEcology(s.ecology_view);lamp.intensity=s.action==='read'&&s.pending?15:(s.daylight<.2?8:1.5);
const celestial=sky.update(new Date(s.clock.iso));if($('skyInfo'))txt('skyInfo',`Sun ${celestial.sun.altitude.toFixed(0)}° · Moon ${celestial.moon.altitude.toFixed(0)}° above horizon · Wickford`);
if($('worldPlans')&&s.built_world){$('worldPlans').replaceChildren();for(const p of s.built_world.plans.slice(-5).reverse())entry($('worldPlans'),`${p.name} · ${p.status}`,`Plan ${p.id} · ${Object.entries(p.bill).map(([m,q])=>q+' kg '+m).join(', ')||'No new materials'} · ${p.work_done_minutes||0}/${p.minutes} min work`);$('worldObjects').replaceChildren();for(const o of Object.values(s.built_world.objects))entry($('worldObjects'),o.name,`${o.id} · (${o.x.toFixed(1)}, ${o.z.toFixed(1)}) · ${o.parts.length} parts`);txt('sourceStocks',Object.entries(s.built_world.sources).map(([m,v])=>`${m}: ${v.stock} kg remains`).join(' · '));}
}catch(e){if(updateRequested){txt('status','Reconnecting after the update…');txt('error','');}else{txt('status','Connection lost — keep the Python terminal open.');txt('error',e.message)}}}
function resize(){renderer.setSize(holder.clientWidth,holder.clientHeight);camera.aspect=holder.clientWidth/holder.clientHeight;camera.updateProjectionMatrix()}addEventListener('resize',resize);resize();
function frame(now){const dt=Math.min(.08,(now-last)/1000);last=now;if(keys.has('ArrowLeft'))yaw+=dt*1.5;if(keys.has('ArrowRight'))yaw-=dt*1.5;let f=(keys.has('KeyW')||keys.has('ArrowUp')?1:0)-(keys.has('KeyS')||keys.has('ArrowDown')?1:0),r=(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0);f+=touchInput.forward;r+=touchInput.right;const norm=Math.max(1,Math.hypot(f,r)),speed=4*dt/norm;const dx=(-Math.sin(yaw)*f+Math.cos(yaw)*r)*speed,dz=(-Math.cos(yaw)*f-Math.sin(yaw)*r)*speed;if(fits(camera.position.x+dx,camera.position.z))camera.position.x+=dx;if(fits(camera.position.x,camera.position.z+dz))camera.position.z+=dz;camera.rotation.set(pitch,yaw,0,'YXZ');
const simdt=s?.paused?0:dt;let moving=false;
const step=anim.steps[0];
if(step){
 if(step.kind==='walk'){
  anim.pose='walk';const delta=step.point.clone().sub(crow.position);delta.y=0;const d=delta.length();
  if(d<.04){crow.position.x=step.point.x;crow.position.z=step.point.z;if(step.face!==null)crow.rotation.y=step.face;anim.steps.shift();}
  else{moving=simdt>0;const angle=Math.atan2(delta.x,delta.z);crow.rotation.y+=Math.atan2(Math.sin(angle-crow.rotation.y),Math.cos(angle-crow.rotation.y))*Math.min(1,dt*10);crow.position.addScaledVector(delta.normalize(),Math.min(d,simdt*1.65));}
 }else{
  anim.pose=step.pose;step.elapsed+=simdt;
  if(step.pose==='sit'){
   const t=T.MathUtils.smoothstep(step.elapsed,0,step.duration);crow.position.lerpVectors(LIB.approach,LIB.seat,t);crow.rotation.y=Math.PI;anim.seated=t;
  }else if(step.pose==='sitfloor'){
   const t=T.MathUtils.smoothstep(step.elapsed,0,step.duration);anim.seated=t;anim.floor=t;crow.rotation.y=Math.PI;
  }else if(step.pose==='standfloor'){
   const t=T.MathUtils.smoothstep(step.elapsed,0,step.duration);anim.seated=1-t;anim.floor=1-t;
  }else if(step.pose==='stand'){
   const t=T.MathUtils.smoothstep(step.elapsed,0,step.duration);crow.position.lerpVectors(LIB.seat,LIB.approach,t);anim.seated=1-t;
  }else if(step.pose==='reading'){anim.seated=1;crow.rotation.y=Math.PI;}else if(step.pose==='readingFloor'){anim.seated=1;anim.floor=1;crow.rotation.y=Math.PI;}
  if(step.elapsed>=step.duration){anim.steps.shift();if(step.done)step.done();}
 }
}
anim.elapsed+=simdt;
const seated=anim.seated,walking=moving?Math.sin(anim.elapsed*8):0;
for(let i=0;i<2;i++){
 legs[i].rotation.x=seated*(-Math.PI/2)+(1-seated)*walking*(i?-.45:.45);
 knees[i].rotation.x=seated*(Math.PI/2)+anim.floor*(Math.PI/2)+(moving?Math.max(0,walking*(i?-1:1))*.25:0);
 arms[i].rotation.x=anim.book?-.65:walking*(i?.35:-.35);
 elbows[i].rotation.x=anim.book?-.85:0;
}
if(anim.pose==='take'||anim.pose==='putback'){arms[1].rotation.x=-1.4*Math.sin(Math.min(1,step.elapsed/step.duration)*Math.PI);elbows[1].rotation.x=-.15;}
headPivot.rotation.x=anim.book?.22+Math.sin(anim.elapsed*.5)*.015:0;
crow.position.y=-.28*seated-.36*anim.floor+(moving?Math.abs(walking)*.025:0);
torso.scale.y=1+Math.sin(anim.elapsed*1.8)*.008;edda.rotation.y=Math.sin(anim.elapsed*.3)*.25;
heldBook.visible=anim.book;if(shelfBook)shelfBook.visible=!anim.book;heldAxe.visible=anim.pose==='fell_tree'&&!moving;bow.visible=anim.pose==='practise'&&!anim.book&&!seated&&!heldAxe.visible;
const turn=anim.elapsed%24;pagePivot.rotation.z=anim.pose.startsWith('reading')&&turn<1.8?Math.PI*T.MathUtils.smoothstep(turn,0,1.8):0;
if(anim.pose==='practise'&&!moving){arms[0].rotation.x=-1.25;arms[1].rotation.x=-1.1;elbows[1].rotation.x=-.8;}
if(heldAxe.visible){arms[1].rotation.x=-.75+Math.sin(anim.elapsed*2)*.55;elbows[1].rotation.x=-.4;}
if(['eat','drink'].includes(anim.pose)&&!moving){arms[1].rotation.x=-1.25;elbows[1].rotation.x=-1.2+Math.sin(anim.elapsed*1.2)*.12;headPivot.rotation.x=.08;}
if(anim.pose==='inspect'&&!moving){headPivot.rotation.x=.38;arms[1].rotation.x=-.9;elbows[1].rotation.x=-.4+Math.sin(anim.elapsed*1.5)*.08;}
if(anim.pose==='gather'&&!moving){const bend=.5+Math.sin(anim.elapsed*1.4)*.25;arms[0].rotation.x=-bend;arms[1].rotation.x=-bend;headPivot.rotation.x=.3;}
if(anim.pose==='craft'&&!moving){arms[1].rotation.x=-.8+Math.sin(anim.elapsed*4)*.12;elbows[1].rotation.x=-.5;headPivot.rotation.x=.18;}
if(anim.pose==='observe'&&!moving)headPivot.rotation.y=Math.sin(anim.elapsed*.2)*.35;else headPivot.rotation.y=0;
crow.visible=!(anim.pose==='sleep');
sky.frame();renderer.render(scene,camera);requestAnimationFrame(frame)}
$('loading').remove();refresh();setInterval(refresh,2500);requestAnimationFrame(frame);
