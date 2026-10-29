"""Sleep consolidation: grounded, finite, competitive, revisable, and never a life-stopper."""
import copy, importlib.util, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import consolidation as C, memory_recall

def life(n=6):
    s={'body':{'active_hours':0.},'memories':[],'appraisals':[]}
    for i in range(1,n+1):
        s['memories'].append({'id':i*2-1,'kind':'started','event':'Started observe.'})
        s['memories'].append({'id':i*2,'kind':'experience','event':f'Observed ivy flowers on tree-{i} with wasps feeding.','new_evidence':True})
    return s
at='2026-11-01T07:00:00+00:00'

# Only real events from the day can ground a memory; uncited text is refused.
s=life();C.ensure(s);digest=C.day_digest(s);ids={d['id'] for d in digest}
assert digest and all(d['id']%2==0 for d in digest), 'started events are not experiences'
r=C.apply(s,'life',{'memories':[{'text':'Wasps feed on ivy flowers in autumn.','revises':0,'evidence_ids':[2,4],'importance':.6},
                                 {'text':'I am destined to be a great sculptor.','revises':0,'evidence_ids':[999],'importance':1}]},ids,at)
assert len(r['added'])==1 and r['refused'][0]['why'].startswith('no event')
# A reworded duplicate reinforces instead of being stored again.
held=s['mind']['life'][0];before=held['strength']
r=C.apply(s,'life',{'memories':[{'text':'In autumn, wasps feed on the ivy flowers.','revises':0,'evidence_ids':[6],'importance':.5}]},ids,at)
assert not r['added'] and held['strength']>before
# Revision replaces the wording but keeps the earlier wording visibly.
r=C.apply(s,'life',{'memories':[{'text':'Wasps and hoverflies feed on ivy flowers when little else is flowering.','revises':held['id'],'evidence_ids':[8],'importance':.7}]},ids,at)
assert r['revised']==[held['id']] and held['previous'][0]['text']=='Wasps feed on ivy flowers in autumn.'
# Topic ceiling: one word may anchor at most four memories, however it is reworded.
s2=life();C.ensure(s2);ids2={d['id'] for d in C.day_digest(s2)}
dark=['Darkness helps focus on form over species','Darkness enhances minimalist abstraction','Darkness supports minimalist plant observation',
      'Darkness simplifies visual constraints','Darkness reduces visual complexity for sculpture','Darkness and hunger suit creative minimalism']
r=C.apply(s2,'life',{'memories':[{'text':t,'revises':0,'evidence_ids':[2],'importance':.5} for t in dark[:5]]},ids2,at)
r2=C.apply(s2,'life',{'memories':[{'text':dark[5],'revises':0,'evidence_ids':[2],'importance':.5}]},ids2,at)
words=[e['text'] for e in s2['mind']['life']]
assert sum('Darkness' in t for t in words)<=4 and any('anchors' in x['why'] for x in r['refused']+r2['refused'])
# Pair ceiling: the same two-word idea at most twice, even with other wording.
s3=life();C.ensure(s3)
r=C.apply(s3,'world',{'memories':[{'text':f'Spring water {w}','revises':0,'evidence_ids':[2],'importance':.5} for w in ['refills slowly','tastes cold','stays clear']]},ids2,at)
assert len(r['added'])==2 and 'idea' in r['refused'][0]['why']
# Capacity: a full section admits only something stronger than its weakest memory, which is archived, not deleted.
s4=life();C.ensure(s4)
s4['mind']['skills']=[{'id':i,'text':f'Unique skill note {w}','strength':.6+i/100,'created':at} for i,w in enumerate(
    'alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar papa quebec romeo sierra tango uniform victor whiskey xray'.split(),1)]
s4['mind']['next_id']=100
r=C.apply(s4,'skills',{'memories':[{'text':'Light passes along the grain held the rim.','revises':0,'evidence_ids':[2],'importance':.9}]},ids2,at)
assert r['forgotten']==[1] and len(s4['mind']['skills'])==24 and s4['mind']['forgotten'][-1]['text']=='Unique skill note alpha'
weak=C.apply(s4,'skills',{'memories':[{'text':'Barely notable carving detail here.','revises':0,'evidence_ids':[2],'importance':0}]},ids2,at)
assert weak['refused'] and weak['refused'][0]['why'].startswith('not stronger')
# Fading follows active life only: three weeks of active hours halve strength; paused time does nothing.
s5=life();C.ensure(s5);s5['mind']['life']=[{'id':1,'text':'x memory','strength':1.0,'created':at}]
C.fade(s5);assert s5['mind']['life'][0]['strength']==1.0
s5['body']['active_hours']=21*24;C.fade(s5);assert abs(s5['mind']['life'][0]['strength']-.5)<1e-3
# Held memories reach decisions through recall.
s['current_intention']='watch the ivy flowers and wasps'
assert any(x['type']=='held_life' for x in memory_recall.recall(s))

# Integration: waking from sleep consolidates; a model failure does not stop his life.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_mind_test',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,1,12,0,tzinfo=app.TZ);app.state['paused']=False
    app.event('Observed ivy on tree-3; wasps were feeding on its flowers.',kind='experience',new_evidence=True)
    calls=[]
    def model(prompt,schema,limit,purpose):
        calls.append(purpose);ids=schema['properties']['memories']['items']['properties']['evidence_ids']['items']['enum']
        return {'memories':[{'text':'Wasps visit ivy flowers.' if purpose.endswith('life') else 'Ivy flowers exist on tree-3.','revises':0,'evidence_ids':ids[-1:],'importance':.5}],'reinforced_ids':[],'contradicted_ids':[]},1
    app.model_call=model
    reports=app.consolidate_after_sleep()
    assert calls==['consolidate:life','consolidate:skills','consolidate:world'] and reports['life']['added']
    assert app.state['memories'][-1]['kind']=='consolidated' and app.state['mind']['nights']==1
    assert not app.consolidate_after_sleep(), 'nothing new since last sleep means nothing to consolidate'
    def broken(*a):raise ConnectionError('Ollama down')
    app.event('Another day.',kind='experience');app.model_call=broken
    assert app.consolidate_after_sleep() is None and not app.state['paused'] and 'Ollama' in app.state['mind']['last_error']
    context=app.decision_context();assert context['held_most_strongly']
print('PASS: grounded in real events; reworded duplicates reinforce; visible revisions; word and idea ceilings; finite capacity with archived '
      'forgetting; fading only with active life; held memories reach recall and decisions; sleep integration; failures never stop life.')
