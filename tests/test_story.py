"""Stories, threads and promises: continuity recorded from what actually happened, never chosen for him."""
import copy, importlib.util, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import story

s={'body':{'active_hours':10.}}
def ev(i,intention,action='observe',text='Observed something.'):
    return {'id':i,'kind':'experience','at':f'2026-11-0{1+i%8}T10:00','intention':intention,'action':action,'event':text,'reason':'Because.'}
a=story.note_step(s,ev(1,'Map the unlogged woodland edge for new plants'))
b=story.note_step(s,ev(2,'Map unlogged woodland edge near (17,-17) for new plants'))
assert a is b and a['stage']=='started' and a['kind']=='looking'
story.note_step(s,ev(3,'Look for new plants along the unlogged woodland edge'))
assert a['stage']=='pursuing' and a['count']==3
c=story.note_step(s,ev(4,'Carve a bowl that holds water','craft'));assert c is not a and c['kind']=='making'
assert [x['id'] for x in story.context(s)]==[a['id']], 'one-step beginnings are not yet stories'
s['body']['active_hours']=10+story.DORMANT_HOURS+1;story.age(s);assert a['stage']=='dormant'
story.note_step(s,ev(5,'Map the unlogged woodland edge for new plants'));assert a['stage']=='pursuing'
m=ev(6,'Map the unlogged woodland edge for new plants','read');story.note_step(s,m);story.settle(s,m,'answered');assert a['stage']=='answered'
s['body']['active_hours']+=story.LEFT_HOURS*2;story.age(s);assert c['stage']=='left'
# Threads and promises.
t=story.add_thread(s,'Moss only on the north side of the birch?','grove',7,'t');assert t and not story.add_thread(s,'Moss only on north side of the birch','grove',8,'t')
assert story.follow_thread(s,t['id'],9,'t')['status']=='followed'
p=story.add_promise(s,'Fix the store-room roof next week','Edda Thorne','t');assert story.keep_promise(s,p['id'],'t')['status'].startswith('kept')
assert not story.open_items(s)['promises']

# Beliefs: patterns from his own record, by rule, revised when experience changes.
b={'body':{'active_hours':0},'memories':[],'appraisals':[]}
def occasion(i,action,valence,ok):
    b['memories'].append({'id':i,'action':action,'world_result':{'success':ok}});b['appraisals'].append({'source_id':i,'valence':valence})
for i in range(3):occasion(i,'browse',-.4,False)
story.update_beliefs(b,'t');assert not b['beliefs'], 'three occasions are not a pattern'
occasion(3,'browse',-.3,False);story.update_beliefs(b,'t')
assert {x['statement'] for x in b['beliefs']}=={'Searching the web at the café tends to leave me low.','Searching the web at the café often does not work out.'}
assert all(x['status']=='forming' for x in b['beliefs'])
for i in range(4,7):occasion(i,'browse',-.3,False)
story.update_beliefs(b,'t');assert all(x['status']=='held' for x in b['beliefs'])
for i in range(7,20):occasion(i,'browse',.6,True)
story.update_beliefs(b,'t2')
assert any(x['status']=='revised' and 'leave me low' in x['statement'] for x in b['beliefs'])
assert any(x['statement']=='Searching the web at the café tends to lift me.' and x['status']=='held' for x in b['beliefs'])

# How work feels: pull, grind, doubt from his appraisals; attached to the story and the project it served.
f={'stories':[{'id':1}],'projects':[{'id':5}]}
carve={'action':'craft','story_id':1,'project_id':5,'world_result':{'trial':{'goal_met':False}}}
assert story.record_feel(f,carve,.5)=='doubt', 'a missed criterion is doubt whatever the mood'
ok={'action':'craft','story_id':1,'project_id':5,'world_result':{'trial':{'goal_met':True}}}
assert story.record_feel(f,ok,.4)=='pull' and story.record_feel(f,ok,0)=='grind' and story.record_feel(f,ok,-.3)=='grind'
assert f['projects'][0]['feel']['sessions']==4 and f['projects'][0]['feel']['mostly']=='grind' and f['stories'][0]['feel']['last']=='grind'
assert story.felt({'action':'rest'},0)=='neutral'

