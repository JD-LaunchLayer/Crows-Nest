"""Causal operations, reusable methods and evidence trails, on private temporary lives."""
import copy
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import subprocess
from datetime import datetime

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import experience
import interactions as I
import life
import memory_recall
import world_state as W


def fresh():
    s={'materials':12.,'stone':8.,'creations':[],'location':'workbench','daylight':1}
    W.ensure(s);life.ensure(s);I.ensure(s)
    return s


def decision(verb, target='', other='', params=None, **extra):
    return {'verb':verb,'object_id':target,'other_id':other,'interaction_params':params or {},
            'procedure_id':'','creation_name':'A chosen object','hypothesis':'This may work.',
            'prediction':'It may hold.','intention':'Try my own idea.',**extra}


def shape(s, **params):
    d=decision('shape',params={'material':'wood','shape':'box','mass_kg':1.,
        'width_m':.2,'depth_m':.2,'support':'bench','passes':'light',**params})
    I.prepare(s,d);r=I.execute(s,d,1800)
    assert r['success'],r
    return d,r


def material_total(s):
    return s['materials']+sum(W.mass(o['parts']).get('wood',0) for o in s['built_world']['objects'].values())


# Initial visible furnishings become ledger objects once. Nothing is reset on load.
s=fresh();before=copy.deepcopy(s);I.ensure(s);assert s==before
s['built_world']['objects']['library_chair']['x']=2
restored=json.loads(json.dumps(s));I.ensure(restored)
assert restored['built_world']['objects']['library_chair']['x']==2

# Shape a material-paid solid with a measured dimension; no prescribed hobby or name.
s=fresh();total=material_total(s);d,r=shape(s)
assert s['materials']==11 and abs(material_total(s)-total)<.02
assert r['measurements']['actual_width_m']>r['measurements']['target_width_m']
I.record(s,d,r,{'id':1,'at':'2026-11-01T12:00:00+00:00'})
method=s['procedures']['methods'][0];assert method['successes']==1
again=decision('shape',params={},procedure_id=method['id'])
I.prepare(s,again);r2=I.execute(s,again,1800)
assert r2['success'] and s['materials']==10
I.record(s,again,r2,{'id':2,'at':'2026-11-02T12:00:00+00:00'})
assert s['procedures']['attempts'][-1]['reused'] and method['attempts']==2
assert s['procedures']['attempts'][-1]['measurements']['width_error_mm']<r['measurements']['width_error_mm']

# Method reuse is an option, not a guarantee; changing supplies causes an honest failure.
s['materials']=0;before=copy.deepcopy(s['built_world']);I.prepare(s,again)
failed=I.execute(s,again,1800);assert not failed['success'] and s['built_world']==before and s['materials']==0
I.record(s,again,failed,{'id':3,'at':'2026-11-03T12:00:00+00:00'})
assert method['successes']==2 and method['attempts']==3
assert len(s['procedures']['attempts'])==3

# Splitting conserves material and leaves two actual independent solids.
s=fresh();_,r=shape(s);obj=r['object_id'];total=material_total(s)
split=decision('split',obj,params={'fraction':.5});I.prepare(s,split)
cut=I.execute(s,split,1200)
assert cut['success'] and len(cut['changed_ids'])==2 and abs(material_total(s)-total)<.02
assert s['materials']==11
# A second operation prepared against old geometry is rejected without partial mutation.
stale=decision('split',obj,params={'fraction':.5});I.prepare(s,stale)
s['built_world']['objects'][obj]['revision']+=1
before=copy.deepcopy(s);bad=I.execute(s,stale,1200)
assert not bad['success'] and s==before

# Placing on a surface persists its height; moving away lowers it to the ground.
s=fresh();_,r=shape(s);obj=r['object_id'];total=material_total(s)
place=decision('place_on',obj,'workbench',{'part_id':'top'});I.prepare(s,place)
assert I.execute(s,place,180)['success']
assert s['built_world']['objects'][obj]['on']=='workbench'
assert not W.move(s,'workbench',2,2)['success']
assert W.move(s,obj,5,3)['success'] and 'on' not in s['built_world']['objects'][obj]
assert abs(min(p['y']-p['height']/2 for p in s['built_world']['objects'][obj]['parts']))<1e-9
assert abs(material_total(s)-total)<.02

