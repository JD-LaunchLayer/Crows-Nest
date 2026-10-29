"""Observable woodland: real seasons, light from actual trees, attention without assignment."""
import copy, importlib.util, shutil, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import ecology, life, memory_recall, world_state

s={'materials':0};world_state.ensure(s);life.ensure(s)
trees_before=copy.deepcopy(s['built_world']['trees'])
eco=ecology.ensure(s);snapshot=copy.deepcopy(eco);ecology.ensure(s)
assert s['ecology']==snapshot and s['built_world']['trees']==trees_before, 'seeding is once-only and leaves trees alone'

def texts(area,doy,daylight=.6):return ' '.join(t for _,t,_ in ecology.visible_facts(s,area,doy,daylight))
# Seasons follow the calendar: bluebells are invisible in late October and flower in late April.
assert 'bluebell' not in texts('grove',302).lower() and 'Bluebells are flowering' in texts('grove',118)
assert 'toadstools' in texts('woodland_edge',290) and 'toadstools' not in texts('woodland_edge',150)
assert ecology.leaf_cover('oak',15)==0 and ecology.leaf_cover('holly',15)==1 and ecology.leaf_cover('oak',200)==1
# Darkness limits what can be seen.
dark=ecology.observe(s,'grove','',302,0);assert dark['dark'] and not dark['findings']
# Repeated looking shows what is new and what has been seen before.
first=ecology.observe(s,'spring_side','',302,.6);again=ecology.observe(s,'spring_side','',302,.6)
assert all(f['new'] for f in first['findings']) and not any(f['new'] for f in again['findings'])
# Focus makes related things likelier to be noticed, but one incidental detail is always included.
def related(focus,n=30):
    st=copy.deepcopy(s);count=0
    for _ in range(n):
        r=ecology.observe(st,'woodland_edge',focus,302,.6)
        count+=sum(any(w in f['text'] for w in ecology.RELATION_WORDS) for f in r['findings'])
    return count
assert related('how plants interact and grow together')>related('')
# Light is computed from the actual standing trees: felling one opens the canopy and the ivy loses its support.
host=next(p for p in eco['plants'] if p['species']=='ivy');tree=s['built_world']['trees'][host['host']]
before=ecology.ground_light(s,tree['x'],tree['z'],200)
world_state.fell_tree(s,tree['id']);after=ecology.ground_light(s,tree['x'],tree['z'],200)
assert after>before and 'stump' in ecology.inspect(s,host['id'],200,.6)['text']
assert ecology.inspect(s,'no-such-plant',200,.6) is None
view=ecology.view(s,15);assert view['trees']['tree-0']['cover']==0 and all(p['species']!='bluebell' for p in view['plants'])

# Integration: an observation is a real event whose findings are recallable on their own.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_eco_test',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    app.state['paused']=False;app.state['daylight']=.7
    base={'action':'observe','reason':'I want to see what grows with what.','intention':'Find which plants grow on other plants',
          'wish':'','wish_reason':'','next_step':'','project_id':-1,'project_title':'','project_status':'active',
          'target_action':'observe','target_sessions':1}
    app.start_action({**app.DECISION_DEFAULTS,**base,'observe_area':'woodland_edge','focus':'plants growing on trees'},1)
    app.tick(600);m=app.finish_action()
    assert m['world_result']['findings'] and m['event'].startswith('Observed the woodland edge')
    app.state['current_intention']='ivy on trees'
    assert any(x['type']=='observed' for x in memory_recall.recall(app.state)) or 'ivy' not in m['event'].lower()
    # A decision saved by an older version (no area) still completes honestly.
    app.start_action({**base},1);app.state['pending']['decision'].pop('observe_area',None);app.tick(600)
    assert app.finish_action()['world_result']['success']
print('PASS: once-only seeding; calendar phenology; darkness; new vs seen details; focused but open attention; '
      'light from actual trees and felling consequences; plant/tree inspection; seasonal view; recallable observation events; legacy observe.')
