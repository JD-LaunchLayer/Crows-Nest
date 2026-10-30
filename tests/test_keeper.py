"""Edda Thorne: conversation, bounded bargains, favours, her own memory; and work that slows when tired or dark."""
import copy, importlib.util, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import town, life, world_state

s={'materials':9,'stone':0,'creations':[]};world_state.ensure(s);life.ensure(s);town.ensure(s)
assert s['keeper']['name']=='Edda Thorne' and any(p['id']=='screen' for p in s['built_world']['objects']['internet_cafe']['parts'])
assert any(p['id']=='counter' for p in s['built_world']['objects']['trading_post']['parts'])
# Old saves that already had the town get furnished once.
old={'materials':0,'stone':0,'creations':[]};world_state.ensure(old);life.ensure(old);town.ensure(old)
cafe=old['built_world']['objects']['internet_cafe'];bare=[p for p in cafe['parts'] if p['id'] in ('floor','back','left','right','front_left','front_right','lintel','roof')]
cafe['parts']=bare;base=len(bare);old['built_world'].pop('town_furnished');town.ensure(old);n=len(cafe['parts']);assert n>base
old['built_world'].pop('town_furnished');town.ensure(old);assert len(cafe['parts'])==n, 'never furnished twice'
# Bargains are bounded by the world, whatever is said.
s['trading']['credit']=5
cheap={'kind':'sell_item','item':'lantern','quantity':1,'credit':3,'minutes':0,'task':''}
assert not town.check_proposal(s,cheap,'d')[0], 'below 70% of the board is refused'
fair={**cheap,'credit':4.5};assert town.check_proposal(s,fair,'d')[0]
r=town.apply_proposal(s,fair,'t','d');assert r['success'] and s['possessions']['lantern']==1 and s['trading']['credit']==.5
greedy={'kind':'buy_goods','item':'wood','quantity':6,'credit':5,'minutes':0,'task':''}
assert not town.check_proposal(s,greedy,'d')[0];ok={**greedy,'credit':2.5};assert town.apply_proposal(s,ok,'t','d')['success'] and s['materials']==3
assert not town.check_proposal(s,{**ok,'quantity':10},'d')[0], 'cannot sell goods he does not have'
fav={'kind':'favour','item':'','quantity':1,'credit':3,'minutes':60,'task':'Patch the store-room roof'}
assert town.apply_proposal(s,fav,'t','d')['success'] and s['keeper']['favours'][0]['id']=='favour-1' and 'favour-1' in town.board(s)['jobs']
credit=s['trading']['credit'];assert town.trade(s,'job','favour-1',1,'t')['success'] and s['trading']['credit']==credit+3 and not s['keeper']['favours']
gift={'kind':'gift','item':'','quantity':1,'credit':1,'minutes':0,'task':''}
assert town.apply_proposal(s,gift,'t','d')['success'] and not town.check_proposal(s,gift,'d')[0], 'one gift a day'
assert not town.check_proposal(s,{**gift,'credit':5},'d2')[0]
town.remember(s,'He asked about the roof and came back to fix it.',.6,'t');town.remember(s,'He came back and fixed the roof as he asked.',.6,'t')
assert len(s['keeper']['notes'])>=1 and s['keeper']['warmth']>0

# Work pace: fresh daylight work is normal; exhaustion and darkness slow outdoor work; rest and reading are unaffected.
w={'materials':0,'creations':[]};world_state.ensure(w);life.ensure(w);w['daylight']=.9
assert life.work_rate(w,'fell_tree')==1 and life.work_rate(w,'read')==1
w['body'].update(exertion=.9,sleep_debt=10);tired=life.work_rate(w,'fell_tree');assert tired<.8
w['daylight']=0;assert abs(life.work_rate(w,'fell_tree')-tired*.5)<1e-9 and life.work_rate(w,'rest')==1
w['possessions']={'lantern':1};assert abs(life.work_rate(w,'fell_tree')-tired)<1e-9

# Conversation in his life: Edda replies from her persona; an accepted, valid offer is settled when the talk ends.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_keeper_test',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,1,12,0,tzinfo=app.TZ);app.state['paused']=False;app.state['trading']['credit']=6
    seen=[]
    def model(prompt,schema,limit=650,purpose='other',system=None):
        seen.append((purpose,system))
        if 'action' in schema['properties']:
            return {'action':'talk','intention':'Get a light for the evenings','reason':'It is dark early.','next_step':'','wish':'','wish_reason':'',
                    'project':'none','project_id':0,'memory_ids_used':[]},1
        if purpose=='parameters:talk':return {'opening':'Good morning. Do you sell anything for light?','hope':'a lantern'},1
        if purpose=='keeper':return {'reply':'Morning! The lantern is six, but for a new face, five.','note_about_crow':'Polite; wants a lantern for the dark.',
            'warmth':.4,'proposal':{'kind':'sell_item','item':'lantern','quantity':1,'credit':5,'minutes':0,'task':''}},1
        if purpose=='talk':return {'say':'Five sounds fair, thank you.','accept_offer':True,'leave':False},1
        return {},1
    app.model_call=model
    d=app.decide_and_start(app.runtime['generation'])
    assert d and ('keeper',town.KEEPER_PERSONA)==next(x for x in seen if x[0]=='keeper') and app.state['pending']['reading']['agreed']['credit']==5
    app.tick(app.state['pending']['remaining']);m=app.finish_action()
    assert app.state['possessions']['lantern']==1 and app.state['trading']['credit']==1 and 'Edda' in m['event'] and app.state['keeper']['talks']==1
    assert m['world_result']['conversation'][1]['who']=='Edda'
print('PASS: furnished café and post (also for old saves); Edda bargains within the board, buys only goods he has, agrees favours he can do as jobs, '
      'gives rarely; her own memory and warmth; pace slows with exhaustion and outdoor darkness, lantern helps; conversations settle real deals.')
