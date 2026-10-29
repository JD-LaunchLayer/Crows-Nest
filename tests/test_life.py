"""Counterfactual checks of the first causal learning/body loop."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import life
import world_state

def fresh():
    state={'energy':85,'materials':8,'creations':[],'location':'cabin'}
    world_state.ensure(state);life.ensure(state);return state

s=fresh();before=copy.deepcopy(s);life.ensure(s);assert s==before
assert life.consume(s,'eat','food_store')['success']
assert s['body']['reserve']==before['body']['reserve']  # Eating is not an instant energy refill.
assert s['provisions']['pantry']==23 and s['body']['stomach']>before['body']['stomach']
life.advance(s,1800,'rest');assert s['body']['stomach']<34 and s['body']['reserve']>before['body']['reserve']
assert life.consume(s,'drink','spring')['success'] and s['provisions']['water_litres']<40
s['provisions']['pantry']=0;assert not life.consume(s,'eat','food_store')['success']
assert not life.consume(s,'eat','library')['success']
assert not life.consume(s,'drink','berry_patch')['success']
one=fresh();two=copy.deepcopy(one)
life.advance(one,7200,'fell_tree');life.advance(two,7200,'rest')
assert one['body']['reserve']<two['body']['reserve'] and one['body']['hydration']<two['body']['hydration']
assert life.fatigue(one)>life.fatigue(two)
one['provisions']['berries']=0;one['provisions']['water_litres']=0
life.advance(one,3600,'sleep');assert abs(one['provisions']['berries']-.25)<1e-8 and abs(one['provisions']['water_litres']-2)<1e-8
restored=json.loads(json.dumps(one));snapshot=copy.deepcopy(restored);life.ensure(restored);assert restored==snapshot
assert restored['provisions']['pantry']==24  # Only the original authored stock, not a reset on load.

bad={'intention':'Test a shape.','creation_shape':'orb','attempt':{'support':'hand','passes':'deep','direction':'across',
     'hypothesis':'This cut might be accurate enough.','predicted_success':True,'expected_error_mm':3,'target_error_mm':6}}
good={**bad,'attempt':{**bad['attempt'],'support':'bench','passes':'light','direction':'along'}}
s=fresh();first=life.practical_attempt(s,bad,2700)
life.bind_trial(s,first,{'id':1,'at':'2026-10-29T12:00:00Z'})
assert not first['goal_met'] and first['predicted_success'] and first['prediction_error_mm']>0
second=life.practical_attempt(s,good,2700);life.bind_trial(s,second,{'id':2,'at':'2026-10-29T13:00:00Z'})
assert second['goal_met'] and second['actual_error_mm']<first['actual_error_mm']
reuse={**good,'creation_shape':'bowl','method_id':second['method_id'],'attempt':{'target_error_mm':6}}
third=life.practical_attempt(s,reuse,2700);assert third['goal_met'] and third['parameters']==second['parameters']
assert {'orb','bowl'}.issubset(set(next(m for m in s['practical']['methods'] if m['id']==second['method_id'])['shapes']))
well=fresh();tired=copy.deepcopy(well);life.advance(tired,14400,'fell_tree')
assert life.practical_attempt(tired,good,2700)['actual_error_mm']>life.practical_attempt(well,good,2700)['actual_error_mm']
trained=fresh()
initial=life.practical_attempt(trained,good,2700)['actual_error_mm']
for _ in range(8):life.practical_attempt(trained,good,2700)
assert life.practical_attempt(trained,{**good,'creation_shape':'spire'},2700)['actual_error_mm']<initial

sad=fresh();neutral=copy.deepcopy(sad);mem={'id':99,'intention':'My own concern.','reason':'An attempt.'}
life.appraise(sad,mem,{'meaning':'This matters to my goal.','valence':-.7,'arousal':.5,'importance':.8})
life.appraise(neutral,mem,{'meaning':'It did not matter much.','valence':0,'arousal':0,'importance':0})
assert sad['affect']['valence']<0 and neutral['affect']['valence']==0
old=sad['affect']['valence'];life.advance(sad,3600,'rest');assert old<sad['affect']['valence']<0
assert sad['affect']['signals'][0]['source_id']==99  # Evidence comes from the event, not a model-supplied ID.

with tempfile.TemporaryDirectory() as temp:
    folder=Path(temp);shutil.copy(ROOT/'crow.py',folder/'crow.py')
    old={'version':4,'materials':8,'energy':80,'memories':[],'creations':[]}
    (folder/'crow-save.json').write_text(json.dumps(old))
    spec=importlib.util.spec_from_file_location('crow_life_test',folder/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    assert json.loads((folder/'crow-save-before-v0.5.json').read_text())==old
    assert app.state['materials']==8 and app.state['provisions']['pantry']==24
    d={'action':'craft','reason':'I want to test this.','intention':'Test a width.','wish':'','wish_reason':'',
       'library_query':'','creation_name':'First trial','creation_shape':'orb','project_id':0,'project_title':'',
       'project_status':'active','target_action':'craft','target_sessions':1,'attempt':bad['attempt']}
    app.state['paused']=False;app.start_action(d,1);app.tick(900)
    remaining=app.state['pending']['remaining'];body=copy.deepcopy(app.state['body'])
    app.state['paused']=True;app.tick(3600);assert app.state['body']==body
    app.state['paused']=False
    app.model_call=lambda *args,**kwargs:({'continue_work':False,'reason':'I want a break.'},1)
    app.review_work(app.state['pending']);assert app.state['pending'] is None and app.state['materials']==8
    job=app.state['suspended_work'][0];assert job['pending']['remaining']==remaining
    app.persist();saved=json.loads((folder/'crow-save.json').read_text());assert saved['suspended_work'][0]['pending']['remaining']==remaining
    app.start_action({'action':'resume_work','resume_work_id':job['id'],'reason':'Return to it.','next_step':''},1)
    assert app.state['pending']['remaining']==remaining and not app.state['suspended_work']
    app.tick(remaining);memory=app.finish_action()
    trial=app.state['practical']['trials'][-1];assert not trial['goal_met'] and app.state['materials']==7
    artifact=app.state['built_world']['objects'][trial['object_id']]
    assert abs(world_state.mass(artifact['parts'])['wood']-1)<.02
    assert abs((artifact['parts'][0]['width']-.14)*1000-trial['actual_error_mm'])<.01
    assert trial['source_id']==memory['id'] and app.state['reflection_pending']==memory['id']
    control=app.state['practical']['control_hours']
    # A read-only reference/ordinary reflection cannot increase motor skill.
    result={'feeling':'I need to change my approach.','lesson':'This attempt missed my tolerance.',
            'topic':'test','enjoyment':0,'personality_note':'','next_step':'Inspect the workpiece.',
            'reading_summary':'','answer_status':'not_applicable','meaning':'My prediction was too optimistic.',
            'adjustment':'Try a supported lighter pass.','valence':-.2,'arousal':.2,'importance':.4}
    app.model_call=lambda *args,**kwargs:(result,1);assert app.reflect(memory)
    assert app.state['practical']['control_hours']==control and trial['adjustment']==result['adjustment']
    assert not app.state['reflection_pending']
    # A new runtime craft gets its own prediction before the attempt, without retroactive invention.
    chosen=copy.deepcopy(d);chosen.pop('attempt')
    app.model_call=lambda *args,**kwargs:(good['attempt'],1);app.prepare_attempt(chosen)
    assert chosen['attempt']['predicted_success'] is True
    app.persist();snapshot=copy.deepcopy(app.state);life.ensure(app.state);assert app.state==snapshot
    calls=[]
    def choose_stub(prompt,schema,limit,*purpose,pick='rest'):
        calls.append({'prompt':prompt,'schema':schema})
        out={}
        for key in schema['required']:
            prop=schema['properties'][key]
            out[key]=(pick if key=='action' else prop['enum'][0]) if 'enum' in prop else '' if prop['type']=='string' else [] if prop['type']=='array' else False if prop['type']=='boolean' else 1
        return out,1
    app.model_call=choose_stub;app.state['energy']=0;app.choose()
    action_schema=calls[0]['schema']
    assert {'eat','drink','read','craft'}.issubset(set(action_schema['properties']['action']['enum']))
    assert 'body' in calls[0]['prompt'] and len(calls[0]['prompt'])<9000
    # Choosing craft brings its measured trial evidence and precommitment into the details step only.
    calls.clear();app.model_call=lambda *a,**k:choose_stub(*a,pick='craft');chosen=app.choose()[0]
    assert len(calls)==2 and 'recent_trials' in calls[1]['prompt'] and 'recent_trials' not in calls[0]['prompt']
    assert chosen['action']=='craft' and set(chosen['attempt'])>={'hypothesis','predicted_success','target_error_mm','support'}

print('PASS: digestion, effort and sleep processes; renewable supplies; no offline refill; '
      'prediction errors and method correction; fatigue and practice transfer; contextual affect; '
      'migration/backup; agent-selected pause/resume; material-paid measurable artifact; no reading-to-skill shortcut.')
