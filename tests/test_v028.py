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
    b['sleep_debt']=0;life.advance(st,3*3600,'rest');night=b['sleep_debt']
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,2,11,0,tzinfo=app.TZ);app.clock()
    b['sleep_debt']=0;life.advance(st,3*3600,'rest');day=b['sleep_debt']
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
