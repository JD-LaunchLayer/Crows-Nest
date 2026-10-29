import copy
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
root=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import world_state as w
state={'materials':0,'creations':[{'id':1,'name':'Old carving','shape':'orb'}],'location':'workbench'}
world=w.ensure(state)
assert 'carving-1' in world['objects'] and len(world['trees'])==71
assert world['objects']['carving-1']['x']==3
assert abs(w.mass(world['objects']['carving-1']['parts'])['wood']-1)<.02
assert w.collect(state,'wood')['success'] and state['materials']==3 and world['sources']['wood']['stock']==247
before=state['materials'];assert w.fell_tree(state,'tree-0')['success'];assert state['materials']==before
stock=world['trees']['tree-0']['stock'];assert w.collect(state,'wood',3,'tree-0')['success'];assert world['trees']['tree-0']['stock']==stock-3
assert not w.fell_tree(state,'tree-0')['success']
world['tools']['axe']=0;assert not w.fell_tree(state,'tree-1')['success'];assert world['trees']['tree-1']['stage']=='standing'
world['sources']['stone']['stock']=1;assert w.collect(state,'stone',3)['success'] and state['stone']==1
assert not w.collect(state,'stone',3)['success']
parts=[{'shape':'box','material':'wood','color':'#aabbcc','x':0,'y':.1,'z':0,'width':.2,'height':.2,'depth':.2}]
plan=w.propose(state,'Small box','new','',0,0,parts);assert plan['bill']=={'wood':4.0}
state['materials']=0;objects=len(world['objects']);assert not w.construct(state,plan['id'])['success'];assert len(world['objects'])==objects
state['materials']=4;result=w.construct(state,plan['id']);assert result['success'] and state['materials']==0
assert not w.construct(state,plan['id'])['success'] and state['materials']==0
ident=result['object_id'];assert w.move(state,ident,-10,8)['success']
assert not w.move(state,ident,-7.5,10)['success'] and world['objects'][ident]['x']==-10
assert not w.move(state,'library',0,0)['success']
assert not w.move(state,ident,99,0)['success']
state['materials']=4
addition=w.propose(state,'A library addition','add','library',0,0,parts)
oldcount=len(world['objects']['library']['parts']);assert w.construct(state,addition['id'])['success'];assert len(world['objects']['library']['parts'])==oldcount+1
remove=w.propose(state,'Open back wall','remove','library',0,0,remove_part='back');before=state['materials']
assert w.construct(state,remove['id'])['success'];assert not any(p['id']=='back' for p in world['objects']['library']['parts']);assert state['materials']>before
stale=w.propose(state,'Stale plan','add','library',0,0,parts);world['objects']['library']['revision']+=1;assert not w.construct(state,stale['id'])['success']
for value in [float('nan'),float('inf'),-1,True]:
 bad=copy.deepcopy(parts);bad[0]['width']=value
 try:w.validate_parts(bad);raise AssertionError('Invalid dimensions accepted')
 except ValueError:pass
# Persist/reload is ordinary JSON; no objects or stocks reset on restart.
restored=json.loads(json.dumps(state));w.ensure(restored);assert restored['built_world']['trees']['tree-0']['stage']=='felled';assert restored['built_world']['sources']['wood']['stock']==247
with tempfile.TemporaryDirectory() as td:
 folder=pathlib.Path(td)
 shutil.copy(root/'crow.py',folder/'crow.py')
 spec=importlib.util.spec_from_file_location('crow_world_test',folder/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
 app.state['paused']=False
 d={'action':'fell_tree','object_id':'tree-0','reason':'I want timber for something I may build.','intention':'Gather timber.','wish':'','wish_reason':'','creation_name':'','creation_shape':'orb','reading_spot':'standing','library_query':'','project_id':0,'project_title':'','project_status':'active','target_action':'fell_tree','target_sessions':1,'plan_id':0,'destination_x':0,'destination_z':0,'material':'wood','plan_operation':'new','part_id':''}
 app.start_action(d,1);assert app.state['built_world']['trees']['tree-0']['stage']=='standing'
 app.tick(5400);app.finish_action();assert app.state['built_world']['trees']['tree-0']['stage']=='felled' and app.state['materials']==0
 d.update(action='gather',target_action='gather');app.start_action(d,1);app.tick(1200);app.finish_action();assert app.state['materials']==3
 d.update(action='plan',target_action='plan',creation_name='Box',object_id='',destination_x=1,destination_z=1);app.start_action(d,1);app.tick(600);app.finish_action(parts)
 assert app.state['built_world']['plans'][-1]['status']=='proposed';assert app.state['materials']==3
# Long jobs are worked in resumable sessions, not granted instantly.
long_parts=[dict(parts[0],width=1,height=1,depth=1,y=.5)]
state['materials']=500
long_plan=w.propose(state,'A large object','new','',8,0,long_parts)
first=w.construct(state,long_plan['id'],120);assert first['success'] and not first['built'];assert long_plan['id'] not in [o.get('plan_id') for o in world['objects'].values()]
assert state['materials']==500
progress=w.plan_by_id(state,long_plan['id']);assert progress['status']=='in_progress' and progress['work_done_minutes']==120
last=w.construct(state,long_plan['id'],progress['minutes']);assert last['built'] and state['materials']==0
print('PASS: finite material conservation, axe/felling/stumps, partial gathering, paid construction, reuse prevention, placement collision, library edits, salvage, stale plans, durable migration and real-time outcomes.')
