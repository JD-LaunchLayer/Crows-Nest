// His journal (Tab): a calmer, longer view of how Crow is, what he thinks, wants and holds.
// Read-only. Everything shown comes from his saved state; the summary sentence is
// assembled from those values by fixed rules, not written by a model.
export function createDiary({document}){
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
  fell_tree:'felling a tree',craft:'carving',plan:'drafting a plan',construct:'building',move_object:'carrying something',resume_work:'returning to his work',interact:'working with an object',browse:'browsing the web',talk:'talking with Edda',trade:'at the trading post',use_item:'using something'};
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
 function update(s){
  if(!$('diary'))return;
  const key=JSON.stringify([s.beliefs&&s.beliefs.length,s.beliefs&&s.beliefs.at(-1),s.stories&&s.stories.length,s.stories&&s.stories.at(-1)&&s.stories.at(-1).count,s.threads,s.promises,s.keeper,s.trading,s.possessions,s.decisions,s.pending&&s.pending.start,(s.diary||[]).length,s.interests,s.interest_history,(s.personality_notes||[]).length,s.affect,s.current_intention,s.clock&&s.clock.date]);
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
 function open(show){const d=$('diary');if(!d)return;d.hidden=!show;if(show&&document.pointerLockElement)document.exitPointerLock?.();}
 function toggle(){open($('diary').hidden);}
 return {update,open,toggle};
}
