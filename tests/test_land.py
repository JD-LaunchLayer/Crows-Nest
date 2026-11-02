"""v0.23: seasonal wild fruit, real crops on his calendar, weekly deliveries, a deeper finite forest and planting."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import garden, life, town, world_state, ecology
TZ=ZoneInfo('Europe/London')
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_land',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    st=app.state
    def at(y,m,d):app.clock(datetime(y,m,d,12,tzinfo=TZ))
    # Wild fruit: grows in late summer, goes over in winter, never regrows off season.
    at(2026,8,10);st['provisions']['berries']=0;life.advance(st,48*3600,'rest');assert st['provisions']['berries']>8
    at(2026,11,10);st['provisions']['berries']=12;life.advance(st,72*3600,'rest');assert st['provisions']['berries']<12*.8
    at(2027,2,1);st['provisions']['berries']=0;life.advance(st,240*3600,'rest');assert st['provisions']['berries']==0
    st['body']['stomach']=0;r=life.consume(st,'eat','berry_patch');assert not r['success'] and 'fruiting season is over' in r['text']
    # Crops: radishes in summer ripen in about a month; tender crops sown in November die; garlic overwinters.
    st['possessions'].update(radish_seeds=1,salad_seeds=1,garlic_bulbs=1)
    g=garden.ensure(st)
    for b in g['beds']:b.update(crop=None,growth=0.,health=1.,moisture=1.,weeds=0.)
    assert garden.work(st,1,'sow','radish_seeds')['success']
    for day in range(40):
        g['beds'][0]['moisture']=1.;g['beds'][0]['weeds']=0.;garden.advance(st,24,190+day)
    assert garden.stage(g['beds'][0])=='ripe' and 'radishes' in garden.look(g['beds'][0])
    h=garden.work(st,1,'harvest');assert h['success'] and 'radishes' in h['text']
    garden.work(st,2,'sow','salad_seeds');garden.work(st,3,'sow','garlic_bulbs')
    for day in range(60):
        for b in g['beds'][1:]:b['moisture']=1.;b['weeds']=0.
        garden.advance(st,24,310+day if 310+day<=365 else 310+day-365)
    assert g['beds'][1]['crop']=='withered', 'salad sown in November is killed by winter'
    assert g['beds'][2]['crop']=='growing' and 0<g['beds'][2]['growth']<.5, 'garlic sits through winter, growing slowly'
    # Weekly delivery on his own calendar tops the standard lines up.
    post=town.ensure(st);post['stock']['provisions_bundle']['qty']=0
    t0=datetime(2026,11,10,9,tzinfo=TZ);town.weekly_delivery(st,t0)
    assert town.weekly_delivery(st,t0+timedelta(days=3)) is None and post['stock']['provisions_bundle']['qty']==0
    assert town.weekly_delivery(st,t0+timedelta(days=7,minutes=1)) and post['stock']['provisions_bundle']['qty']==6
    assert {'seed_potatoes','garlic_bulbs','hazel_sapling'}<=set(post['stock'])
    assert 'reading cabin' in town.KEEPER_PERSONA and 'café' in town.KEEPER_PERSONA
    # The forest: deeper woods exist, nothing regrows, and he can plant.
    w=world_state.ensure(st);before=world_state.forest_state(st)
    assert before['standing_trees']>180 and ecology.AREAS['deeper_woods']
    st['possessions']['hazel_sapling']=1
    bad=world_state.plant_tree(st,'hazel_sapling',2,2,'t');assert not bad['success']
    ok=world_state.plant_tree(st,'hazel_sapling',14,-2,'2026-11-10');assert ok['success'],ok
    tid=ok['tree_id'];assert w['trees'][tid]['stage']=='young' and 'young hazel he planted' in ecology._tree_facts(st,w['trees'][tid],314)[0][1]
    for year in range(9):
        for doy in range(1,366,5):world_state.grow_trees(st,24*5,garden.warmth(doy))
    assert w['trees'][tid]['stage']=='standing', w['trees'][tid]
    years_to_fell=None
    assert world_state.fell_tree(st,tid)['success']
    after=world_state.forest_state(st);assert after['felled_stumps']==before['felled_stumps']+1
    assert 'plant_tree' not in app.available_actions()
    st['possessions']['oak_sapling']=1;assert 'plant_tree' in app.available_actions()
    assert 'woods' in app.decision_context()
print('PASS v0.23: seasonal wild fruit; crops by season on his calendar; weekly deliveries; deeper finite forest; planting grows real trees in years.')
