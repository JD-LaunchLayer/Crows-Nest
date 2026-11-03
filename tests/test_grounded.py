"""v0.26.3: darkness shows only the outlines of what is there; Edda knows when the delivery is due; a rest story about a meal ends when digestion has."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import ecology, story, town
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_grounded',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,25,21,0,tzinfo=app.TZ);app.clock();st=app.state
    deep=ecology.observe(st,'deeper_woods','anything',329,0.)['text']
    assert 'tree trunks' in deep and 'bushy' not in deep and 'shrub' not in deep, deep
    edge=ecology.observe(st,'woodland_edge','anything',329,0.)['text']
    assert 'low bushy shapes' in edge, edge
    assert ecology.observe(st,'clearing','anything',329,0.)['text']
    st['trading']['last_delivery']='2026-11-19T10:12:00+00:00'
    assert town.next_delivery(st).startswith('Thursday 26 November'), town.next_delivery(st)
    assert 'nobody else works here' in town.KEEPER_PERSONA
s={'body':{'active_hours':1.}}
def step(action,intention,sens,i):
    m={'id':i,'kind':'experience','action':action,'intention':intention,'at':f't{i}','event':'x'}
    story.note_step(s,m);story.settle_need(s,m,sens);return next(x for x in s['stories'] if x['id']==m['story_id'])
assert step('rest','Let the just-eaten meal digest quietly in the cabin',['Food is still digesting.'],1)['stage']=='started'
assert step('rest','Let the just-eaten meal digest quietly in the cabin',['Beginning to feel sleepy.'],2)['stage']=='done'
assert step('rest','Rest quietly while the repeated asking settles',[],3)['stage']=='started'
print('PASS v0.26.3: dark outlines only of what is there; Edda told when the delivery is due; meal-rest stories end with digestion.')
