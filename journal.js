// Observer-only activity detail and source-backed reading history.
export function createJournal({document,apiFetch}){
 const $=id=>document.getElementById(id),records=new Map(),sources=new Map(),expanded=new Set();
 let total=0,rendered='',loadingOlder=false;
 function node(tag,text,parent,cls){const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;if(parent)parent.append(n);return n;}
 function date(at){if(!at)return 'Earlier saved reading';const d=new Date(at);return Number.isNaN(d.getTime())?'Earlier saved reading':d.toLocaleString('en-GB',{timeZone:'Europe/London'});}
 function link(parent,record){
  try{const url=new URL(record.url);if(url.protocol==='https:'&&url.hostname==='en.wikipedia.org'){const a=node('a',record.title||'Wikipedia source',parent);a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';return;}}catch{}
  node('strong',record.title||'Saved article',parent);
 }
 function excerpt(pre,payload,record){
  const count=record?.processed_chars||0;
  const label=count?`Excerpt supplied to Crow (${count} characters)`:'Retrieved excerpt · no processing length recorded';
  pre.textContent=label+'\n\n'+(count?payload.text.slice(0,count):payload.text||'No excerpt saved.');
 }
 function render(){
  const items=[...records.values()].sort((a,b)=>b.id-a.id),key=JSON.stringify(items);
  if(key!==rendered){
   rendered=key;const parent=$('readingLog');parent.replaceChildren();
   if(!items.length)node('p','No reading recorded yet.',parent,'muted');
   for(const record of items){
    const card=node('article','',parent,'entry reading-entry');link(card,record);
    node('em',date(record.at)+' · '+({lookup:'Quick research',leisure:'Reading at leisure',legacy:'Earlier reading'}[record.mode]||'Reading'),card);
    if(record.new_source_text===false)node('p','Previously consulted excerpt · not fresh source evidence.',card,'muted');
    if(record.question)node('p','Question: '+record.question,card);
    if(record.intention)node('p','Working towards: '+record.intention,card);
    if(record.reason)node('p','Why: '+record.reason,card);
    if(record.summary)node('p','Crow’s source summary: '+record.summary,card);
    else node('p',record.status==='awaiting_note'?'Processing note pending.':'No source summary was saved.',card,'muted');
    if(record.lesson)node('p','His note: '+record.lesson,card);
    if(['answered','partial','not_answered'].includes(record.answer_status))node('p','His assessment: '+({answered:'question answered',partial:'partly answered',not_answered:'question still open'}[record.answer_status])+'.',card,'muted');
    if(record.next_step)node('p','Next step he considered: '+record.next_step+' (tentative)',card);
    const button=node('button',expanded.has(record.id)?'Hide excerpt':'View excerpt',card,'excerpt-button');
    const pre=node('pre','',card,'source-excerpt');pre.hidden=!expanded.has(record.id);
    if(sources.has(record.id))excerpt(pre,sources.get(record.id),record);
    button.onclick=async()=>{
     if(!pre.hidden){pre.hidden=true;expanded.delete(record.id);button.textContent='View excerpt';return;}
     pre.hidden=false;expanded.add(record.id);button.textContent='Hide excerpt';
     if(sources.has(record.id)){excerpt(pre,sources.get(record.id),records.get(record.id));return;}
     button.disabled=true;pre.textContent='Loading the saved excerpt…';
     try{const response=await apiFetch('/api/reading/'+record.id);if(!response.ok)throw Error('The saved excerpt is unavailable.');const payload=await response.json();sources.set(record.id,payload);rendered='';render();}
     catch(error){pre.textContent=error.message;}
     finally{button.disabled=false;}
    };
   }
  }
  const button=$('olderReading');button.disabled=loadingOlder||records.size>=total;button.hidden=records.size>=total;
  $('readingLogStatus').textContent=total?`Showing ${records.size} of ${total} saved reading${total===1?'':'s'}.`:'';
 }
 $('olderReading').onclick=async()=>{
  if(loadingOlder)return;loadingOlder=true;render();
  try{
   const before=Math.min(...records.keys());
   const response=await apiFetch('/api/reading'+(Number.isFinite(before)?'?before='+before:''));
   if(!response.ok)throw Error('Could not load earlier reading.');
   const data=await response.json();total=data.total;for(const record of data.items)records.set(record.id,record);
  }catch(error){$('readingLogStatus').textContent=error.message;loadingOlder=false;$('olderReading').disabled=false;return;}
  loadingOlder=false;render();
 };
 function update(state){
  total=state.reading_count||0;for(const record of state.reading_log||[])records.set(record.id,record);render();
  const parent=$('activityDetails');parent.replaceChildren();const pending=state.pending,d=pending?.decision;
  if(d){
   if(d.action==='read'||state.action==='read'){
    if(pending.reading)node('p','Source: '+pending.reading.title,parent);
    if(d.research_question)node('p','Question: '+d.research_question,parent);
    node('p',d.reading_mode==='leisure'?'Reading at leisure.':'Quick research: no simulated reading wait.',parent,'muted');
   }
   const object=state.built_world?.objects?.[d.object_id]||state.built_world?.trees?.[d.object_id];
   if(d.object_id)node('p','Object: '+(object?.name||d.object_id),parent);
   const plan=state.built_world?.plans?.find(p=>p.id===d.plan_id);
   if(plan){node('p',`Plan ${plan.id}: ${plan.name}`,parent);node('p',`${plan.work_done_minutes||0}/${plan.minutes} minutes worked · ${plan.status}`,parent,'muted');node('p','Materials: '+(Object.entries(plan.bill||{}).map(([m,q])=>`${q} kg ${m}`).join(', ')||'No additional materials'),parent,'muted');}
   if(d.action==='gather')node('p','Collecting: '+d.material,parent);
   if(d.action==='move_object'&&Number.isFinite(d.destination_x)&&Number.isFinite(d.destination_z))node('p',`Chosen position: (${d.destination_x}, ${d.destination_z})`,parent);
   if(pending.start)node('p','Started: '+date(pending.start),parent,'muted');
  }else if(state.reflection_pending){node('p','Considering the result before choosing what to do next.',parent,'muted');}
  $('nextStep').textContent=state.next_step?'Tentative next step: '+state.next_step:'Crow has not chosen a next step yet.';
 }
 return {update};
}