# Arrangements keep both solids, not two copies plus a new free object.
s=fresh();_,base=shape(s,mass_kg=3,width_m=.35,depth_m=.35);_,top=shape(s)
total=material_total(s);stack=decision('stack',top['object_id'],base['object_id'],{'part_id':'body'})
I.prepare(s,stack);r=I.execute(s,stack,600);assert r['success'],r
assert abs(material_total(s)-total)<.02
assert not s['built_world']['objects'][base['object_id']]['parts']
W.ensure(s);assert not s['built_world']['objects'][base['object_id']]['parts']
assert len(s['built_world']['objects'][r['object_id']]['parts'])==2
# Removing parts or changing a target never regenerates it at reload.
loaded=json.loads(json.dumps(s));I.ensure(loaded)
assert material_total(loaded)==material_total(s)

# Failures are atomic: unsupported material/tools, bad faces, insufficient stock.
for params in ({'material':'stone'},{'width_m':float('nan')},{'mass_kg':19}):
    s=fresh();d=decision('shape',params={'material':'wood','shape':'box','mass_kg':1,'width_m':.2,
        'depth_m':.2,'support':'bench','passes':'light',**params})
    try:I.prepare(s,d)
    except ValueError:continue
    before=copy.deepcopy(s);r=I.execute(s,d,1800)
    assert not r['success'] and s==before
s=fresh();_,r=shape(s);wrong=decision('place_on',r['object_id'],'library_chair',{'part_id':'back'})
I.prepare(s,wrong);before=copy.deepcopy(s);assert not I.execute(s,wrong,180)['success'] and s==before

# Posture is chosen, not an implicit reward for approaching a chair.
s=fresh();before=copy.deepcopy(s)
sit=decision('sit','library_chair',params={'part_id':'seat'});I.prepare(s,sit)
assert 'posture' not in s
assert I.execute(s,sit,900)['success'] and s['posture']['object_id']=='library_chair'
assert s['affect']==before['affect'] and s['body']==before['body']
lie=decision('lie','cabin_bed',params={'part_id':'bed'});I.prepare(s,lie)
assert I.execute(s,lie,900)['success']

# Recall preserves a contradiction and distinguishes experience from interpretation.
assert not memory_recall.similar('The shallow joint held firmly.','The shallow joint never held firmly.')
s.update(current_intention='The shallow joint held firmly',next_step='',
    memories=[{'id':1,'kind':'experience','event':'The shallow joint held firmly.'},
              {'id':2,'kind':'experience','event':'The shallow joint never held firmly.'}],
    long_term=[{'source_id':1,'interpretation':'The shallow joint held firmly.'}])
recall=memory_recall.recall(s,4000)
assert any('never' in r['text'] for r in recall) and {'event','lesson'}<={r['type'] for r in recall}

# Returning and feeling are separate; repeated source text remains labelled as such.
s=fresh();s['interests']={'earlier topic':8}
for ident,day,enjoy,freshness in [(10,1,2,True),(20,2,1,True),(30,3,-2,False)]:
    m={'id':ident,'at':f'2026-11-{day:02d}T12:00:00+00:00','action':'read','kind':'experience',
       'intention':'My own subject','choice_id':ident-1,'new_source_text':freshness}
    experience.record(s,m,{'topic':'my subject','enjoyment':enjoy,'feeling':'My response.'})
    experience.record(s,m,{'topic':'my subject','enjoyment':enjoy,'feeling':'My response.'})
row=experience.summary(s)[0]
assert row['episodes']==3 and row['separate_choices']==3 and row['fresh_experiences']==2
assert row['recent_enjoyment']==[2,1,-2] and row['physical_successes']==0
assert s['interests']=={'earlier topic':8}

