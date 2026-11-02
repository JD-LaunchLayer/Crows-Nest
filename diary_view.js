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
 // Headlines: what is happening now and in his day so far, in a few short lines. The full journal is one click away.
 function headlines(s){
  const out=[],today=(s.memories||[]).filter(m=>m.day===s.day),done=today.filter(m=>m.kind==='experience'),short=(t,n=110)=>{t=String(t||'').replace(/\s+/g,' ').trim();const cut=t.search(/[.;](\s|$)/);t=cut>20&&cut<n?t.slice(0,cut):t;return t.length>n?t.slice(0,n-1)+'…':t};
  const aff=s.affect||{},body=bodyWords(s.body);
  out.push(['Right now',`${s.pending?(VERB[s.action]||s.action):'deciding what to do'} · ${mood(aff.valence||0,aff.arousal||0)} · ${body.length?body.join(', '):'body fine'}`]);
  if(s.current_intention)out.push(['Aiming for',short(s.current_intention,140)]);
  const counts={};for(const m of done)counts[m.action]=(counts[m.action]||0)+1;
  out.push(['His day so far',done.length?`${done.length} things done: `+Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,4).map(([a,n])=>`${VERB[a]||a} ${n}`).join(', '):'just begun']);
  const hi=[];const seenBefore=new Set((s.memories||[]).filter(m=>m.kind==='experience'&&m.day<s.day).map(m=>m.action));
  for(const m of done){const r=m.world_result||{};
   if(!seenBefore.has(m.action)&&!hi.some(h=>h.startsWith('First')))hi.push(`First time ${VERB[m.action]||m.action}`);
   if(['observe','explore'].includes(m.action)&&r.findings?.filter?.(f=>f.new).length)hi.push(`Noticed ${r.findings.filter(f=>f.new).length} new thing${r.findings.filter(f=>f.new).length>1?'s':''} (${m.time})`);
   if(['talk','trade','play_music','garden','plant_tree','craft','practise','fell_tree','browse','read'].includes(m.action))hi.push(`${m.time} · ${short(m.event,100)}`);
  }
  const edges=done.filter(m=>/has been seen before|can be made out in|is not in /.test(m.event||'')).length;if(edges)hi.push(`Told ${edges}× today that there was nothing new where he looked`);
  out.push(['Highlights',hi.length?hi.slice(-6):['nothing out of the ordinary']]);
  const thought=(s.diary||[]).at(-1);if(thought)out.push(['Latest thought',`“${short(thought.text,150)}”`]);
  const watch=[],p=s.provisions||{};
  if((p.pantry||0)<1)watch.push(`no ready food${(p.berries||0)<10?`, ${(p.berries||0).toFixed(0)} servings of fruit left`:''}`);
  if(s.trading)watch.push(`${s.trading.credit||0} trade credit`);
  watch.push(s.keeper?.talks?`talked with Edda ${s.keeper.talks}×`:'has not met Edda');
  const gaps=(s.world_gaps||[]).filter(g=>String(g.last||'').slice(0,10)===String(s.clock?.iso||'').slice(0,10));if(gaps.length)watch.push(`${gaps.length} place${gaps.length>1?'s':''} where the world ran out today`);
  out.push(['Worth knowing',watch.join(' · ')]);
  const box=$('diaryHeadlines');if(!box)return;box.replaceChildren();
  for(const [k,v] of out){if(Array.isArray(v)){const h=el('p');h.append(el('b',k+':'));box.append(h);const ul=el('ul');for(const x of v)ul.append(el('li',x));box.append(ul);}else{const pEl=el('p');const b=el('b',k+': ');pEl.append(b,document.createTextNode(v));box.append(pEl);}}
 }
 if($('diaryMore'))$('diaryMore').onclick=()=>{const pages=$('diaryPages');const brief=pages.classList.toggle('brief');$('diaryMore').textContent=brief?'Show the full journal':'Show headlines only';};
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
   if(t){trade.append(el('p',`Trade credit: ${t.credit}`));
    const owned=Object.entries(s.possessions||{}).filter(([,n])=>n);trade.append(el('p',owned.length?'He owns: '+owned.map(([k,n])=>n>1?`${k} ×${n}`:k).join(', '):'He has not bought anything yet.','muted'));
    if((t.requests||[]).length){trade.append(el('p','Things he has asked the post to stock:'));for(const r of [...t.requests].reverse().slice(0,8))trade.append(el('p',`“${r.item}”${r.times>1?` (asked ${r.times} times)`:''}`,'thought'));}
    else trade.append(el('p','He has not asked for anything to be stocked.','muted'));
    const last=(t.ledger||[]).at(-1);if(last)trade.append(el('p','Last at the post: '+last.text,'muted'));}}
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
    for(const f of k.favours||[])people.append(el('p',`Open favour (${f.id}): ${f.task} · ${f.minutes} min · ${f.credit} credit`,'muted'));}}
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
  const p=s.provisions||{};L.push(`Food: pantry ${(p.pantry??0).toFixed(1)} · fruit ${(p.berries??0).toFixed(1)} · water ${(p.water_litres??0).toFixed(1)} L · credit ${s.trading?.credit??0} · owns: ${Object.entries(s.possessions||{}).filter(([,n])=>n).map(([k,n])=>n>1?k+'×'+n:k).join(', ')||'nothing'}`);
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
