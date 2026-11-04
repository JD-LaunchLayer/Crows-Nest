import * as T from '/vendor/three.module.js';
import {installTouchControls} from '/mobile_controls.js';
import {createSky} from '/sky.js';
import {createJournal} from '/journal.js';import {buildVillage} from '/village.js';import {createPlayer} from '/music_player.js';
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
const lifeView=createLifeView({document});const player=createPlayer();const diary=createDiary({document,player});
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
const stations={cabin:new T.Vector3(-10,0,-6),range:new T.Vector3(10,0,-7),woods:new T.Vector3(13,0,10),workbench:new T.Vector3(0,0,10),library:new T.Vector3(-11,0,5),cafe:new T.Vector3(9,0,-14.2),shop:new T.Vector3(-3,0,-14.2),garden:new T.Vector3(-9,0,-14.2)};
buildVillage({T,scene,mat}); // scenery only: lanes, green and high street (village.js)
// Open-front cabin: floor and three walls, so it is possible to look inside.
box(6,.15,5,'#806c4b',-10,.05,-10);box(6,3,.2,'#76644b',-10,1.5,-12.5);box(.2,3,5,'#806c4b',-13,1.5,-10);box(.2,3,5,'#806c4b',-7,1.5,-10);
block(-10,-12.5,6,.2);block(-13,-10,.2,5);block(-7,-10,.2,5);
const roof=mesh(new T.ConeGeometry(4.5,2.5,4),'#4e5540',-10,4,-10);roof.rotation.y=Math.PI/4;
const legacyBed=[box(1.5,.4,2.6,'#a3a782',-11.5,.35,-10.3),box(1.3,.18,.55,'#d5ccb1',-11.5,.65,-11.1)];const blanket=box(1.3,.1,1.6,'#6f7f63',-11.5,.95,-9.7);blanket.visible=false;box(.7,1,.6,'#8c704e',-8.2,.5,-11.5);
// Range target with concentric faces pointing into the clearing.
box(.18,2.5,.18,'#6e593e',10,1.25,-10);for(const [r,col,z] of [[1,'#dfd6b4',-9.9],[.7,'#877249',-9.86],[.45,'#d6c99e',-9.82],[.17,'#935d3e',-9.78]]){mesh(new T.CylinderGeometry(r,r,.07,16),'#'+col.replace('#',''),10,2,z).rotation.x=Math.PI/2;}block(10,-10,2,.5);
// Workbench, reading cabin and a small quiet pond.
const benchStart=scene.children.length;box(3,.23,1.4,'#a58c5c',0,1.2,12);for(const x of [-1.2,1.2])for(const z of [11.5,12.5])box(.17,1.2,.17,'#645739',x,.6,z);block(0,12,3,1.4);const legacyBench=scene.children.slice(benchStart),legacyBenchBlock=obstacles.at(-1);
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
block(LIB.seat.x,LIB.seat.z,1,1);const legacyChairBlock=obstacles.at(-1);
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
function tree(x,z,h=5,given=null){
 const id=given||'tree-'+treeNumber++,group=new T.Group();group.position.set(x,0,z);scene.add(group);
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
// Birds (v0.25): where each one is comes from the server, on Crow's clock, so what you see is what he could notice.
// Between moves they fly over in a short arc; in the air they circle; perched they bob and look about.
const birdGroup=new T.Group();scene.add(birdGroup);const birdMeshes=new Map();
function makeBird(b){
 const [body,wing,accent,bill]=b.colours,k=b.size/.3,g=new T.Group();birdGroup.add(g);
 const torsoB=mesh(new T.SphereGeometry(.09,8,6),body,0,0,0,g);torsoB.scale.set(.9,.85,1.35);torsoB.castShadow=false;
 mesh(new T.SphereGeometry(.07,8,6),accent,0,-.01,.05,g).scale.set(.85,.9,.7);
 const head=new T.Group();head.position.set(0,.07,.1);g.add(head);
 mesh(new T.SphereGeometry(.058,8,6),body,0,0,0,head);
 const bk=mesh(new T.ConeGeometry(.018,.06,4),bill,0,-.005,.07,head);bk.rotation.x=Math.PI/2;
 for(const x of [-.035,.035])mesh(new T.SphereGeometry(.011,5,4),'#0c0c0c',x,.015,.04,head);
 const tail=box(.07,.015,.12,wing,0,.01,-.15,g);tail.rotation.x=.25;
 const wings=[-1,1].map(side=>{const w=new T.Group();w.position.set(side*.07,.03,0);g.add(w);box(.13,.012,.1,wing,side*.065,0,0,w);return w});
 g.scale.setScalar(k);return {g,head,wings,pos:new T.Vector3(b.x,b.y,b.z),from:null,to:null,t:0,dur:1,mode:b.mode,target:b,angle:0};
}
function syncBirds(list){
 for(const b of list||[]){let m=birdMeshes.get(b.id);if(!m){m=makeBird(b);birdMeshes.set(b.id,m);m.g.position.set(b.x,b.y,b.z);}
  const moved=Math.hypot(b.x-m.target.x,b.z-m.target.z)>.2||Math.abs(b.y-m.target.y)>.2||b.mode!==m.target.mode;
  if(moved){m.from=m.g.position.clone();m.to=b.mode==='air'?new T.Vector3(b.x+(b.radius||8),b.y,b.z):new T.Vector3(b.x,b.y,b.z);
   m.t=0;m.dur=Math.min(7,Math.max(1.4,m.from.distanceTo(m.to)/5));}
  m.target=b;m.g.visible=b.mode!=='roost';}
}
function animateBirds(dt,elapsed){
 for(const m of birdMeshes.values()){if(!m.g.visible)continue;const b=m.target;let flapping=false;
  if(m.from&&m.t<1){m.t=Math.min(1,m.t+dt/m.dur);const e=T.MathUtils.smoothstep(m.t,0,1);
   const p=m.from.clone().lerp(m.to,e);p.y+=Math.sin(Math.PI*e)*Math.min(4,m.from.distanceTo(m.to)*.25);
   const d=p.clone().sub(m.g.position);if(d.lengthSq()>1e-6)m.g.rotation.y=Math.atan2(d.x,d.z);m.g.position.copy(p);flapping=true;
   if(m.t>=1){m.from=null;if(b.mode==='air')m.angle=0;}}
  else if(b.mode==='air'){m.angle+=dt*.5;const r=b.radius||8;const x=b.x+Math.cos(m.angle)*r,z=b.z+Math.sin(m.angle)*r;
   m.g.rotation.y=Math.atan2(-Math.sin(m.angle),Math.cos(m.angle))+Math.PI;m.g.position.set(x,b.y+Math.sin(elapsed*.7+m.angle)*.4,z);flapping=Math.sin(elapsed*1.3+m.angle*3)>-.2;}
  else{m.g.position.y=b.y+.05+Math.abs(Math.sin(elapsed*3+m.angle))*.006;m.head.rotation.y=Math.sin(elapsed*.9+b.x)*.8;
   if(b.mode==='ground'&&Math.sin(elapsed*.6+b.z)>.95)m.head.rotation.x=.6;else m.head.rotation.x=0;}
  const flap=flapping?Math.sin(elapsed*22)*.9:0;m.wings[0].rotation.z=-flap-.05;m.wings[1].rotation.z=flap+.05;}
}
// Deer (v0.26): a small herd whose places come from the server on Crow's clock. They walk between spots,
// lower their heads to feed, lift them to look about, and lie down by day and at night.
const deerGroup=new T.Group();scene.add(deerGroup);const deerMeshes=new Map();
function makeDeer(d){
 const coat='#8a6a4c',dark='#4a3a2c',g=new T.Group();deerGroup.add(g);const body=new T.Group();g.add(body);
 const trunk=mesh(new T.SphereGeometry(.3,10,8),coat,0,.78,0,body);trunk.scale.set(.75,.72,1.55);
 mesh(new T.SphereGeometry(.13,8,6),'#efe8dc',0,.86,-.42,body).scale.set(1,1.1,.5);              // pale rump patch
 const neck=new T.Group();neck.position.set(0,.95,.36);body.add(neck);
 const nk=mesh(new T.CylinderGeometry(.07,.1,.42,7),coat,0,.18,.06,neck);nk.rotation.x=.45;
 const head=new T.Group();head.position.set(0,.38,.18);neck.add(head);
 mesh(new T.SphereGeometry(.1,8,6),coat,0,0,0,head).scale.set(.85,.9,1.2);
 const snout=mesh(new T.ConeGeometry(.06,.18,6),coat,0,-.03,.15,head);snout.rotation.x=Math.PI/2;
 mesh(new T.SphereGeometry(.028,6,5),'#151515',0,-.03,.24,head);
 for(const x of [-.06,.06]){const ear=mesh(new T.ConeGeometry(.04,.14,5),coat,x*1.4,.1,-.03,head);ear.rotation.z=x>0?-.6:.6;ear.scale.z=.5;
  mesh(new T.SphereGeometry(.018,5,4),'#111',x*.9,.03,.07,head);}
 if(d.role==='buck')for(const x of [-.04,.04]){const a=mesh(new T.CylinderGeometry(.008,.014,.2,4),'#d9cdb3',x,.17,0,head);a.rotation.z=x>0?-.15:.15;}
 const legs=[];for(const [x,z] of [[-.12,.3],[.12,.3],[-.12,-.3],[.12,-.3]]){const hip=new T.Group();hip.position.set(x,.68,z);body.add(hip);
  cyl(.03,.02,.68,dark,0,-.34,0,hip,5);legs.push(hip);}
 const k=d.small?.6:1;g.scale.setScalar(k);
 return {g,body,neck,legs,from:null,to:null,t:0,dur:1,target:d,phase:Math.random()*6};
}
function syncDeer(list){
 const seen=new Set();
 for(const d of list||[]){seen.add(d.id);let m=deerMeshes.get(d.id);if(!m){m=makeDeer(d);deerMeshes.set(d.id,m);m.g.position.set(d.x,0,d.z);m.g.rotation.y=d.heading;}
  if(Math.hypot(d.x-m.target.x,d.z-m.target.z)>.3){m.from=m.g.position.clone();m.to=new T.Vector3(d.x,0,d.z);m.t=0;m.dur=Math.min(20,Math.max(3,m.from.distanceTo(m.to)/1.4));}
  m.target=d;}
 for(const [id,m] of deerMeshes)if(!seen.has(id)){deerGroup.remove(m.g);deerMeshes.delete(id);}
}
function animateDeer(dt,elapsed){
 for(const m of deerMeshes.values()){const d=m.target;let walking=false;
  if(m.from&&m.t<1){m.t=Math.min(1,m.t+dt/m.dur);const p=m.from.clone().lerp(m.to,T.MathUtils.smoothstep(m.t,0,1));
   const dir=p.clone().sub(m.g.position);if(dir.lengthSq()>1e-7)m.g.rotation.y=Math.atan2(dir.x,dir.z);m.g.position.copy(p);walking=true;if(m.t>=1)m.from=null;}
  const lying=!walking&&(d.doing==='lying down'||d.doing==='bedded down');
  m.body.position.y=T.MathUtils.lerp(m.body.position.y,lying?-.5:0,dt*2);
  m.legs.forEach((l,i)=>{l.rotation.x=walking?Math.sin(elapsed*6+i*1.6)*.45:lying?(i<2?-1.3:1.3):0;});
  const feeding=!walking&&!lying&&(d.doing==='browsing'||d.doing==='grazing')&&Math.sin(elapsed*.4+m.phase)>-.4;
  m.neck.rotation.x=T.MathUtils.lerp(m.neck.rotation.x,feeding?1.25:d.doing==='standing alert'?-.25:0,dt*2);}
}
// Garden beds beside the cabin: soil darkens when damp, weeds show as tufts, plants grow with the crop.
const GARDEN_BEDS=[[-11.4,-15.6],[-9.0,-15.6],[-6.6,-15.6]];const gardenGroup=new T.Group();scene.add(gardenGroup);let gardenKey='';
function syncGarden(g){
 if(!g)return;const key=JSON.stringify(g.beds.map(b=>[b.crop,Math.round(b.growth*10),b.moisture>.3,Math.round(b.weeds*4),b.health<.6]));if(key===gardenKey)return;gardenKey=key;
 while(gardenGroup.children.length){const c=gardenGroup.children[0];gardenGroup.remove(c);c.geometry?.dispose()}
 g.beds.forEach((b,i)=>{const [x,z]=GARDEN_BEDS[i];
  const frame=box(1.9,.18,1.1,'#6b5236',x,.09,z,gardenGroup);frame.castShadow=false;
  box(1.75,.06,.95,b.moisture>.3?'#4e3a28':'#8f7a58',x,.19,z,gardenGroup).castShadow=false;
  const tufts=Math.round(b.weeds*6);for(let k=0;k<tufts;k++)mesh(new T.ConeGeometry(.05,.14,4),'#5f7a3a',x-.75+k*.28,.27,z+((k%2)?.35:-.33),gardenGroup);
  if(b.crop==='growing'||b.crop==='withered'){const h=b.crop==='withered'?.12:.08+.42*Math.min(1,b.growth);const c=b.crop==='withered'?'#7a6440':(b.health<.6?'#9aa04a':(b.growth>=1?'#3f7a2f':'#5f9a45'));
   for(let k=0;k<4;k++)mesh(new T.ConeGeometry(.09+.1*Math.min(1,b.growth),h,5),c,x-.6+k*.4,.22+h/2,z,gardenGroup);}
 });
}
// v0.31.2: raw materials in his woods, as anyone walking there would see them; fuller or thinner as he takes from them.
const resourceGroup=new T.Group();scene.add(resourceGroup);let resourceKey='';
const RES_SEASON={reeds:{winter:'#b9a978',spring:'#7f9a55',summer:'#5f8a45',autumn:'#b5a26a'},flax:{winter:'#9a8a6a',spring:'#7fa06a',summer:'#6f8f9a',autumn:'#b8a46a'},nettles:{winter:'#8a8a80',spring:'#3f6a35',summer:'#355f2f',autumn:'#6f6a40'}};
function syncResources(view){
 if(!view)return;const key=JSON.stringify(view.map(r=>[r.id,Math.round(r.left*5),r.season]));if(key===resourceKey)return;resourceKey=key;
 while(resourceGroup.children.length){const c=resourceGroup.children[0];resourceGroup.remove(c);c.geometry?.dispose()}
 for(const r of view){const {x,z}=r,f=Math.max(.15,r.left),rnd=i=>{const v=Math.sin((x*12.9898+z*78.233+i*37.719))*43758.5453;return v-Math.floor(v)};
  const flat=(rad,c)=>{const m=mesh(new T.CylinderGeometry(rad,rad*1.05,.03,10),c,x,.015,z,resourceGroup);m.castShadow=false;return m};
  if(r.kind==='clay_bed'){flat(1.3*Math.sqrt(f),'#7d6650');}
  else if(r.kind==='sand_gravel'){flat(1.4,'#c9b383');for(let i=0;i<6;i++)mesh(new T.SphereGeometry(.07,5,4),'#9c917e',x-1+2*rnd(i),.06,z-1+2*rnd(i+9),resourceGroup);}
  else if(r.kind==='reeds'||r.kind==='flax'){const c=RES_SEASON[r.kind][r.season],n=Math.round((r.kind==='reeds'?16:12)*f),h=r.kind==='reeds'?1.8:.8;
   for(let i=0;i<n;i++)cyl(.015,.02,h,c,x-.7+1.4*rnd(i),h/2,z-.7+1.4*rnd(i+20),resourceGroup,4);}
  else if(r.kind==='nettles'){const c=RES_SEASON.nettles[r.season],n=Math.round(7*f),h=r.season==='winter'?.9:1.1;
   for(let i=0;i<n;i++)mesh(new T.ConeGeometry(r.season==='winter'?.04:.18,h,5),c,x-.6+1.2*rnd(i),h/2,z-.6+1.2*rnd(i+30),resourceGroup);}
  else if(r.kind==='flint'){for(let i=0;i<Math.round(6*f);i++)mesh(new T.DodecahedronGeometry(.09+.06*rnd(i)),'#e8e4d8',x-.8+1.6*rnd(i),.07,z-.8+1.6*rnd(i+40),resourceGroup);}
  else if(r.kind==='iron_hollow'){flat(1.5,'#8a5a32');for(let i=0;i<Math.round(6*f);i++)mesh(new T.DodecahedronGeometry(.12),'#6e4026',x-1.2+2.4*rnd(i),.08,z-1.2+2.4*rnd(i+50),resourceGroup);}
  else if(r.kind==='copper_outcrop'){box(1.6,.7,1.1,'#7d7a72',x,.35,z,resourceGroup);for(let i=0;i<Math.round(5*f);i++)box(.25,.08,.2,'#3f8a6a',x-.6+1.2*rnd(i),.72,z-.4+.8*rnd(i+60),resourceGroup);}
  else if(r.kind==='tin_stones'){flat(.9,'#9c917e');for(let i=0;i<Math.round(5*f);i++)mesh(new T.SphereGeometry(.06,5,4),'#2f2a28',x-.6+1.2*rnd(i),.05,z-.6+1.2*rnd(i+70),resourceGroup);}
 }
}
// v0.32.0: his heaps and fires: a pile of wood and stems, flames and a warm light when lit, grey ash after.
const fireGroup=new T.Group();scene.add(fireGroup);let fireKey='';const fireLights=[];
function syncFires(view){
 if(!view)return;const key=JSON.stringify(view.map(f=>[f.id,f.lit,Math.round(f.kg*2),f.ash>0,!!f.covered]));if(key===fireKey)return;fireKey=key;
 while(fireGroup.children.length){const c=fireGroup.children[0];fireGroup.remove(c);c.geometry?.dispose()}fireLights.length=0;
 for(const f of view){const {x,z}=f,h=Math.min(.6,.12+f.kg*.06);
  if(f.ash>0&&!f.lit&&f.kg<.05){const a=mesh(new T.CylinderGeometry(.45,.5,.02,9),'#8d8a84',x,.01,z,fireGroup);a.castShadow=false;continue;}
  if(f.kg>.02)mesh(new T.ConeGeometry(.45,h,7),'#6b4e2e',x,h/2,z,fireGroup);
  if(f.lit&&f.covered){const m=mesh(new T.SphereGeometry(.55,9,6),'#6e5a44',x,.05,z,fireGroup);m.scale.y=.5;
   const sm=mesh(new T.ConeGeometry(.08,.7,5),'#b9b4ac',x,.6,z,fireGroup);sm.castShadow=false;sm.material=new T.MeshStandardMaterial({color:'#b9b4ac',transparent:true,opacity:.45,flatShading:true});
   const l=new T.PointLight('#ff7a30',.6,2.5);l.position.set(x,.3,z);fireGroup.add(l);fireLights.push(l);continue;}
  if(f.lit){mesh(new T.ConeGeometry(.22,.55,6),'#ff9a3a',x,h+.2,z,fireGroup).castShadow=false;mesh(new T.ConeGeometry(.12,.35,5),'#ffd36a',x,h+.25,z,fireGroup).castShadow=false;
   const l=new T.PointLight('#ffb060',4,8);l.position.set(x,h+.6,z);fireGroup.add(l);fireLights.push(l);}
 }
}
function syncTrees(world){
 for(const [id,t]of Object.entries(world.trees||{})){
  let visual=treeMeshes.get(id);
  // Trees beyond the original ring (the deeper woods) and ones he planted are built from his world as they appear;
  // a planted tree is rebuilt as it grows.
  if(visual&&t.stage==='young'&&Math.abs(visual.h-t.height)>.2){scene.remove(visual.group);treeMeshes.delete(id);visual=null;}
  if(!visual){tree(t.x,t.z,Math.max(.4,t.height),id);visual=treeMeshes.get(id);ecologyKey='';}
  visual.group.visible=t.stage==='standing'||t.stage==='young';
  if(t.stage==='felled'&&!visual.stump){visual.stump=mesh(new T.CylinderGeometry(.2,.25,.4,6),'#8a7350',visual.x,.2,visual.z);visual.log=mesh(new T.CylinderGeometry(.16,.20,visual.h*.65,6),'#856a43',visual.x+.7,.22,visual.z);visual.log.rotation.z=Math.PI/2;}
  if(visual.log){visual.log.visible=t.stock>0;visual.log.scale.y=Math.max(.02,t.stock/t.timber_kg)}
 }
}

for(let i=0;i<65;i++){const a=i*2.39996,r=23+(i%7)*1.1;tree(Math.cos(a)*r,Math.sin(a)*r,4+(i%5)*.65)}
for(const [x,z,h]of [[17,10,5],[15,14,6],[20,12,5],[18,6,4],[-18,-9,5],[-20,-15,6]])tree(x,z,h);
// Small details without textures or outside image services.
for(let i=0;i<65;i++){let a=i*2.4,r=6+(i%11)*1.4;const x=Math.cos(a)*r,z=Math.sin(a)*r;if(Math.abs(x)<2||Math.abs(z)<2)continue;const stone=mesh(new T.DodecahedronGeometry(.13+(i%3)*.06,0),i%4?'#828771':'#b4ac7e',x,.13,z);stone.scale.y=.6;}
// Fixed name boards: over doorways, or on posts for open places. Readable from both sides,
// they stay where they are mounted instead of turning to face the viewer.
function sign(text,x,y,z,face,{w=2.6,h=.46,post=false}={}){
 const c=document.createElement('canvas');c.width=512;c.height=Math.round(512*h/w);const q=c.getContext('2d');
 q.fillStyle='#283b2b';q.fillRect(0,0,c.width,c.height);q.strokeStyle='#8a7550';q.lineWidth=6;q.strokeRect?.(3,3,c.width-6,c.height-6);
 q.fillStyle='#eee5c7';let size=Math.round(c.height*.52);q.font=`${size}px Georgia`;while((q.measureText?.(text)?.width||0)>c.width*.86&&size>10){size-=2;q.font=`${size}px Georgia`;}
 q.textAlign='center';q.textBaseline='middle';q.fillText(text,c.width/2,c.height/2+2);
 const texture=new T.CanvasTexture(c);texture.colorSpace=T.SRGBColorSpace;
 const face_=new T.MeshStandardMaterial({map:texture,emissiveMap:texture,emissive:0xffffff,emissiveIntensity:.18,roughness:1});
 const g=new T.Group();g.position.set(x,y,z);g.rotation.y=Math.atan2(face[0]-x,face[1]-z);scene.add(g);
 box(w+.08,h+.08,.05,'#4b3b27',0,0,0,g);
 for(const side of [1,-1]){const m=new T.Mesh(new T.PlaneGeometry(w,h),face_);m.position.z=side*.03;if(side<0)m.rotation.y=Math.PI;g.add(m);}
 if(post)for(const px of [-w/2+.12,w/2-.12])box(.1,y,.1,'#5b4a33',px,-y/2,0,g);
 return g;
}
sign('THE CABIN',-10,2.3,-6.75,[-10,0],{w:2.2,h:.42});
sign('READING CABIN',-11,2.75,6.84,[-11,0],{w:2.8});
sign('TRADING POST',-3,2.56,-14.78,[-3,0],{w:3.2});
sign('INTERNET CAFÉ',9,2.56,-14.78,[9,0],{w:3.2});
sign('ARCHERY RANGE',12.4,1.55,-8.4,[2,0],{w:2.2,h:.42,post:true});
sign('WORKBENCH',-2.4,1.45,11.2,[0,0],{w:1.9,h:.4,post:true});
sign('WOODLAND',13.8,1.55,8.1,[6,3.6],{w:1.8,h:.4,post:true});
sign('GARDEN',-12.9,1.3,-14.7,[-8,-8],{w:1.5,h:.38,post:true});
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
// His lantern: carried and lit after dark once he owns one. The light is real in the scene.
const heldLantern=new T.Group();elbows[0].add(heldLantern);heldLantern.position.set(0,-.38,.06);heldLantern.visible=false;
mesh(new T.CylinderGeometry(.06,.07,.14,6),'#b08a3c',0,-.07,0,heldLantern);mesh(new T.SphereGeometry(.045,8,6),'#ffd27a',0,-.07,0,heldLantern);
const lanternLight=new T.PointLight(0xffc56b,0,9,1.6);lanternLight.position.set(0,-.07,0);heldLantern.add(lanternLight);
const heldAxe=new T.Group();box(.055,.55,.055,'#937449',0,0,0,heldAxe);box(.30,.14,.07,'#a8afaa',.10,.21,0,heldAxe);elbows[1].add(heldAxe);heldAxe.position.set(0,-.29,.08);heldAxe.visible=false;
const heldHarp=new T.Group();crow.add(heldHarp);heldHarp.position.set(.05,.62,.34);heldHarp.rotation.y=Math.PI/2;
box(.05,.62,.05,'#c9b48a',-.16,.3,0,heldHarp);box(.36,.05,.05,'#c9b48a',.02,.6,0,heldHarp);const harpNeck=box(.05,.5,.05,'#b89c6e',.2,.36,0,heldHarp);harpNeck.rotation.z=-.5;
for(let i=0;i<7;i++)box(.006,.12+i*.06,.006,'#eee6cf',-.12+i*.045,.3+i*.03,0,heldHarp);heldHarp.visible=false;
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
 const seat=s?.built_world?.objects?.library_chair;
 if(seat?.parts?.length){LIB.seat.set(seat.x,0,seat.z);LIB.approach.set(seat.x,0,seat.z-.8);}
 const spot=anim.desired?.spot||'standing';
 const after=spot==='chair'?[walk(LIB.approach,Math.PI),wait('sit',1.2),wait('reading',Infinity)]:
 spot==='floor'?[walk(LIB.floor,Math.PI),wait('sitfloor',1.2),wait('readingFloor',Infinity)]:
 [walk(LIB.aisle,Math.PI),wait('readingStanding',Infinity)];
 anim.steps=[walk(new T.Vector3(0,0,0)),walk(LIB.door),walk(LIB.aisle),walk(LIB.shelf,0),
 wait('take',1.4,()=>{anim.book=true}),walk(LIB.aisle),...after];
}
// His bed in the cabin: sleeping lies him down under a blanket; resting sits him on its edge.
const BEDSIDE=new T.Vector3(-10.2,0,-10.1);
// Where an activity actually happens: the chosen area, tree, plant or object, when the decision names one.
const AREA_SPOTS={grove:[15.5,8.5],spring_side:[-15.6,-1.5],clearing:[1.5,2.5],deeper_woods:[27,13]};
// Inside the buildings: at the trading post counter, or on the café terminal stool.
const INSIDE={trade:[-3,-16.4],talk:[-3,-16.4],browse:[10.3,-17.6]};
function targetFor(d){
 if(!d.pending)return null;
 if(INSIDE[d.action])return new T.Vector3(INSIDE[d.action][0],0,INSIDE[d.action][1]);
 if(d.action==='observe'){
  if(AREA_SPOTS[d.area])return new T.Vector3(...[AREA_SPOTS[d.area][0],0,AREA_SPOTS[d.area][1]]);
  const a=Math.atan2(crow.position.z,crow.position.x)||0;return new T.Vector3(Math.cos(a)*20,0,Math.sin(a)*20);
 }
 if(d.action==='interact'&&d.posture)return new T.Vector3(d.posture.x,0,d.posture.z);
 if(['inspect','gather','interact'].includes(d.action)&&d.objectId){
  const o=s.built_world?.objects?.[d.objectId]||s.built_world?.trees?.[d.objectId]||(s.ecology?.plants||[]).find(p=>p.id===d.objectId);
  if(o){const r=Math.hypot(o.x,o.z)||1;return new T.Vector3(o.x-o.x/r*1.1,0,o.z-o.z/r*1.1)}
 }
 return null;
}
// Walk straight there unless something solid is in the way; then go round by the green as before.
function route(to){
 const from=crow.position,dx=to.x-from.x,dz=to.z-from.z,len=Math.hypot(dx,dz);
 for(let k=1;k<len/.4;k++){const t=k*.4/len;if(t*len<.9||len-t*len<.9)continue;const x=from.x+dx*t,z=from.z+dz*t;
  if(obstacles.some(o=>Math.abs(x-o.x)<o.w&&Math.abs(z-o.z)<o.d))return [walk(new T.Vector3(0,0,0)),walk(to)];}
 return [walk(to)];
}
function beginDesired(){
 const wasPondering=anim.activeAction==='ponder'&&anim.floor>0;
 anim.returning=false;anim.seated=0;anim.floor=0;
 const d=anim.desired;if(!d)return;
 // Between activities he is choosing what to do next: he sits down where he is rather than heading off (v0.24).
 if(!d.pending&&!d.twin&&!anim.snap){anim.activeAction='ponder';anim.steps=[wait('ponderdown',1.1),wait('ponder',Infinity)];return}
 const rise=wasPondering?[wait('ponderup',.9)]:[];
 if(d.pending&&d.action==='read'){readingPlan();return}
 anim.activeAction=d.pending?d.action:'idle';
 const pose=d.pending&&d.action==='interact'&&d.posture?(d.posture.verb==='sit'?'objectSit':'objectLie'):(d.pending?d.action:'idle');
 let place=stations[d.location]||stations.cabin;
 if(d.pending&&['eat','drink'].includes(d.action)){const target=s.built_world?.objects[d.objectId||(d.action==='eat'?'food_store':'spring')];if(target)place=new T.Vector3(target.x,0,target.z-1);}
 if(d.pending&&d.action==='plant_tree'&&d.dest&&isFinite(d.dest[0])){place=new T.Vector3(d.dest[0]-.8,0,d.dest[1]);}
 if(d.pending&&d.action==='fell_tree'){const tree=s.built_world?.trees[d.objectId];if(tree)place=new T.Vector3(tree.x-.9,0,tree.z);}
 place=targetFor(d)||place;
 const toBed=d.pending&&['sleep','rest'].includes(d.action);if(toBed)place=BEDSIDE.clone();
 // The twin's clock outruns any walk, so its view shows him where he is rather than on the way there.
 // Opening the page mid-activity shows him where he already is; the twin's clock outruns any walk.
 if(d.twin||anim.snap){anim.snap=false;crow.position.copy(place);anim.steps=[wait(pose,Infinity)];return}
 if(wasPondering){anim.seated=1;anim.floor=1;}
 anim.steps=toBed?[...rise,...route(stations.cabin),walk(place),wait(d.action,Infinity)]
  :[...rise,...route(place),wait(pose,Infinity)];
}
function setActivity(data){
 const key=`${data.decisions}:${Boolean(data.pending)}`;if(key===anim.key)return;
 anim.key=key;anim.desired={action:data.action,location:data.location,pending:Boolean(data.pending),spot:data.pending?.decision?.reading_spot||'standing',objectId:data.pending?.decision?.object_id||'',area:data.pending?.decision?.observe_area||'',twin:Boolean(data.twin),posture:data.pending?.posture||null,verb:data.pending?.decision?.verb||'',dest:data.pending?.decision?[data.pending.decision.destination_x,data.pending.decision.destination_z]:null};
 if(!initialized){initialized=true;crow.position.copy(stations[data.location]||stations.cabin);anim.snap=true;}
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
const worldMeshes=new Map();let worldObstacleRecords=[],furnitureReplaced=false;
function syncBuiltWorld(world){
 if(!world)return;syncTrees(world);
 if(world.interaction_furniture&&!furnitureReplaced){
  for(const m of [...legacyBed,...legacyBench,chair]){scene.remove(m);m.traverse?.(c=>c.geometry?.dispose());}
  for(const b of [legacyBenchBlock,legacyChairBlock]){const i=obstacles.indexOf(b);if(i>=0)obstacles.splice(i,1);}
  furnitureReplaced=true;
 }
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
    else if(p.shape==='wedge'){const tri=new T.Shape();tri.moveTo(-.5,-.5);tri.lineTo(.5,-.5);tri.lineTo(0,.5);tri.closePath();geo=new T.ExtrudeGeometry(tri,{depth:1,bevelEnabled:false});geo.translate(0,0,-.5);}
    else if(p.shape==='arch'){geo=new T.TorusGeometry(.42,.08,6,14,Math.PI);geo.translate(0,-.42,0);}
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
$('find').onclick=()=>{const p=crow.position;if(p.x<-7&&p.x>-15&&p.z>6&&p.z<13){camera.position.set(-11,1.7,8);yaw=Math.atan2(camera.position.x-p.x,camera.position.z-p.z);pitch=-.10;return;}const candidates=[[p.x,p.z+4],[p.x+4,p.z],[p.x-4,p.z],[p.x,p.z-4]];const clear=(x,z)=>{for(let i=1;i<10;i++){const t=i/10;if(!fits(x+(p.x-x)*t*.85,z+(p.z-z)*t*.85))return false}return true};const at=candidates.find(([x,z])=>fits(x,z)&&clear(x,z))||candidates.find(([x,z])=>fits(x,z));if(at){camera.position.set(at[0],1.7,at[1]);yaw=Math.atan2(at[0]-p.x,at[1]-p.z);pitch=-.06}};
$('toggle').onclick=async()=>{const b=$('toggle');b.disabled=true;try{const r=await apiFetch('/api/toggle',{method:'POST',headers:{'X-Crow':'local'}});if(!r.ok)throw Error('Could not change pause state');await refresh()}catch(e){txt('error',e.message)}finally{b.disabled=false}};
const touchInput=typeof $('touchPad').addEventListener==='function'?installTouchControls({canvas:renderer.domElement,pad:$('touchPad'),knob:$('stickKnob'),onLook:(dx,dy)=>{yaw-=dx;pitch=T.MathUtils.clamp(pitch-dy,-1.1,1.1)}}):{forward:0,right:0};
$('mobileFind').onclick=()=>$('find').onclick();
if($('sound'))$('sound').onclick=()=>{player.setEnabled(!player.enabled);$('sound').textContent=player.enabled?'Sound on':'Sound off';if(player.enabled&&s)player.follow(s);};
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
txt('toggle',s.paused?'Begin life':'Pause');{const visitor=s.viewer==='visitor';$('toggle').hidden=visitor;const up=$('updateCrow')?.closest?.('section');if(up)up.hidden=visitor;document.body?.classList?.toggle('visitor',visitor);}txt('clock',`${s.clock.date} · ${s.clock.time} · ${s.twin?'twin clock':s.crow_clock?`Crow's time${s.crow_clock.scale>1?' ('+s.crow_clock.scale+'× speed)':''}`:'UK time'}`);txt('status',s.runtime.status+(s.last_seconds!==null?' · Last choice '+s.last_seconds+'s':''));txt('error',s.last_error);$('toggle').disabled=updating;txt('activity',({eat:'Eating',drink:'Drinking',rest:'Resting',practise:'Practising archery',explore:'Exploring',craft:'Making a carving',read:'Reading Wikipedia',sleep:'Sleeping',observe:'Watching the woodland',reflect:'Reflecting',gather:'Gathering materials',plan:'Preparing a construction plan',construct:'Constructing',move_object:'Carrying and placing an object',inspect:'Inspecting an object',fell_tree:'Felling a tree',interact:'Working with objects',browse:'Browsing the web',talk:'Talking with Edda',trade:'At the trading post',use_item:'Using an item',garden:'Working in the garden',plant_tree:'Planting a tree',play_music:'Playing the harp',resume_work:'Returning to his work',hunt:'Out with the bow',butcher:'Cutting up a carcass',preserve:'Smoking meat',put_out_food:'Putting food out and waiting quietly',notebook:'Writing in his notebook'})[s.action]||s.action);txt('reason',s.reason);{const b=s.body||{};$('energy').value=b.reserve??s.energy;if($('rested'))$('rested').value=Math.max(0,Math.min(100,100-(b.sleep_debt||0)*100/12-(b.exertion||0)*40));}txt('resources',`Wood: ${s.materials} kg · Stone: ${s.stone||0} kg · Archery sessions: ${s.skills.archery} · Carvings: ${s.skills.craft}`);txt('intention',s.current_intention||'Crow has not expressed an intention yet.');
setActivity(s);
$('feed').replaceChildren();for(const m of s.memories.slice(-16).reverse())entry($('feed'),m.event,[m.at?new Date(m.at).toLocaleString('en-GB',{timeZone:'Europe/London'}):`Earlier prototype · Day ${m.day} · ${m.time}`,m.intention?'Aim: '+m.intention:'',m.reason?'Why: '+m.reason:'',m.next_step?'Tentative next step: '+m.next_step:''].filter(Boolean).join(' · '));
$('wishes').replaceChildren();for(const w of s.wishes.slice(-10).reverse())entry($('wishes'),w.text,`${w.reason} · First expressed day ${w.day} · ${w.mentions} mention(s)`);if(!s.wishes.length)entry($('wishes'),'No wishes expressed yet.');
$('projects').replaceChildren();for(const p of s.projects.slice(-8).reverse())entry($('projects'),p.title,`${p.status} · ${p.progress}/${p.target} ${p.target_action} sessions${p.feel?` · felt mostly ${p.feel.mostly||'mixed'} (pull ${p.feel.pull}, grind ${p.feel.grind}, doubt ${p.feel.doubt})`:''}`);if(!s.projects.length)entry($('projects'),'No projects chosen yet.');
$('emotions').replaceChildren();if(!s.affect)for(const [name,value]of Object.entries(s.emotions)){const label=document.createElement('div');label.textContent=name.charAt(0).toUpperCase()+name.slice(1);const bar=document.createElement('progress');bar.max=100;bar.value=value;$('emotions').append(label,bar)}
txt('feeling',s.appraisals.length?s.appraisals.at(-1).feeling:'He has not reflected on a completed experience yet.');
$('longterm').replaceChildren();for(const m of s.long_term.slice(-6).reverse())entry($('longterm'),m.interpretation,'Based on: '+m.fact);
$('reading').replaceChildren();const source=s.pending?.reading;if(source){const a=document.createElement('a');a.textContent=source.title;a.href=source.url;a.target='_blank';a.rel='noopener noreferrer';$('reading').append(a)}
const pending=s.pending;txt('remaining',pending?(pending.decision?.action==='read'&&pending.duration===0?`${s.paused?'Paused · ':''}Quick research · finishes after processing the excerpt`:`${s.paused?'Paused · ':''}${Math.ceil(pending.remaining/60)} min remaining · ${Math.round(pending.duration/60)} min session`):s.reflection_pending?'Processing this experience.':'Choosing the next activity.');
journal.update(s);
lifeView.update(s);diary.update(s);player.follow(s);syncGarden(s.garden);edda.visible=Boolean(s.keeper&&s.built_world?.objects?.trading_post);const lit=Boolean(s.possessions?.lantern)&&s.daylight<.12;heldLantern.visible=lit;lanternLight.intensity=lit?6:0;
$('creations').replaceChildren();for(const c of s.creations.slice(-8).reverse())entry($('creations'),c.name,`${c.shape} · Day ${c.day}`);if(s.built_world){syncBuiltWorld(s.built_world)}else{creations(s.creations)}syncEcology(s.ecology_view);syncBirds(s.birds_view);syncDeer(s.deer_view);syncResources(s.resources_view);syncFires(s.fires_view);lamp.intensity=s.action==='read'&&s.pending?15:(s.daylight<.2?8:1.5);
const celestial=sky.update(new Date(s.clock.iso));if($('skyInfo'))txt('skyInfo',`Sun ${celestial.sun.altitude.toFixed(0)}° · Moon ${celestial.moon.altitude.toFixed(0)}° above horizon · Wickford`);
if($('worldPlans')&&s.built_world){$('worldPlans').replaceChildren();for(const p of s.built_world.plans.slice(-5).reverse())entry($('worldPlans'),`${p.name} · ${p.status}`,`Plan ${p.id} · ${Object.entries(p.bill).map(([m,q])=>q+' kg '+m).join(', ')||'No new materials'} · ${p.work_done_minutes||0}/${p.minutes} min work`);$('worldObjects').replaceChildren();for(const o of Object.values(s.built_world.objects))entry($('worldObjects'),o.name,`${o.id} · (${o.x.toFixed(1)}, ${o.z.toFixed(1)}) · ${o.parts.length} parts`);txt('sourceStocks',Object.entries(s.built_world.sources).map(([m,v])=>`${m}: ${v.stock} kg remains`).join(' · '));}
}catch(e){if(updateRequested){txt('status','Reconnecting after the update…');txt('error','');}else{txt('status','Connection lost — keep the Python terminal open.');txt('error',e.message)}}}
function resize(){renderer.setSize(holder.clientWidth,holder.clientHeight);camera.aspect=holder.clientWidth/holder.clientHeight;camera.updateProjectionMatrix()}addEventListener('resize',resize);resize();
function frame(now){const dt=Math.min(.08,(now-last)/1000);last=now;animateBirds(dt,now/1000);animateDeer(dt,now/1000);if(keys.has('ArrowLeft'))yaw+=dt*1.5;if(keys.has('ArrowRight'))yaw-=dt*1.5;let f=(keys.has('KeyW')||keys.has('ArrowUp')?1:0)-(keys.has('KeyS')||keys.has('ArrowDown')?1:0),r=(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0);f+=touchInput.forward;r+=touchInput.right;const norm=Math.max(1,Math.hypot(f,r)),speed=4*dt/norm;const dx=(-Math.sin(yaw)*f+Math.cos(yaw)*r)*speed,dz=(-Math.cos(yaw)*f-Math.sin(yaw)*r)*speed;if(fits(camera.position.x+dx,camera.position.z))camera.position.x+=dx;if(fits(camera.position.x,camera.position.z+dz))camera.position.z+=dz;camera.rotation.set(pitch,yaw,0,'YXZ');
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
  }else if(step.pose==='ponderdown'||step.pose==='ponder'||step.pose==='play_music'){
   const t=step.pose==='ponderdown'?T.MathUtils.smoothstep(step.elapsed,0,step.duration):1;anim.seated=t;anim.floor=t;
  }else if(step.pose==='ponderup'){
   const t=T.MathUtils.smoothstep(step.elapsed,0,step.duration);anim.seated=1-t;anim.floor=1-t;
  }else if(step.pose==='standfloor'){
   const t=T.MathUtils.smoothstep(step.elapsed,0,step.duration);anim.seated=1-t;anim.floor=1-t;
  }else if(step.pose==='stand'){
   const t=T.MathUtils.smoothstep(step.elapsed,0,step.duration);crow.position.lerpVectors(LIB.seat,LIB.approach,t);anim.seated=1-t;
  }else if(step.pose==='rest'&&crow.position.distanceTo(BEDSIDE)<.6){anim.seated=1;crow.rotation.y=Math.PI/2;crow.position.x=-10.95;crow.position.z=-10.0;
  }else if(step.pose==='objectSit'){anim.seated=1;crow.rotation.y=Math.PI;
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
if(anim.pose==='objectSit'&&!moving)crow.position.y=(anim.desired?.posture?.height||.49)-.77;
if(anim.pose==='objectLie'&&!moving){const p=anim.desired.posture;crow.position.set(p.x,p.height+.25,p.z+.65);crow.rotation.set(-Math.PI/2,0,0);anim.objectLying=true;}
else if(anim.objectLying){anim.objectLying=false;crow.rotation.x=0;}
const inBed=anim.pose==='sleep'&&!moving&&(anim.inBed||crow.position.distanceTo(BEDSIDE)<.6);
if(inBed){anim.inBed=true;crow.position.set(-11.5,.82,-9.25);crow.rotation.set(-Math.PI/2,0,0);
 for(let i=0;i<2;i++){legs[i].rotation.x=0;knees[i].rotation.x=0;arms[i].rotation.x=0;elbows[i].rotation.x=0}}
else if(anim.inBed){anim.inBed=false;crow.rotation.x=0;crow.position.set(BEDSIDE.x,0,BEDSIDE.z);}
blanket.visible=inBed;
torso.scale.y=1+Math.sin(anim.elapsed*1.8)*.008;edda.rotation.y=Math.sin(anim.elapsed*.3)*.25;
heldBook.visible=anim.book;if(shelfBook)shelfBook.visible=!anim.book;heldAxe.visible=anim.pose==='fell_tree'&&!moving;bow.visible=anim.pose==='practise'&&!anim.book&&!seated&&!heldAxe.visible;
const turn=anim.elapsed%24;pagePivot.rotation.z=anim.pose.startsWith('reading')&&turn<1.8?Math.PI*T.MathUtils.smoothstep(turn,0,1.8):0;
if(anim.pose==='practise'&&!moving){arms[0].rotation.x=-1.25;arms[1].rotation.x=-1.1;elbows[1].rotation.x=-.8;}
if(heldAxe.visible){arms[1].rotation.x=-.75+Math.sin(anim.elapsed*2)*.55;elbows[1].rotation.x=-.4;}
if(['eat','drink'].includes(anim.pose)&&!moving){arms[1].rotation.x=-1.25;elbows[1].rotation.x=-1.2+Math.sin(anim.elapsed*1.2)*.12;headPivot.rotation.x=.08;}
if(anim.pose==='inspect'&&!moving){headPivot.rotation.x=.38;arms[1].rotation.x=-.9;elbows[1].rotation.x=-.4+Math.sin(anim.elapsed*1.5)*.08;}
if((anim.pose==='gather'||anim.pose==='garden')&&!moving){const bend=.5+Math.sin(anim.elapsed*1.4)*.25;arms[0].rotation.x=-bend;arms[1].rotation.x=-bend;headPivot.rotation.x=.3;}
if(anim.pose==='craft'&&!moving){arms[1].rotation.x=-.8+Math.sin(anim.elapsed*4)*.12;elbows[1].rotation.x=-.5;headPivot.rotation.x=.18;}
if(anim.pose==='interact'&&!moving){arms[1].rotation.x=-.8+Math.sin(anim.elapsed*3)*.12;elbows[1].rotation.x=-.5;headPivot.rotation.x=.18;}
heldHarp.visible=anim.pose==='play_music'&&!moving;
if(anim.pose==='play_music'&&!moving){arms[0].rotation.x=-.9+Math.sin(anim.elapsed*5)*.1;arms[1].rotation.x=-.75+Math.sin(anim.elapsed*4.3+1)*.12;elbows[0].rotation.x=-.6;elbows[1].rotation.x=-.7;headPivot.rotation.x=.15;}
if(anim.pose==='ponder'&&!moving){headPivot.rotation.x=.12+Math.sin(anim.elapsed*.35)*.05;arms[1].rotation.x=-.5;elbows[1].rotation.x=-1.1;}
if(anim.pose==='observe'&&!moving)headPivot.rotation.y=Math.sin(anim.elapsed*.2)*.35;else headPivot.rotation.y=0;
crow.visible=true;if(inBed){headPivot.rotation.set(0,0,0);torso.scale.y=1+Math.sin(anim.elapsed*.9)*.02;}
sky.frame();renderer.render(scene,camera);requestAnimationFrame(frame)}
$('loading').remove();refresh();setInterval(refresh,2500);requestAnimationFrame(frame);
