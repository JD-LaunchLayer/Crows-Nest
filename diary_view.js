// His journal (Tab): a calmer, longer view of how Crow is, what he thinks, wants and holds.
// Read-only. Everything shown comes from his saved state; the summary sentence is
// assembled from those values by fixed rules, not written by a model.
export function createDiary({document,player=null}){
 const $=id=>document.getElementById(id);let last='';
 function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
 function mood(v,a){
  const tone=v>.35?'contented':v>.1?'mildly positive':v<-.35?'troubled':v<-.1?'a little low':'even';
  const pace=a>.6?'and stirred up':a>.3?'and alert':'and calm';
  return `${tone} ${pace}`;
 }
 function bodyWords(b){
  const out=[];if(!b)return out;
  if(b.reserve<35&&b.stomach<8)out.push('hungry');else if(b.reserve<65&&b.stomach<8)out.push('a bit hungry');
  if(b.hydration<35)out.push('very thirsty');else if(b.hydration<65)out.push('thirsty');
  if(b.sleep_debt>8)out.push('very sleepy');else if(b.sleep_debt>4)out.push('getting sleepy');
  if(b.exertion>.45)out.push('physically tired');
  return out;
 }
 const VERB={rest:'resting',sleep:'asleep',eat:'eating',drink:'drinking',observe:'watching the woodland',reflect:'thinking quietly',
  explore:'exploring',practise:'practising archery',read:'reading',inspect:'examining something',gather:'gathering materials',
  fell_tree:'felling a tree',craft:'carving',plan:'drafting a plan',construct:'building',move_object:'carrying something',resume_work:'returning to his work',interact:'working with an object',browse:'browsing the web',talk:'talking with Edda',trade:'at the trading post',use_item:'using something',garden:'gardening',plant_tree:'planting a tree',play_music:'playing the harp',hunt:'out with the bow',butcher:'cutting up a carcass',preserve:'smoking meat',put_out_food:'putting food out and waiting quietly'};
 function summary(s){
  const parts=[];const twin=s.twin;
  parts.push(s.pending?`He is ${VERB[s.action]||s.action}.`:'He is between activities.');
  const aff=s.affect||{};parts.push(`He seems ${mood(aff.valence||0,aff.arousal||0)}.`);
  const body=bodyWords(s.body);parts.push(body.length?`His body: ${body.join(', ')}.`:'Nothing in his body is pressing.');
  if(s.current_intention)parts.push(`What he is aiming for: “${s.current_intention}”.`);
  if(s.next_step)parts.push(`He is thinking of next: “${s.next_step}”.`);
  const started=(s.memories||[]).filter(m=>m.kind==='started').slice(-20);const counts={};
  for(const m of started)counts[m.action]=(counts[m.action]||0)+1;
  const top=Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([a,n])=>`${VERB[a]||a} (${n})`);
  if(top.length)parts.push(`Lately he has mostly been ${top.join(', ')} out of his last ${started.length} choices.`);
  const wishes=(s.wishes||[]).filter(w=>w.status!=='withdrawn');
  if(wishes.length)parts.push(`He has expressed ${wishes.length} wish${wishes.length>1?'es':''}; the most recent is “${wishes.at(-1).text}”.`);
  if(twin)parts.push('This is the time-lapse twin, living on a fast-forward clock.');
  return parts.join(' ');
 }
 // Crow today (v0.27): the friendly page. What he's doing, how he seems, what he hopes for, in plain words.
 // Everything comes from his saved state by fixed rules; nothing here is written by a model. The detailed notes are one click away.
 function money(x){const t=Math.round((+x||0)*10),g=Math.floor(Math.abs(t)/10),sv=Math.abs(t)%10;const out=[g?g+' gold':'',sv?sv+' silver':''].filter(Boolean).join(' ');return (t<0?'-':'')+(out||'nothing');}
 const DOING={rest:'having a quiet rest in his cabin',sleep:'fast asleep in his cabin',eat:'having something to eat',drink:'having a drink at the spring',
  observe:'watching the woods closely',reflect:'sitting and thinking',explore:'out walking in the woods',practise:'practising his archery',read:'reading in the reading cabin',
  inspect:'taking a close look at something',gather:'gathering wood',fell_tree:'felling a tree',craft:'carving something',plan:'sketching out a plan',construct:'building',
  move_object:'carrying something across the clearing',interact:'working on something at the bench',browse:'at the café, searching the web',talk:'chatting with Edda',
  trade:'at the trading post',use_item:'using one of his things',garden:'pottering in the garden',plant_tree:'planting a young tree',play_music:'playing his harp',
  hunt:'out with his bow',butcher:'cutting up a carcass',preserve:'smoking meat over a slow fire',put_out_food:'putting a little food out and waiting quietly',resume_work:'getting back to his work'};
 const DID={rest:'had a rest',sleep:'slept',eat:'had something to eat',drink:'had a drink at the spring',observe:'watched the woods',reflect:'sat and thought',
  explore:'went for a walk in the woods',practise:'practised archery',read:'did some reading',inspect:'looked closely at something',gather:'gathered wood',fell_tree:'felled a tree',
  craft:'carved something',plan:'sketched a plan',construct:'did some building',move_object:'carried something',interact:'worked on something',browse:'searched the web at the café',
  talk:'chatted with Edda',trade:'went to the trading post',use_item:'used one of his things',garden:'worked in the garden',plant_tree:'planted a young tree',play_music:'played his harp',
  hunt:'went out with his bow',butcher:'cut up a carcass',preserve:'smoked some meat',put_out_food:'put a little food out and waited',resume_work:'got back to his work'};
 function feelWords(v,a){const tone=v>.35?'happy and content':v>.1?'in good spirits':v<-.35?'quite down':v<-.1?'a little low':'steady';return tone+(a>.6?', if a bit wound up':a>.3?' and alert':' and calm');}
 function bodyFriendly(b){const out=[];if(!b)return out;
  if(b.reserve<35&&b.stomach<8)out.push("he's hungry");else if(b.reserve<65&&b.stomach<8)out.push("he's a bit peckish");
  if(b.hydration<35)out.push("he's very thirsty");else if(b.hydration<65)out.push("he's thirsty");
  if(b.sleep_debt>8)out.push("he's really tired");else if(b.sleep_debt>4)out.push("he's getting sleepy");
  if(b.exertion>.45)out.push('his muscles are tired from work');return out;}
 const tidy=t=>String(t||'').replace(/\s*\((?:threads?|promises?)\s*[\d–\-, and]+\)/gi,'').replace(/\b(?:threads?|promises?)\s*\d+(?:\s*[–\-]\s*\d+)?(?:\s*(?:,|and)\s*\d+)*\s*/gi,'').replace(/\s+/g,' ').trim();
 const first=(t,n=150)=>{t=tidy(t);const c=t.search(/[.;](\s|$)/);t=c>15&&c<n?t.slice(0,c):t;return t.length>n?t.slice(0,n-1)+'…':t};
 function detail(m){const r=m.world_result||{},ev=String(m.event||'');
  if(m.action==='eat'){const f=ev.match(/serving of (.+?) from/);return f?`(${f[1]})`:'';}
  if(['observe','explore'].includes(m.action)){const a=(r.findings||[]).map(f=>f.text||'').find(t=>/ bird | animal /.test(' '+t+' '));if(a)return '— spotted '+first(a,120).replace(/^A /,'a ').replace(/ is .*/,'');const n=(r.findings||[]).filter(f=>f.new).length;return n?`— noticed ${n} new thing${n>1?'s':''}`:'';}
  if(m.action==='read'||m.action==='browse'){const t=(m.source||{}).title;return t?`(${t})`:'';}
  if(['trade','hunt','butcher','preserve','put_out_food','garden','plant_tree','play_music','craft'].includes(m.action))return '— '+first(ev,120).toLowerCase().replace(/^(did|finished|bought|sold|played|picked|put|shot|walked|gutted|kept|sowed|watered|pulled|planted)/i,x=>x.toLowerCase());
  return '';}
 function headlines(s){
  const box=$('diaryHeadlines');if(!box)return;box.replaceChildren();
  const para=(t,cls)=>box.append(el('p',t,cls)),head=t=>box.append(el('h3',t));
  const aff=s.affect||{},body=bodyFriendly(s.body);
  para(`${s.pending?`Crow is ${DOING[s.action]||s.action}.`:'Crow is deciding what to do next.'} He seems ${feelWords(aff.valence||0,aff.arousal||0)}${body.length?', and '+body.join(', '):''}.`,'lead');
  if(s.current_intention)para(`What he's hoping to do: “${first(s.current_intention,200)}”`);
  if(s.next_step&&s.next_step!==s.current_intention)para(`After that, he's thinking: “${first(s.next_step,200)}”`,'muted');
  // His day so far, with runs of the same thing gathered together.
  const today=(s.memories||[]).filter(m=>m.kind==='experience'&&m.day===s.day);
  head('His day so far');
  if(!today.length)para('His day has only just begun.','muted');
  const groups=[];for(const m of today){const g=groups.at(-1);if(g&&g.action===m.action&&!['talk','trade','eat'].includes(m.action))g.items.push(m);else groups.push({action:m.action,items:[m]});}
  const ul=el('ul');for(const g of groups.slice(-10)){const a=g.items[0],z=g.items.at(-1);
   const when=g.items.length>1?`${a.time}–${z.time}`:a.time;const what=(DID[g.action]||g.action)+(g.items.length>1?` (${g.items.length} times)`:'');
   ul.append(el('li',`${when} · ${what} ${g.items.length===1?detail(a):''}`.trim()));}
  if(groups.length)box.append(ul);
  // How he's been feeling, in his own words.
  const thoughts=(s.diary||[]).slice(-3).reverse();
  if(thoughts.length){head("How he's been feeling");for(const d of thoughts)para(`${String(d.at||'').slice(11,16)} · “${first(d.text,220)}”`,'thought');}
  // Wishes, newest first, each once.
  const ws=[];for(const w of [...(s.wishes||[])].filter(w=>w.status!=='withdrawn').reverse()){if(!ws.some(x=>x.text===w.text))ws.push(w);if(ws.length>=5)break;}
  if(ws.length){head("What he's wishing for");const wl=el('ul');for(const w of ws)wl.append(el('li',`“${first(w.text,180)}”${(w.mentions||1)>=10?' — something he keeps coming back to':''}`));box.append(wl);}
  // On his mind: things left open and promises, in plain words.
  const open=(s.threads||[]).filter(t=>t.status==='open').slice(-3).reverse(),prom=(s.promises||[]).filter(p=>p.status==='open').slice(-3).reverse();
  if(open.length||prom.length){head("On his mind");
   for(const t of open){para(`“${first(t.text,200)}”`,'thought');if(t.world_note)para('A note from the world: '+t.world_note,'muted');}
   for(const p of prom){para(`He promised ${p.to.split(' ')[0]}: “${first(p.text,200)}”`,'thought');if(p.world_note)para('A note from the world: '+p.world_note,'muted');}}
  const notes=(s.personality_notes||[]).slice(-2).reverse();
  if(notes.length){head("What he's noticed about himself");for(const n of notes)para(`“${first(n.text,220)}”`,'thought');}
  // Edda.
  const k=s.keeper;if(k&&k.talks){head('Him and Edda');
   const feel=k.warmth>.5?'genuinely fond of him':k.warmth>.3?'fond of him':k.warmth>.05?'warming to him':k.warmth<-.3?'wary of him':k.warmth<-.05?'a little cool towards him':'still making her mind up about him';
   para(`They've talked ${k.talks} time${k.talks===1?'':'s'}, and Edda seems ${feel}.`);
   const talk=[...(s.memories||[])].reverse().find(m=>m.world_result&&m.world_result.conversation);
   if(talk)for(const c of talk.world_result.conversation.slice(0,2))para(`${c.who}: “${first(c.text,220)}”`,'thought');}
  // Birds that are getting used to him.
  const looks=Object.fromEntries((s.birds_view||[]).map(b=>[b.id,b.look]).filter(([,l])=>l));
  const tame=Object.entries(s.wildlife?.trust||{}).filter(([id,t])=>t>=.1&&looks[id]).sort((a,b)=>b[1]-a[1]).slice(0,3);
  if(tame.length){head('Birds getting used to him');const bl=el('ul');
   for(const [id,t] of tame)bl.append(el('li',`The ${looks[id]} ${t<.3?'is starting to get used to him':t<.6?'comes a little closer when he is quiet':t<.85?'will feed near him':'will take food from his hand'}.`));box.append(bl);}
  // Purse and pantry.
  const pv=s.provisions||{};head('Purse and pantry');
  para(`He has ${money(s.trading?.credit||0)} in his purse and ${Math.round((pv.pantry||0)*10)/10} serving${(pv.pantry||0)===1?'':'s'} of food in the chest${(pv.berries||0)>=1?`, with fruit on the bushes`:''}.`);
 }
 if($('diaryMore'))$('diaryMore').onclick=()=>{const pages=$('diaryPages');const brief=pages.classList.toggle('brief');$('diaryMore').textContent=brief?'Show the detailed notes':'Back to Crow today';};
 function update(s){
  latest=s;
  if(!$('diary'))return;
  headlines(s);
  const key=JSON.stringify([s.beliefs&&s.beliefs.length,s.beliefs&&s.beliefs.at(-1),s.stories&&s.stories.length,s.stories&&s.stories.at(-1)&&s.stories.at(-1).count,s.threads,s.promises,s.keeper,s.trading,s.world_gaps,s.music&&s.music.sessions,s.possessions,s.decisions,s.pending&&s.pending.start,(s.diary||[]).length,s.interests,s.interest_history,(s.personality_notes||[]).length,s.affect,s.current_intention,s.clock&&s.clock.date]);
  if(key===last)return;last=key;
  if(s.clock)$('diaryDate').textContent=`${s.clock.date} · ${s.clock.time}${s.twin?' · twin clock':s.crow_clock?' · Crow\'s own time':' · UK time'}`;
  $('diaryBadge').textContent=s.twin?'CROW · TIME-LAPSE TWIN':'CROW\'S JOURNAL';
  $('diaryNow').textContent=summary(s);
  const events=new Map((s.memories||[]).map(m=>[m.id,m]));
  const thoughts=$('diaryThoughts');thoughts.replaceChildren();
  for(const d of (s.diary||[]).slice(-10).reverse()){
   const p=el('p',undefined,'thought');p.append(el('span',`${(d.at||'').slice(0,16).replace('T',' ')}${events.get(d.source_id)?' · after: '+events.get(d.source_id).event.slice(0,110):''}`));
   p.append(document.createTextNode(d.text));thoughts.append(p);
  }
  if(!(s.diary||[]).length)thoughts.append(el('p','No reflections recorded yet.','muted'));
  const box=$('diaryInterests');box.replaceChildren();
  const items=Object.entries(s.interests||{}).sort((a,b)=>Math.abs(b[1])-Math.abs(a[1])).slice(0,10);
  const histories=Object.values(s.interest_history||{}).filter(x=>x.episodes?.length).sort((a,b)=>b.episodes.at(-1).source_id-a.episodes.at(-1).source_id).slice(0,10);
  for(const h of histories){
   const es=h.episodes,choices=new Set(es.map(e=>e.choice_id).filter(i=>i!=null));
   box.append(el('p',h.topic));
   box.append(el('p',`${es.length} recorded experiences · ${choices.size} separate choices · ${es.filter(e=>e.fresh).length} with new evidence`,'muted'));
   for(const e of es.slice(-3))box.append(el('p',`“${e.feeling}” · ${e.action} · Experience ${e.source_id}`,'thought'));
  }
  if(!histories.length){
   for(const [topic,score]of items)box.append(el('p',`${topic} · ${score>0?'drawn to':'put off by'} · earlier reported preference; no detailed trail recorded yet`,'muted'));
   if(!items.length)box.append(el('p','No interest history recorded yet.','muted'));
  }
  const trade=$('diaryTrade');if(trade){trade.replaceChildren();const t=s.trading;
   if(t){trade.append(el('p',`In his purse: ${money(t.credit)}`));
    const owned=Object.entries(s.possessions||{}).filter(([,n])=>n);trade.append(el('p',owned.length?'He owns: '+owned.map(([k,n])=>n>1?`${k} ×${n}`:k).join(', '):'He has not bought anything yet.','muted'));
    if((t.requests||[]).length){trade.append(el('p','Things he has asked the post to stock:'));for(const r of [...t.requests].reverse().slice(0,8))trade.append(el('p',`“${r.item}”${r.times>1?` (asked ${r.times} times)`:''}`,'thought'));}
    else trade.append(el('p','He has not asked for anything to be stocked.','muted'));
    const last=(t.ledger||[]).at(-1);if(last)trade.append(el('p','Last at the post: '+last.text,'muted'));}}
  const shelves=$('diaryShelves');if(shelves){shelves.replaceChildren();const t=s.trading;
   if(t){const stock=Object.entries(t.stock||{});const inStock=stock.filter(([,v])=>v.qty>0),out=stock.filter(([,v])=>!(v.qty>0));
    shelves.append(el('p',`In stock: ${inStock.length} lines · sold out: ${out.length}`,'muted'));
    for(const [,v] of inStock.sort((a,b)=>a[1].name.localeCompare(b[1].name)))shelves.append(el('p',`${v.name} — ${Math.round(v.qty*100)/100} left · ${money(v.price)}`));
    if(out.length)shelves.append(el('p','Sold out: '+out.map(([,v])=>v.name).join(', '),'muted'));
    const today=(s.clock?.iso||'').slice(0,10),done=t.jobs_done||{};
    const sweep=done.sweep_post?.slice(0,10)===today?'done today':'needs doing today';
    const crates=t.last_delivery&&!(done.carry_crates&&done.carry_crates>=t.last_delivery)?'crates waiting from the last delivery':'no crates until the next delivery';
    shelves.append(el('p',`Jobs: sweeping ${sweep} · ${crates}`));
    const fav=s.keeper?.favours||[];if(fav.length)shelves.append(el('p','Favours agreed with Edda: '+fav.map(f=>`${f.task} (${money(f.credit)})`).join('; '),'muted'));
    if(t.last_delivery)shelves.append(el('p','Last delivery: '+t.last_delivery.slice(0,16).replace('T',' '),'muted'));
    for(const l of (t.ledger||[]).slice(-6).reverse())shelves.append(el('p',`${(l.at||'').slice(5,16).replace('T',' ')} · ${l.text}`,'thought'));}
   else shelves.append(el('p','The trading post has not opened yet.','muted'));}
  const musicBox=$('diaryMusic');if(musicBox){musicBox.replaceChildren();const pieces=[...(s.music?.pieces||[])].reverse();
   if(s.music&&pieces.length)musicBox.append(el('p',`${Math.round((s.music.hours||0)*10)/10} hours at the harp · ${s.music.sessions||0} sessions`,'muted'));
   for(const pc of pieces.slice(0,10)){const box=el('div',undefined,'story');
    box.append(el('p',`${pc.title}${pc.source==='composed'?' · his own':' · from '+pc.source+(pc.by&&pc.by!=='traditional'?' ('+pc.by+')':'')}`));
    box.append(el('p',`played ${pc.times_played} time${pc.times_played===1?'':'s'}${pc.revisions?` · revised ${pc.revisions}×`:''}${pc.last_slips!=null?` · last time ${pc.last_slips} slip${pc.last_slips===1?'':'s'}, ${pc.last_timing}`:''}`,'muted'));
    if(player){const row=el('p');
     if(pc.last_played){const b=el('button','As he last played it','secondary');b.onclick=()=>{player.setEnabled(true);player.play(pc.last_played,pc.tempo)};row.append(b,document.createTextNode(' '));}
     const w=el('button','As written','secondary');w.onclick=()=>{player.setEnabled(true);player.play(pc.notes,pc.tempo)};row.append(w);box.append(row);}
    musicBox.append(box);}
   if(!pieces.length)musicBox.append(el('p',s.possessions?.harp?'He has not played anything yet.':'He has no instrument.','muted'));}
  const gapBox=$('diaryGaps');if(gapBox){gapBox.replaceChildren();
   const WORDS={seen_all:'Had seen everything there',not_found:'Looked for something not there',not_here:'Looked in the wrong place for',unanswered:'Question not answered by the'};
   const gaps=[...(s.world_gaps||[])].sort((a,b)=>b.times-a.times||String(b.last).localeCompare(String(a.last))).slice(0,12);
   for(const g of gaps){const what=g.kind==='unanswered'?`${WORDS[g.kind]} ${g.target}`:`${WORDS[g.kind]||g.kind}${g.target?': '+g.target.replace('_',' '):''}`;
    gapBox.append(el('p',`${what} · ${g.times} time${g.times===1?'':'s'} · last ${String(g.last||'').slice(0,16).replace('T',' ')}`));
    for(const f of (g.focuses||[]).slice(-2))gapBox.append(el('p','“'+f+'”','thought'));}
   if(!gaps.length)gapBox.append(el('p','He has not reached the edge of anything yet.','muted'));}
  const people=$('diaryPeople');if(people){people.replaceChildren();const k=s.keeper;
   const talk=[...(s.memories||[])].reverse().find(m=>m.world_result&&m.world_result.conversation);
   if(talk){people.append(el('p',`Last talked: ${(talk.at||'').slice(0,16).replace('T',' ')}`,'muted'));
    for(const c of talk.world_result.conversation)people.append(el('p',`${c.who}: “${c.text}”`,'thought'));
    if(talk.world_result.text)people.append(el('p',talk.world_result.text,'muted'));}
   else people.append(el('p','They have not spoken yet.','muted'));
   if(k){const feel=k.warmth>.3?'fond of him':k.warmth>.05?'warming to him':k.warmth<-.3?'wary of him':k.warmth<-.05?'a little cool towards him':'undecided about him';
    people.append(el('p',`Edda seems ${feel}. They have talked ${k.talks} time${k.talks===1?'':'s'}.`));
    for(const n of (k.notes||[]).slice(-5).reverse())people.append(el('p','Edda: “'+n.text+'”','thought'));
    for(const f of k.favours||[])people.append(el('p',`Open favour (${f.id}): ${f.task} · ${f.minutes} min · ${money(f.credit)}`,'muted'));}}
  const stories=$('diaryStories');if(stories){stories.replaceChildren();
   const shown=(s.stories||[]).filter(x=>x.count>1).sort((a,b)=>(b.updated_hours||0)-(a.updated_hours||0)).slice(0,6);
   for(const st of shown){const box=el('div',undefined,'story');box.append(el('p',`${st.title}`));
    box.append(el('p',`${st.stage} · ${st.count} steps${st.feel&&st.feel.last?' · lately felt like '+st.feel.last:''}`,'muted'));
    const list=el('ol');for(const step of st.steps.slice(-6)){const li=el('li');li.append(el('span',(step.at||'').slice(0,16).replace('T',' ')+' · '));li.append(document.createTextNode(step.text+(step.because?' — because: '+step.because:'')));list.append(li)}
    box.append(list);stories.append(box)}
   if(!shown.length)stories.append(el('p','No story has more than one step yet.','muted'))}
  const bel=$('diaryBeliefs');if(bel){bel.replaceChildren();const list=(s.beliefs||[]);
   for(const b of list.filter(b=>b.status!=='revised').slice(-8).reverse())bel.append(el('p',`${b.statement} · ${b.status}, ${b.observations} times`,'thought'));
   for(const b of list.filter(b=>b.status==='revised').slice(-3).reverse())bel.append(el('p',`Used to be: “${b.statement}”`,'muted'));
   if(!list.length)bel.append(el('p','Not enough experience for any pattern yet.','muted'))}
  const open=$('diaryOpen');if(open){open.replaceChildren();
   const threads=(s.threads||[]).filter(t=>t.status==='open'),promises=(s.promises||[]).filter(p=>p.status==='open');
   for(const t of threads.slice(-6).reverse())open.append(el('p',`“${t.text}” · at ${String(t.place||'').replace('_',' ')}`,'thought'));
   for(const p of promises.slice(-6).reverse())open.append(el('p',`Promised ${p.to}: “${p.text}”`,'thought'));
   const followed=(s.threads||[]).filter(t=>t.status==='followed').slice(-2);for(const t of followed)open.append(el('p',`Followed up: “${t.text}”`,'muted'));
   if(!threads.length&&!promises.length&&!followed.length)open.append(el('p','Nothing left open.','muted'))}
  const self=$('diarySelf');self.replaceChildren();
  for(const n of (s.personality_notes||[]).slice(-6).reverse())self.append(el('p','“'+n.text+'”','thought'));
  if(!(s.personality_notes||[]).length)self.append(el('p','He has not described himself yet.','muted'));
 }
 // A compact plain-text report of his recent life: the parts that change, without the long history sections.
 function report(s){
  const L=[],cut=(t,n=170)=>{t=String(t||'').replace(/\s+/g,' ').trim();return t.length>n?t.slice(0,n-1)+'…':t};
  const v=document.querySelector?.('meta[name="crow-version"]')?.content||'';
  L.push(`CROW REPORT · v${v} · ${s.clock?.date||''} ${s.clock?.time||''}${s.crow_clock?' (his own time)':''}`);
  L.push('','HOW HE IS',summary(s));
  const p=s.provisions||{};L.push(`Food: pantry ${(p.pantry??0).toFixed(1)} · fruit ${(p.berries??0).toFixed(1)} · water ${(p.water_litres??0).toFixed(1)} L · purse ${money(s.trading?.credit??0)} · owns: ${Object.entries(s.possessions||{}).filter(([,n])=>n).map(([k,n])=>n>1?k+'×'+n:k).join(', ')||'nothing'}`);
  {const lots=p.larder||[];if(lots.length){const by={};for(const l of lots)by[l.food]=(by[l.food]||0)+l.servings;L.push('Larder: '+Object.entries(by).map(([k,n])=>`${k} ${n.toFixed(1)}`).join(' · '));}
   const w=s.wildlife;if(w){const alive=(w.deer||[]).filter(d=>d.alive).length;const tr=Object.entries(w.trust||{}).filter(([,t])=>t>=.05).sort((a,b)=>b[1]-a[1]).slice(0,4);
    L.push(`Wildlife: ${alive} deer in the herd · hunts ${w.hunts||0} · carcasses waiting ${(w.carcasses||[]).length}`+(tr.length?' · birds trusting him: '+tr.map(([k,t])=>`${k} ${t.toFixed(2)}`).join(', '):''));}}
  const trees=Object.values(s.built_world?.trees||{}),standing=trees.filter(t=>t.stage==='standing'),near=standing.map(t=>Math.hypot(t.x,t.z)).sort((a,b)=>a-b)[0];
  L.push(`Woods: ${standing.length} standing · ${trees.filter(t=>t.stage==='felled').length} stumps · ${trees.filter(t=>t.stage==='young').length} planted · nearest tree ${near?Math.round(near):'-'} m from centre · fallen timber ${s.built_world?.sources?.wood?.stock??'-'} kg · wood carried ${s.materials??0} kg`);
  if(s.model_spend)L.push(`Model: spend today $${(s.model_spend.usd||0).toFixed(3)} · ${s.model_spend.calls||0} calls · ${s.model_spend.fallbacks||0} fallbacks${s.model_spend.last_fallback?' · last fallback: '+cut(s.model_spend.last_fallback,140):''}`);
  const started=(s.memories||[]).filter(m=>m.kind==='started').slice(-30),counts={};for(const m of started)counts[m.action]=(counts[m.action]||0)+1;
  L.push('Last 30 choices: '+Object.entries(counts).sort((a,b)=>b[1]-a[1]).map(([a,n])=>`${a} ${n}`).join(', '));
  L.push('','RECENT EVENTS (newest last)');
  for(const m of (s.memories||[]).filter(m=>m.kind==='experience').slice(-15))L.push(`- ${(m.at||'').slice(5,16).replace('T',' ')} ${m.action}: ${cut(m.event,190)}${m.reason?' | why: '+cut(m.reason,120):''}`);
  L.push('','RECENT THOUGHTS');for(const d of (s.diary||[]).slice(-8))L.push(`- ${(d.at||'').slice(5,16).replace('T',' ')} ${cut(d.text,160)}`);
  L.push('','STORIES');for(const st of (s.stories||[]).filter(x=>x.count>1&&x.stage!=='left').sort((a,b)=>(b.updated_hours||0)-(a.updated_hours||0)).slice(0,5))L.push(`- [${st.stage}, ${st.count} steps, ${st.feel?.last||'-'}] ${cut(st.title,140)}`);
  L.push('','LEFT OPEN');for(const t of (s.threads||[]).filter(t=>t.status==='open').slice(-5))L.push('- '+cut(t.text,160));
  for(const pr of (s.promises||[]).filter(p=>p.status==='open'))L.push(`- promised ${pr.to}: ${cut(pr.text,140)}`);
  L.push('','PATTERNS');for(const b of (s.beliefs||[]).filter(b=>b.status!=='revised').slice(-8))L.push(`- ${b.statement} (${b.status}, ${b.observations})`);
  L.push('','WISHES (most mentioned)');for(const x of [...(s.wishes||[])].filter(x=>x.status!=='withdrawn').sort((a,b)=>b.mentions-a.mentions).slice(0,5))L.push(`- ${cut(x.text,140)} ×${x.mentions}`);
  L.push('','SELF-NOTES');for(const n of (s.personality_notes||[]).slice(-4))L.push('- '+cut(n.text,160));
  const k=s.keeper;L.push('','EDDA & TRADE',`Talked ${k?.talks||0} times · warmth ${(k?.warmth||0).toFixed(2)} · last ledger: ${cut((s.trading?.ledger||[]).at(-1)?.text||'none',120)}`);
  const lastTalk=[...(s.memories||[])].reverse().find(m=>m.world_result&&m.world_result.conversation);if(lastTalk)L.push('Last talk: '+cut(lastTalk.world_result.conversation.map(c=>c.who+': '+c.text).join(' / '),400));
  {const st=Object.values(s.trading?.stock||{}).filter(v=>v.qty>0);if(st.length)L.push('Shelves: '+st.map(v=>`${cut(v.name,40)} ${Math.round(v.qty*100)/100}@${v.price}`).join(' · '));
   const dn=s.trading?.jobs_done||{};if(Object.keys(dn).length)L.push('Jobs last done: '+Object.entries(dn).map(([j,a])=>`${j} ${String(a).slice(5,16).replace('T',' ')}`).join(' · '));}
  L.push('','GARDEN');for(const b of (s.garden?.beds||[]))L.push(`- bed ${b.n}: ${b.crop||'empty'}${b.item?' ('+b.item+')':''} growth ${Math.round((b.growth||0)*100)}% health ${Math.round((b.health??1)*100)}%`);
  L.push('','WHERE THE WORLD RAN OUT (top)');for(const g of [...(s.world_gaps||[])].sort((a,b)=>b.times-a.times).slice(0,8))L.push(`- ${g.kind} ${g.target||''} ×${g.times}: ${cut((g.focuses||[]).at(-1)||'',120)}`);
  if(s.music?.pieces?.length){L.push('','MUSIC',`${(s.music.hours||0).toFixed(1)} h at the harp`);for(const pc of s.music.pieces.slice(-5))L.push(`- ${pc.title} (${pc.source}) ×${pc.times_played}, last slips ${pc.last_slips??'-'}`);}
  const tr=(s.practical?.trials||[]).at(-1);if(tr)L.push('','LAST CARVING',`${tr.method_id} · error ${tr.actual_error_mm} mm vs ${tr.target_error_mm} mm · ${tr.goal_met?'met':'not met'}`);
  const ar=(s.practical?.archery||[]).at(-1);if(ar)L.push('LAST ARCHERY',`${ar.on_target}/12 on target, ${ar.in_gold} gold, mean ${ar.mean_cm_from_centre} cm`);
  return L.join('\n');
 }
 let latest=null;
 async function copyReport(){
  if(!latest)return;const text=report(latest),b=$('diaryCopy');
  try{await navigator.clipboard.writeText(text);}
  catch(e){const t=document.createElement('textarea');t.value=text;document.body.append(t);t.select();try{document.execCommand('copy')}finally{t.remove()}}
  if(b){b.textContent='Copied';setTimeout(()=>{b.textContent='Copy report'},1600);}
 }
 if($('diaryCopy'))$('diaryCopy').onclick=copyReport;
 function open(show){const d=$('diary');if(!d)return;d.hidden=!show;if(show&&document.pointerLockElement)document.exitPointerLock?.();}
 function toggle(){open($('diary').hidden);}
 return {update,open,toggle,report};
}