# In his life: steps join stories as activities finish; reflections can leave threads open and follow them up.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_story_test',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,1,12,0,tzinfo=app.TZ);app.state['paused']=False
    base={'reason':'Want to see.','intention':'Watch which insects visit the ivy flowers','next_step':'','wish':'','wish_reason':'','project_id':-1,
          'project_title':'','project_status':'active','target_action':'observe','target_sessions':1}
    seen={}
    def model(prompt,schema,limit=650,purpose='other',system=None):
        seen[purpose]=schema
        return ({'feeling':'Curious.','lesson':'','topic':'ivy insects','enjoyment':1,'personality_note':'','next_step':'','reading_summary':'',
                 'answer_status':'not_applicable','meaning':'Something to watch.','adjustment':'','valence':.3,'arousal':.2,'importance':.4,
                 'left_open':model.left,'thread_followed':model.follow,'promise_kept':0},1)
    app.model_call=model
    for i in range(2):
        model.left='Which insect comes to the ivy after dark?' if i==0 else '';model.follow=0 if i==0 else app.state['threads'][0]['id']
        app.start_action({**app.DECISION_DEFAULTS,**base,'action':'observe','observe_area':'woodland_edge','focus':'ivy insects'},1)
        app.tick(app.state['pending']['remaining']);m=app.finish_action();app.reflect(m)
    st=app.state['stories'][-1];assert st['count']==2 and m['story_id']==st['id']
    assert app.state['threads'][0]['status']=='followed' and app.state['threads'][0]['place']=='woodland_edge'
    assert 'left_open' in seen['reflect']['properties']
    ctx=app.decision_context();assert ctx['your_ongoing_stories'][0]['story'].startswith('Watch which insects')
print('PASS: pull, grind and doubt per story and project; patterns form, hold and are revised from his record; matching intentions continue one story; single steps are not stories; dormant and answered only by time or evidence; '
      'threads deduped and followed; promises kept by his account; stories reach his decisions.')
# v0.30.5: the same promise said again is one promise, said again; a slightly different title is still that title.
import inner as _inner
_st={'promises':[],'next_promise_id':1}
story.ensure(_st)
a=story.add_promise(_st,"I'll check each line against my copy, one at a time, before agreeing to any figure.",'Edda Thorne','t1')
b=story.add_promise(_st,"I'll check each line against my copy with you, one at a time, before we settle any figure.",'Edda Thorne','t2')
c=story.add_promise(_st,'I will bring you twenty kilos of wood tomorrow.','Edda Thorne','t3')
assert a is b and a['times_said']==2 and a['last_said']=='t2' and c is not a and len(_st['promises'])==2
print('PASS v0.30.5: a promise said again is the same promise.')
# v0.30.8: going to an empty chest is not eating, so it never shapes what he believes eating does for him.
_st2={'memories':[],'appraisals':[],'beliefs':[]};story.ensure(_st2)
for i in range(8):
    _st2['memories'].append({'id':i,'action':'eat','world_result':{'success':False}})
    _st2['appraisals'].append({'source_id':i,'valence':-.6})
story.update_beliefs(_st2,'t')
assert not any(b['key'].endswith(':eat') for b in _st2['beliefs']), _st2['beliefs']
print('PASS v0.30.8: an empty chest is not a meal in his record.')
# v0.30.12: a plan to eat the last bread ends when the chest turns out empty; it is not shown as still under way.
_st3={'stories':[{'id':1,'title':'Eat the last bit of bread slowly here in my cabin','stage':'pursuing','steps':[]}]}
story.settle_need(_st3,{'action':'eat','story_id':1,'at':'t','world_result':{'success':False,'text':'Nothing was eaten: the provisions chest is empty.'}},['Persistent hunger; little food is being digested.'])
assert _st3['stories'][0]['stage']=='left' and 'nothing there' in _st3['stories'][0]['ended_by']
print('PASS v0.30.12: a plan to eat what is not there ends when he finds nothing.')
