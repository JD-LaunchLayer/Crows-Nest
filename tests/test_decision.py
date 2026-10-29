"""Two-stage choice and protected recall on a long synthetic life (not Crow's real save)."""
import copy, importlib.util, json, shutil, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import lived_fixture, memory_recall

def load(folder,name):
    shutil.copy(ROOT/'crow.py',folder/'crow.py')
    spec=importlib.util.spec_from_file_location(name,folder/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    return app

def stub(calls,stage1,params=None):
    def call(prompt,schema,limit,*purpose):
        calls.append({'prompt':prompt,'schema':schema,'limit':limit})
        if 'action' in schema['properties']:return copy.deepcopy(stage1),1
        return copy.deepcopy(params or {}),1
    return call

base={'action':'rest','intention':'Carve a bowl whose rim does not split','reason':'My last rim split.','next_step':'',
      'wish':'','wish_reason':'','project':'none','project_id':0,'memory_ids_used':[]}
ACTION_SPECIFIC={'creation_shape','creation_name','reading_spot','reading_mode','library_query','research_question','attempt',
                 'destination_x','destination_z','plan_operation','part_id','material','object_id','plan_id','method_id','target_action'}

with tempfile.TemporaryDirectory() as td:
    app=load(Path(td),'crow_decision_test');lived_fixture.populate(app.state);app.state['paused']=False
    before=copy.deepcopy(app.state)

    # 1. Rest: one small call, no irrelevant fields, a decision start_action accepts.
    calls=[];app.model_call=stub(calls,base);d,_=app.choose()
    assert len(calls)==1 and not ACTION_SPECIFIC & set(calls[0]['schema']['properties'])
    assert len(calls[0]['schema']['properties'])<=9 and calls[0]['limit']<=400
    prompt=calls[0]['prompt'];context=json.loads(prompt[prompt.index(' State: ')+8:])
    # 2. Memory survives pressure: recent events and relevant memories are present on a busy life.
    assert context['recent_events'] and context['relevant_memories'] and context['body']
    texts=' '.join(m['text'] for m in context['relevant_memories'])
    assert 'split the bowl rim' in texts, 'old specific lesson should be recalled for a matching intention'
    assert len(prompt)+len(app.BASELINE)<7600
    # Recall and context building never rewrite his saved life.
    life_only=lambda s:{k:v for k,v in s.items() if k not in ('minute','day','clock','daylight')}
    assert life_only(app.state)==life_only(before)
    app.start_action(d,1);started=app.state['memories'][-1]
    assert started['recalled_ids'] and started['memory_ids_used']==[]

    # 3. A cited memory ID that was not shown is discarded, not trusted.
    shown=context['relevant_memories'][0]['id']
    calls=[];app.model_call=stub(calls,{**base,'memory_ids_used':[shown,999999]});d,_=app.choose()
    assert d['memory_ids_used']==[shown]

    # 4. Details step sees only its own fields and cannot change the action.
    calls=[];app.model_call=stub(calls,{**base,'action':'read','intention':'Find how woodland plants compete'},
        {'library_query':'plant competition','research_question':'How do plants compete for light?','reading_mode':'lookup',
         'reading_spot':'floor','action':'sleep'})
    d,_=app.choose()
    assert len(calls)==2 and d['action']=='read' and d['reading_spot']=='floor'
    assert set(calls[1]['schema']['properties'])=={'library_query','research_question','reading_mode','reading_spot'}
    assert 'times_consulted' in calls[1]['prompt']

    # 5. A single possible target is used without asking; drink needs no detail call.
    calls=[];app.model_call=stub(calls,{**base,'action':'drink'});d,_=app.choose()
    assert len(calls)==1 and d['object_id']==''

    # 6. Projects: continuing keeps the milestone he set; starting asks only then for its title.
    calls=[];app.model_call=stub(calls,{**base,'action':'rest','project':'continue','project_id':1});d,_=app.choose()
    assert d['project_id']==1 and d['target_action']=='read' and d['target_sessions']==5 and len(calls)==1
    calls=[];app.model_call=stub(calls,{**base,'action':'observe','project':'start'},
        {'project_title':'Notice which birds visit','target_action':'observe','target_sessions':3});d,_=app.choose()
    assert d['project_id']==0 and d['project_title']=='Notice which birds visit' and len(calls)==2
    calls=[];app.model_call=stub(calls,{**base,'project':'none','project_id':1});d,_=app.choose()
    assert d['project_id']==-1

    # 7. Unavailable mechanics are not offered: no paused jobs or plans exist here.
    allowed=calls[0]['schema']['properties']['action']['enum']
    assert 'resume_work' not in allowed and 'construct' not in allowed and 'rest' in allowed and 'sleep' in allowed

    # 8. Observed repetition is reported as counts only.
    pattern=memory_recall.recent_pattern(app.state)
    assert pattern['readings_not_answering']>=10 and pattern['repeated_excerpts']>=10

    # 9. Identical lessons are recalled once, so repetition cannot crowd out other evidence.
    app.state['current_intention']='woodland plant interactions'
    recalled=memory_recall.recall(app.state,1700)
    keys=[m['text'] for m in recalled];assert len(keys)==len(set(keys))
    assert {m['type'] for m in recalled}>={'reading'} or {m['type'] for m in recalled}>={'lesson'}

print('PASS: small choice schema; details only for the chosen action; memory protected and relevance-ranked on a long life; '
      'unchanged save; uncited IDs rejected; single targets; project milestones; unavailable mechanics hidden; repetition observable.')
