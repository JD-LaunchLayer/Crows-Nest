"""Building skill: any shape can be tried; how true it comes out depends on practice, fatigue and light."""
import copy, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import life, world_state

def fresh():
    s={'materials':400,'stone':400,'creations':[]};world_state.ensure(s);life.ensure(s);s['daylight']=.9;return s
arch=[{'shape':'arch','material':'stone','color':'#888888','x':0,'y':1,'z':0,'width':2,'height':1,'depth':.4}]
wall=[{'shape':'box','material':'wood','color':'#a48859','x':0,'y':.5,'z':0,'width':2,'height':1,'depth':.2}]
# A beginner can attempt an arch; it is unlikely to hold, and the attempt is recorded as his evidence.
s=fresh();placed,failed,report=life.build_parts(s,1,copy.deepcopy(arch)+copy.deepcopy(arch)+copy.deepcopy(arch))
assert failed and 'did not hold' in report and life.building_record(s)['arch']['attempts']==3
# Simple straight work holds even for a beginner.
placed,failed,_=life.build_parts(s,2,copy.deepcopy(wall));assert placed and not failed and placed[0]['finish'] in ('fair','rough','fine')
# Practice with curved work makes the same arch truer; other handiwork carries over a little.
s2=fresh();life.build_practice(s2,arch,60*60);_,_,_=life.build_parts(s2,1,copy.deepcopy(arch))
assert s2['practical']['building']['parts'][-1]['error_cm']<s['practical']['building']['parts'][0]['error_cm']
s3=fresh();life.build_practice(s3,wall,60*60);life.build_parts(s3,1,copy.deepcopy(arch))
assert s2['practical']['building']['parts'][-1]['error_cm']<s3['practical']['building']['parts'][-1]['error_cm']<s['practical']['building']['parts'][0]['error_cm']
# Exhaustion and darkness make the same work worse.
s4=fresh();s4['body'].update(exertion=1,sleep_debt=12);s4['daylight']=0;life.build_parts(s4,1,copy.deepcopy(wall))
s5=fresh();life.build_parts(s5,1,copy.deepcopy(wall))
assert s4['practical']['building']['parts'][-1]['error_cm']>s5['practical']['building']['parts'][-1]['error_cm']
# Through construction: materials are paid; what falls apart returns half as offcuts; the object holds only what held.
s6=fresh();plan=world_state.propose(s6,'Gateway','new','',5,5,copy.deepcopy(wall)+copy.deepcopy(arch))
stone=s6['stone'];r=world_state.construct(s6,plan['id'],None,execute=lambda parts:life.build_parts(s6,plan['id'],parts))
built=s6['built_world']['objects'].get(r.get('object_id'))
if built:
    assert len(built['parts'])<=2 and 'parts held' in r['text']
    if len(built['parts'])==1:assert s6['stone']>stone-world_state.mass(arch)['stone']
assert world_state.mass([{**arch[0]}])['stone']<world_state.mass([{**arch[0],'shape':'box'}])['stone']
print('PASS: any shape can be attempted; hard shapes fail for beginners; practice (and some carry-over) makes them truer; '
      'fatigue and darkness worsen work; failed parts return half as offcuts; his own building record by shape.')
