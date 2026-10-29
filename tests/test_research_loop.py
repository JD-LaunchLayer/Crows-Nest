"""Relevance selection and repeat evidence, without assigning another activity."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import reading_journal
with tempfile.TemporaryDirectory() as td:
    folder=Path(td);shutil.copy(ROOT/'crow.py',folder/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_search_loop_test',folder/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    calls=[]
    class Reply:
        def __init__(self,obj):self.obj=obj
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):return json.dumps(self.obj).encode()
    def transport(req,timeout):
        calls.append(req.full_url)
        if 'list=search' in req.full_url:return Reply({'query':{'search':[
            {'pageid':1,'title':'Woodland period','snippet':'An archaeological period.'},
            {'pageid':2,'title':'Plant interaction','snippet':'Relationships between plants.'}]}})
        return Reply({'query':{'pages':[{'title':'Plant interaction','fullurl':'https://en.wikipedia.org/wiki/Plant_interaction','extract':'Plants can compete for available light.'}]}})
    app.urllib.request.urlopen=transport
    app.model_call=lambda prompt,*args:({'page_id':2,'reason':'This candidate concerns plants.'},1)
    source=app.wikipedia('woodland interactions','How do plants interact?')
    assert source['title']=='Plant interaction' and 'pageids=2' in calls[-1]
    calls.clear();app.model_call=lambda *args:({'page_id':0,'reason':'None answers my question.'},1)
    miss=app.wikipedia('unhelpful query','A particular question?');assert miss['unavailable'] and len(calls)==1
    d={'action':'read','reason':'Find an answer.','intention':'Investigate plants.','wish':'','wish_reason':'',
       'library_query':'plants','research_question':'How do they interact?','reading_mode':'leisure',
       'creation_name':'','creation_shape':'orb','project_id':0,'project_title':'','project_status':'active',
       'target_action':'read','target_sessions':1}
    app.state['paused']=False;app.start_action(d,1,source)
    assert app.state['pending']['duration']==0 and app.state['pending']['decision']['reading_mode']=='lookup'
    memory=app.finish_action()
    result={'feeling':'That is a specific fact.','lesson':'Plants can compete for light.','topic':'plants','enjoyment':1,
            'personality_note':'','next_step':'','reading_summary':'Competition for light is described.','answer_status':'partial',
            'meaning':'Some of my question is answered.','valence':.1,'arousal':.1,'importance':.2}
    app.model_call=lambda *args:(copy.deepcopy(result),1);app.reflect(memory)
    old_notes=len(app.state['long_term']);old_interest=app.state['interests']['plants']
    app.start_action(d,1,source);repeated=app.finish_action();assert repeated['new_source_text'] is False
    app.reflect(repeated)
    assert len(app.state['long_term'])==old_notes and app.state['interests']['plants']==old_interest
    assert app.state['reading_log'][-1]['repeat_of']==memory['id']
    context=reading_journal.research_context(app.state)
    assert context['sources'][0]['times_consulted']==2 and context['sources'][0]['answer_status']=='partial'
    snapshot=copy.deepcopy(app.state['reading_log']);reading_journal.ensure(app.state,folder)
    assert app.state['reading_log']==snapshot
print('PASS: relevant candidate instead of first hit; honest no-match result; quick task research; '
      'repeat excerpt labelled and not boosted as fresh learning; progress/repetition context; history retained.')
