"""v0.25: birds by look and place only, the same for the view and his senses; 'past' steers away; supplies carry units."""
import contextlib, importlib.util, io, json, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import birds, ecology, life
NAMES=['robin','blackbird','pigeon','tit','magpie','crow','wren','jay','chaffinch']
assert not any(n in b['look'] for b in birds.BIRDS for n in NAMES), 'never named'
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_birds',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,12,11,0,tzinfo=app.TZ);app.clock();st=app.state
    view=birds.view(st,ecology,1.);assert len(view)>=8 and all({'x','y','z','mode','colours'}<=set(v) for v in view)
    assert birds.where(st,ecology,1.)==birds.where(st,ecology,1.), 'deterministic for a moment'
    night=birds.where(st,ecology,0.);assert all(w['mode']=='roost' for w in night)
    # What he can notice matches the view, with no names and no explanations.
    seen=[]
    for area in ecology.AREAS:seen+=birds.facts(st,ecology,area,1.)
    assert seen and all(t.startswith('A ') and ' is ' in t for _,t in seen)
    # A bird counts as seen once, wherever it perches next.
    assert ecology.fact_key('bird-1','A x is on a low branch of tree-3.')==ecology.fact_key('bird-1','A x is on the ground near (1, 2).')
    r=ecology.observe(st,'clearing','birds',316,1.);assert 'bird' in json.dumps(r['findings']) or r['edge']
    # 'past tree-56' is not a look at tree-56.
    assert ecology._negated('unrecorded plant past tree-56 and tree-21',len('unrecorded plant past '))
    s=app.decision_context()['supplies'];assert set(s)=={'ready_food_servings','in_the_provisions_chest','fruit_on_bushes_servings','spring_water_litres'}
    # Favours say how they are done; objects are described in words, not raw data.
    import town;town.apply_proposal(st,{'kind':'favour','task':'Carry the crates in','minutes':60,'credit':2},'t',1)
    fav=app.decision_context()['people'][0]['open_favours'][0];assert 'trade, job favour-' in fav
    d={**app.DECISION_DEFAULTS,'action':'inspect','object_id':'workbench','intention':'look','reason':'r'}
    st['paused']=False;app.start_action(d,1);app.tick(60);ev=app.finish_action()['event'];assert 'fixed in place' in ev and not ev.startswith('Inspected {')
print('PASS v0.25: birds by look and place only, deterministic, roosting at night; seen once each; "past" steers away; supplies carry units.')
