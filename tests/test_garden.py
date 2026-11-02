"""Garden: water from the spring, weeds, seasons, slow growth, withering, honest harvests."""
import importlib.util, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import garden, life, town, world_state

s={'materials':0,'stone':0,'creations':[]};world_state.ensure(s);life.ensure(s);town.ensure(s);g=garden.ensure(s)
assert s['trading']['stock']['seeds']['qty']==8 and 'sow' in town.ITEM_KNOWLEDGE['seeds'] and 'sow' not in town.POSSESSION_LOOKS['seeds']
assert not garden.work(s,1,'sow')['success'], 'no seeds yet'
s['possessions']['seeds']=2
assert garden.work(s,1,'sow')['success'] and s['possessions']['seeds']==1 and garden.stage(g['beds'][0])=='sown'
water=s['provisions']['water_litres'];assert garden.work(s,1,'water')['success'] and s['provisions']['water_litres']==water-2
# A dry bed does not grow; a tended bed in summer ripens in about three weeks; winter is much slower.
def grow(days,doy,tend=True,bed=0):
    for _ in range(days*4):
        if tend:g['beds'][bed]['moisture']=1;g['beds'][bed]['weeds']=0
        garden.advance(s,6,doy)
summer=dict(g['beds'][0]);grow(22,172);assert garden.stage(g['beds'][0])=='ripe'
assert 'full-grown' in garden.look(g['beds'][0]) and garden.work(s,1,'harvest')['success'] and garden.stage(g['beds'][0])=='empty'
s['possessions']['seeds']=1;garden.work(s,2,'sow');grow(22,355,bed=1);assert garden.stage(g['beds'][1]) in ('sprouting','growing')
# Neglect: left dry it withers; weeds return; looking describes what is visible only.
garden.advance(s,24*10,172);assert garden.stage(g['beds'][1])=='withered' and 'shrivelled' in garden.look(g['beds'][1])
assert 'weeds' in garden.look(g['beds'][2]) and not any(ch.isdigit() for ch in garden.look(g['beds'][2])[6:])
assert not garden.work(s,3,'harvest')['success']
s['provisions']['water_litres']=1;assert not garden.work(s,3,'water')['success'], 'needs spring water'
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_garden_test',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,1,12,0,tzinfo=app.TZ);app.state['paused']=False
    before=dict(app.state['garden']['beds'][0]);app.tick(3600*24);assert app.state['garden']['beds'][0]['moisture']<before['moisture']
    app.state['paused']=True;frozen=dict(app.state['garden']['beds'][0]);app.tick(3600*24);assert app.state['garden']['beds'][0]==frozen
    app.state['paused']=False
    d={**app.DECISION_DEFAULTS,'action':'garden','reason':'Look at the beds.','intention':'See what the beds need','bed':2,'garden_task':'weed'}
    app.start_action(d,1);assert app.state['pending']['remaining']==1200
    app.tick(1200);m=app.finish_action();assert 'Pulled the weeds' in m['event'] and app.state['garden']['beds'][1]['weeds']==0
    assert app.decision_context()['garden_beds'][0].startswith('Bed 1')
print('PASS: seeds from the post; sowing, watering from the spring, weeding, harvesting; seasons; dryness withers; '
      'nothing changes while paused; observable descriptions only; garden work in his life.')
