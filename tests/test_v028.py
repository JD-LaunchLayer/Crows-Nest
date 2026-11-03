"""v0.28: a body clock (drowsier late in the dark; a sleep begun in the dark runs to first light); lit buildings after dark;
the post's ledger readable; promises lapse after about five days."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import town, story, life
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_v028',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    # Late evening in the dark: drowsier than the same idle hours by day.
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,2,22,0,tzinfo=app.TZ);app.clock();st=app.state;b=st['body']
    b['sleep_debt']=0;life.advance(st,3*3600,'reflect');night=b['sleep_debt']
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,2,11,0,tzinfo=app.TZ);app.clock()
    b['sleep_debt']=0;life.advance(st,3*3600,'reflect');day=b['sleep_debt']
    assert night>day+1, (night,day)
    # A sleep begun at 23:00, even if he needs little, runs on until first light; a daytime nap does not.
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,2,23,0,tzinfo=app.TZ);app.clock();st['paused']=False;b['sleep_debt']=1
    d={**app.DECISION_DEFAULTS,'action':'sleep','intention':'sleep','reason':'r'};app.start_action(d,1)
    wake=datetime(2026,12,2,23,0,tzinfo=app.TZ)+timedelta(seconds=st['pending']['duration'])
    assert wake.date().day==3 and 7<=wake.hour<=8, wake
    st['pending']=None
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,2,14,0,tzinfo=app.TZ);app.clock();b['sleep_debt']=1;app.start_action(d,1)
    assert st['pending']['duration']<2*3600
    st['pending']=None
    # Lit buildings after dark only.
    assert 'lit_after_dark' not in app.decision_context()
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,2,2,30,tzinfo=app.TZ);app.clock()
    assert any('reading cabin' in x for x in app.decision_context()['lit_after_dark'])
    # The ledger can be read at the post.
    town.trade(st,'job','sweep_post',1,'2026-12-02T09:00:00+00:00')
    assert any('sweep' in e.lower() for e in town.board(st)['ledger_latest_entries'])
    # Promises lapse after about five days; recent ones stay open.
    st['promises']=[];old=story.add_promise(st,'I will come Monday 30 November at 13:00','Edda Thorne','2026-11-25T10:00:00+00:00')
    new=story.add_promise(st,'I will weed the bed tomorrow','Edda Thorne','2026-12-01T10:00:00+00:00');story.age(st)
    assert old['status'].startswith('lapsed') and new['status']=='open'
print('PASS v0.28: body clock; sleep in the dark runs to first light; lit buildings after dark; readable ledger; promises lapse.')
# v0.28.1: a 'none' target touches nothing; his purse can be opened and counted.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_v0281',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,2,15,0,tzinfo=app.TZ);app.clock();st=app.state;st['paused']=False
    import interactions, copy
    before=copy.deepcopy(st['built_world']['objects'])
    d={**app.DECISION_DEFAULTS,'action':'interact','verb':'place_on','object_id':'none','other_id':'workbench','interaction_params':{'part_id':'top'},'intention':'open my purse','reason':'r'}
    interactions.prepare(st,d);app.start_action(d,1);app.tick(400);ev=app.finish_action()['event']
    assert ev.startswith('Nothing was done') and st['built_world']['objects']==before, ev
    st['trading']['credit']=1.;d={**app.DECISION_DEFAULTS,'action':'inspect','object_id':'purse','intention':'count my purse','reason':'r'}
    assert 'purse' in app.parameter_request({'action':'inspect'})[1]['object_id']['enum']
    app.start_action(d,1);app.tick(120);ev=app.finish_action()['event'];assert 'Opened his purse' in ev and '1 gold' in ev, ev
print('PASS v0.28.1: none touches nothing; the purse opens and counts.')
# v0.29.3: a quiet rest eases sleepiness a little (far less than sleep); sitting awake doing nothing still adds to it.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_v0293',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,7,3,0,tzinfo=app.TZ);app.clock();st=app.state;b=st['body']
    b['sleep_debt']=9;life.advance(st,3600,'rest');rested=b['sleep_debt']
    b['sleep_debt']=9;life.advance(st,3600,'sleep');slept=b['sleep_debt']
    b['sleep_debt']=9;life.advance(st,3600,'reflect');awake=b['sleep_debt']
    assert slept<rested<9<awake, (slept,rested,awake)
print('PASS v0.29.3: rest eases sleepiness a little; sleep far more.')