# Full backend: an in-flight physical attempt survives reload; nothing is awarded by reading/reflection.
with tempfile.TemporaryDirectory() as td:
    folder=pathlib.Path(td);shutil.copy(ROOT/'crow.py',folder/'crow.py')
    def load():
        spec=importlib.util.spec_from_file_location('crow_experience_test',folder/'crow.py')
        app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
        app.CLOCK_OVERRIDE=lambda:datetime(2026,11,1,12,0,tzinfo=app.TZ)
        return app
    app=load();app.state['paused']=False;app.state['materials']=5
    d={**app.DECISION_DEFAULTS,'action':'interact','intention':'Try my idea','reason':'My choice',
       **decision('shape',params={'material':'wood','shape':'wedge','mass_kg':1,
          'width_m':.2,'depth_m':.2,'support':'bench','passes':'light'})}
    app.start_action(d,1);app.tick(300);app.persist();remaining=app.state['pending']['remaining']
    app=load();assert app.state['pending']['remaining']==remaining and app.state['materials']==5
    app.state['paused']=False;app.tick(remaining*10);m=app.finish_action()
    assert app.state['materials']==4 and m['world_result']['object_id']
    assert m['choice_id'] and app.state['procedures']['attempts'][-1]['source_id']==m['id']
    res={'feeling':'Surprised by that result.','lesson':'','topic':'my chosen shapes','enjoyment':1,
         'personality_note':'','next_step':'','meaning':'A useful attempt.','valence':.2,'arousal':.2,
         'importance':.4,'adjustment':'','reading_summary':'','answer_status':'not_applicable'}
    app.model_call=lambda *a,**k:(res,1)
    app.reflect(m);app.reflect(m)
    assert len(app.state['interest_history']['my chosen shapes']['episodes'])==1
    assert len(app.state['procedures']['attempts'])==1
    # New-version migration backs up exact prior bytes before adding furnishings.
    prior={'materials':7,'creations':[],'memories':[]}
    (folder/'crow-save.json').write_text(json.dumps(prior));app=load()
    assert json.loads((folder/'crow-save-before-v0.16.json').read_text())==prior

    # The detail call is specific to the operation Crow actually selected.
    calls=[]
    choice={'action':'interact','intention':'Try my own arrangement','reason':'My choice','next_step':'',
            'wish':'','wish_reason':'','project':'none','project_id':0,'memory_ids_used':[]}
    def model(prompt,schema,limit=650,purpose='other',**kw):
        calls.append((purpose,prompt,schema))
        if purpose=='choose_action':return choice,1
        if purpose=='parameters:interact':return {'verb':'sit'},1
        if purpose=='interaction:sit':return {'object_id':'library_chair','part_id':'seat','hypothesis':'','prediction':''},1
        raise AssertionError(purpose)
    app.model_call=model;chosen,_=app.choose()
    assert chosen['action']=='interact' and chosen['verb']=='sit'
    assert 'verb' not in calls[0][2]['properties'] and 'shape' not in calls[-1][2]['properties']
    assert 'No other people, shop or currency exist' not in calls[0][1]
    assert len(calls)==3 and 'physical_successes' not in calls[0][2]['properties']
    choice.update(project='start')
    original_model=model
    def new_project(prompt,schema,limit=650,purpose='other',**kw):
        if purpose=='parameters:interact':
            return {'verb':'sit','project_title':'My own arrangement','target_action':'interact','target_sessions':2},1
        return original_model(prompt,schema,limit,purpose,**kw)
    app.model_call=new_project;chosen,_=app.choose()
    assert chosen['project_id']==0 and chosen['project_title']=='My own arrangement' and chosen['target_sessions']==2
    bad=decision('sit','library_chair',params={'part_id':'seat'},hypothesis=None)
    try:I.prepare(app.state,bad);raise AssertionError('Malformed text must fail before work')
    except ValueError:pass

    # Reporting reads the live save/log without starting actions or invoking AI.
    for day in range(1,4):
        app.CLOCK_OVERRIDE=lambda day=day:datetime(2026,11,day,12,0,tzinfo=app.TZ)
        app.event('A recorded choice.',kind='started',action='observe',memory_ids_used=[])
    app.persist();before={p.name:p.read_bytes() for p in folder.iterdir() if p.is_file()}
    output=subprocess.check_output([sys.executable,str(ROOT/'tools/behaviour_report.py'),'--save',str(app.SAVE),'--days','3'],text=True)
    report=json.loads(output)
    assert len(report['by_day'])==3 and report['physical_attempts']==0
    assert before=={p.name:p.read_bytes() for p in folder.iterdir() if p.is_file()}

print('PASS: material conservation; atomic failures; persisted surfaces/postures; methods reused on actual targets; '
      'supplies still constrain reuse; predictions before work; save migration and in-flight progress; '
      'contradictory recall; interest evidence across days; idempotent reflection; no assigned enjoyment.')
