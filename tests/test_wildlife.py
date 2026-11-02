"""v0.26: foods with their own fill, deer by look only, hunting with real consequences, birds that slowly come to trust him."""
import contextlib, importlib.util, io, json, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import birds, ecology, foods, wildlife, town
NAMES=['deer','roe','venison','robin','blackbird','buck','doe','fawn']
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_wild',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,16,7,40,tzinfo=app.TZ);app.clock();st=app.state
    # ---- foods: old pantry becomes plain provisions; each food fills by its own amount, unseen ----
    st['provisions']['pantry']=6.;st['provisions'].pop('larder',None)
    assert foods.view(st)=={'bread, cheese and dried fruit':6.}
    foods.add(st,'berries',2);assert st['provisions']['pantry']==8.
    supplies=json.dumps(app.decision_context()['supplies'])
    assert 'fill' not in supplies and '22' not in supplies, 'numbers are never shown'
    st['body']['stomach']=0;r=app.life.consume(st,'eat','food_store','berries');light=st['body']['stomach']
    st['body']['stomach']=0;r=app.life.consume(st,'eat','food_store','provisions');full=st['body']['stomach']
    assert light<full and 'wild fruit' in r['text'] or 'bread' in r['text']
    # ---- deer: seen by look, never named; drawn in the view ----
    view=wildlife.view(st,ecology,.5);assert len(view)==5 and all({'x','z','doing'}<=set(v) for v in view)
    seen=[t for a in ecology.AREAS for _,t in wildlife.facts(st,ecology,a,.5)]
    assert seen and not any(n in t.lower() for t in seen for n in NAMES), seen[:2]
    assert ecology.fact_key('deer-2','A x is browsing near (1, 2).')==ecology.fact_key('deer-2','A x is lying down near (3, 4).')
    # ---- the bow is on Edda's shelves; hunting appears only once he owns bow and arrows ----
    assert 'hunting_bow' in town.ensure(st)['stock'] and 'arrows' in town.ensure(st)['stock']
    assert 'hunt' not in app.available_actions()
    st['possessions'].update(hunting_bow=1,arrows=6);assert 'hunt' in app.available_actions()
    # ---- a hunt: outcomes are real; a kill gives a carcass that must be cut up, meat that spoils unless smoked ----
    st['practical']['archery_hours']=40.
    outcomes=set();killed=None
    for seed in range(60):
        area=wildlife.herd_area(st,ecology,.5)[0]
        r=wildlife.hunt(st,ecology,area,.5,0.,seed);outcomes.add(r['text'].split('.')[0][:22])
        if wildlife.ensure(st)['carcasses']:killed=r;break
        wildlife.ensure(st)['spooked_until']=0;st['possessions']['arrows']=6
    assert killed and not any(n in killed['text'].lower() for n in NAMES), killed
    assert 'butcher' in app.available_actions()
    alive=sum(d['alive'] for d in wildlife.ensure(st)['deer']);assert alive==4
    r=wildlife.butcher(st,1.);assert r['success'] and st['possessions']['hide']==1 and 'venison' in foods.kinds(st)
    assert 'preserve' in app.available_actions()
    st['materials']=10;r=wildlife.preserve(st);assert r['success'] and 'smoked venison' in foods.kinds(st)
    # Fresh meat goes off: jump a week on and it is thrown out; smoked meat stays.
    foods.add(st,'venison',3)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,24,8,0,tzinfo=app.TZ);app.clock()
    gone=foods.advance(st);assert any(l['food']=='venison' for l in gone) and 'smoked venison' in foods.kinds(st)
    # A carcass left too long is lost.
    wildlife.ensure(st)['carcasses'].append({'id':'deer-x','look':'slender animal','kg':18,'killed_day':0,'small':False})
    assert wildlife.advance(st) and not wildlife.ensure(st)['carcasses']
    # ---- birds: trust grows slowly with food they eat, never with food they ignore; hunting sets it back ----
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,24,11,0,tzinfo=app.TZ);app.clock()
    foods.add(st,'provisions',10);w=wildlife.ensure(st);w['trust'].clear()
    for k in range(12):
        app.CLOCK_OVERRIDE=lambda k=k:datetime(2026,11,25+k//2,10+3*(k%2),0,tzinfo=app.TZ);app.clock()
        for _ in range(3):wildlife.put_out_food(st,ecology,'clearing','provisions',1.)
    assert w['trust'].get('bird-1',0)<.7, 'a few days is not enough to tame even the boldest'
    assert w['trust'].get('bird-1',0)>w['trust'].get('bird-2',0)>0, w['trust']   # the robin-like bird is the least wary
    assert w['trust'].get('bird-7',0)==0, 'the wren-like bird eats none of it'
    r=wildlife.put_out_food(st,ecology,'clearing','provisions',1.);assert 'bird' in r['text'] and not any(n in r['text'].lower() for n in NAMES)
    before=w['trust']['bird-1'];wildlife._set_back_birds(st,'clearing',.1);assert w['trust']['bird-1']<before
    # A bird that trusts him spends time about the cabin.
    w['trust']['bird-1']=.95;spots=set()
    for h in range(9,16):
        app.CLOCK_OVERRIDE=lambda h=h:datetime(2026,11,24,h,0,tzinfo=app.TZ);app.clock()
        spots|={x['label'] for x in birds.where(st,ecology,1.) if x['id']=='bird-1'}
    assert any('cabin' in s or 'chest' in s for s in spots), spots
    # The character sheet keeps the real names for Jordan only.
    assert wildlife.sheet()['birds'][0]['species']=='European robin'
    assert 'species' not in json.dumps(birds.view(st,ecology,1.))
print('PASS v0.26: foods fill by their own unseen amounts; deer by look only; hunting, butchering, spoiling and smoking; birds come to trust him slowly.')
# v0.26.1: on a walk looking for anything new, animals there are noticed before one more unrecorded tree.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_wild2',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,16,13,0,tzinfo=app.TZ);app.clock();st=app.state
    area=wildlife.herd_area(st,ecology,.6)[0]
    r=ecology.observe(st,area,'anything not yet recorded',320,.6,limit=3)
    assert 'animal on long thin legs' in r['text'], r['text'][:300]
    r=ecology.observe(st,area,'an unrecorded shrub, not an animal',320,.6,limit=3)
    assert 'animal on long thin legs' not in r['text']
print('PASS v0.26.1: animals catch the eye on a general look, and stay out of it when he says he is not looking for them.')
