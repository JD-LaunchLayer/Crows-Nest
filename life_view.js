// Read-only evidence of bodily state, experiments and tested procedures.
export function createLifeView({document}){
 const $=id=>document.getElementById(id);let previous='';
 function line(parent,text,cls=''){const p=document.createElement('p');p.textContent=text;if(cls)p.className=cls;parent.append(p);return p;}
 function card(parent,title){const div=document.createElement('article');div.className='entry';line(div,title);parent.append(div);return div;}
 let mindKey='';
 const NAMES={life:'What mattered and what he believes',skills:'How to do things',world:'What the world allows'};
 function renderMind(mind){
  const box=$('mind');if(!box)return;const key=JSON.stringify(mind||{});if(key===mindKey)return;mindKey=key;box.replaceChildren();
  if(!mind||!Object.keys(NAMES).some(k=>(mind[k]||[]).length)){line(box,'Nothing consolidated yet. This happens after he sleeps.','muted');return;}
  for(const [k,title]of Object.entries(NAMES)){
   const items=[...(mind[k]||[])].sort((a,b)=>b.strength-a.strength);const div=card(box,`${title} · ${items.length}/24`);
   for(const e of items)line(div,`${'●'.repeat(Math.max(1,Math.min(5,Math.round(e.strength*4))))} ${e.text}${e.previous?.length?' (revised)':''}${e.contested?' (contested)':''}`);
   if(items.length)line(div,'Closest to fading: '+items.at(-1).text,'muted');
  }
  const lost=(mind.forgotten||[]).slice(-3).reverse();
  if(lost.length){const div=card(box,'Recently forgotten');for(const e of lost)line(div,e.text,'muted');}
 }
 function update(state){
  if(!state.body||!state.provisions)return;
  const b=state.body,signals=[];
  if(b.reserve<35&&b.stomach<8)signals.push('Persistent hunger.');else if(b.reserve<65&&b.stomach<8)signals.push('Some hunger.');
  if(b.stomach>35)signals.push('Feeling full.');else if(b.stomach>8)signals.push('Food is digesting.');
  if(b.hydration<35)signals.push('Strong thirst.');else if(b.hydration<65)signals.push('Noticeable thirst.');
  if(b.sleep_debt>8)signals.push('Heavy sleepiness.');else if(b.sleep_debt>4)signals.push('Beginning to feel sleepy.');
  if(b.exertion>.45)signals.push('Muscles tired from recent effort.');
  $('bodySignals').textContent=signals.join(' ')||'No strong bodily discomfort.';
  const p=state.provisions;
  $('provisions').textContent=`Ready food: ${p.pantry.toFixed(1)} servings · Fruit available: ${p.berries.toFixed(1)} servings · Spring basin: ${p.water_litres.toFixed(1)} litres`;
  const last=state.appraisals?.at(-1);
  $('affectContext').textContent=last?.meaning?`${last.meaning}${last.concern?' · Concern: '+last.concern:''}`:'';
  renderMind(state.mind);
  const used=state.runtime?.model_usage?.choose_action,spendLine=state.model_spend;
  if($('modelSpend'))$('modelSpend').textContent=(used?`Last decision: ${used.provider==='anthropic'?'Claude '+used.model:'local '+used.model}. `:'')+
   (spendLine?`Cloud spend today $${spendLine.usd.toFixed(3)} · total $${spendLine.total_usd.toFixed(2)}${spendLine.fallbacks?` · ${spendLine.fallbacks} fallbacks to local today`:''}.`:'');
  const pending=state.pending?.decision?.action==='craft'?state.pending.decision:null;
  const key=JSON.stringify([state.practical||{},state.suspended_work||[],pending]);if(key===previous)return;previous=key;
  const trials=$('experiments'),methods=$('testedMethods');trials.replaceChildren();methods.replaceChildren();
  const practical=state.practical||{trials:[],methods:[]};
  if(pending?.attempt){const a=pending.attempt,div=card(trials,'Current attempt: '+pending.intention);if(a.hypothesis)line(div,'His hypothesis: '+a.hypothesis);line(div,`Chosen tolerance: ${a.target_error_mm} mm · Expected width error: ${a.expected_error_mm} mm.`);line(div,'Result pending.','muted');}
  for(const job of state.suspended_work||[]){const div=card(trials,'Paused work: '+job.pending.decision.intention);line(div,`${Math.ceil(job.pending.remaining/60)} minutes remain · Can be resumed as job ${job.id}.`,'muted');}
  for(const t of practical.trials.slice(-12).reverse()){
   const div=card(trials,`${t.intention||'Practical attempt'} · ${t.goal_met?'Criterion met':'Criterion not met'}`);
   if(t.hypothesis)line(div,'His hypothesis: '+t.hypothesis);
   line(div,'Method: '+Object.entries(t.parameters).map(([k,v])=>`${k}: ${v}`).join(' · '));
   line(div,t.predicted_success===null?'No success prediction recorded.':`He predicted: ${t.predicted_success?'success':'the criterion would not be met'}.`);
   if(t.expected_error_mm!==null)line(div,`Expected width error: ${t.expected_error_mm} mm.`);
   line(div,`Measured width error: ${t.actual_error_mm} mm · His tolerance: ${t.target_error_mm} mm.`);
   if(t.adjustment)line(div,'His possible adjustment: '+t.adjustment);
   line(div,`Workpiece: ${t.object_id||'record pending'} · Experience ${t.source_id??'pending'}`,'muted');
  }
  if(!practical.trials.length)line(trials,'No measured practical attempts yet.','muted');
  for(const m of practical.methods){
   const div=card(methods,m.id.replaceAll(':',' · '));
   line(div,`${m.successes}/${m.attempts} attempts met their chosen tolerances. Best measured width error: ${m.best_error_mm} mm.`);
   line(div,m.shapes.length?'Tested successfully on: '+m.shapes.join(', '):'No successful trial recorded yet.','muted');
  }
  if(!practical.methods.length)line(methods,'No practical methods tested yet.','muted');
 }
 return {update};
}
