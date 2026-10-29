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
  fell_tree:'felling a tree',craft:'carving',plan:'drafting a plan',construct:'building',move_object:'carrying something',resume_work:'returning to his work'};
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
  const key=JSON.stringify([s.decisions,s.pending&&s.pending.start,(s.diary||[]).length,s.interests,(s.personality_notes||[]).length,s.affect,s.current_intention,s.clock&&s.clock.date]);
  if(key===last)return;last=key;
  if(s.clock)$('diaryDate').textContent=`${s.clock.date} · ${s.clock.time}${s.twin?' · twin clock':' · UK time'}`;
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
  for(const [topic,score] of items){
   box.append(el('div',`${topic} · ${score>0?'drawn to':'put off by'} (${score})`));
   const bar=el('div',undefined,'bar'+(score<0?' neg':''));const fill=el('i');fill.style&&(fill.style.width=Math.min(100,Math.abs(score)*10)+'%');bar.append(fill);box.append(bar);
  }
  if(!items.length)box.append(el('p','No interests have formed yet.','muted'));
  const self=$('diarySelf');self.replaceChildren();
  for(const n of (s.personality_notes||[]).slice(-6).reverse())self.append(el('p','“'+n.text+'”','thought'));
  if(!(s.personality_notes||[]).length)self.append(el('p','He has not described himself yet.','muted'));
 }
 function open(show){const d=$('diary');if(!d)return;d.hidden=!show;if(show&&document.pointerLockElement)document.exitPointerLock?.();}
 function toggle(){open($('diary').hidden);}
 return {update,open,toggle};
}
