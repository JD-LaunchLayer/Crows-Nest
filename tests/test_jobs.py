"""v0.26.2: posted jobs are real work: the sweep once a day, crates only after a delivery."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import town
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_jobs',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,18,8,0,tzinfo=app.TZ);app.clock();st=app.state
    at='2026-11-18T08:00:00+00:00'
    r=town.trade(st,'job','sweep_post',1,at);assert r['success'] and st['trading']['credit']==1
    r=town.trade(st,'job','sweep_post',1,'2026-11-18T08:40:00+00:00');assert not r['success'] and 'tomorrow' in r['text']
    assert st['trading']['credit']==1
    assert 'tomorrow' in town.board(st)['jobs']['sweep_post']['now']
    r=town.trade(st,'job','sweep_post',1,'2026-11-19T07:30:00+00:00');assert r['success']
    # Crates: only once per delivery.
    st['trading']['last_delivery']='2026-11-16T10:00:00+00:00'
    assert town.trade(st,'job','carry_crates',1,at)['success']
    r=town.trade(st,'job','carry_crates',1,'2026-11-19T09:00:00+00:00');assert not r['success'] and 'delivery' in r['text']
    town.weekly_delivery(st,datetime(2026,11,23,10,0,tzinfo=app.TZ))
    assert town.trade(st,'job','carry_crates',1,'2026-11-23T11:00:00+00:00')['success']
    # A job that is not needed costs only a short visit, not the full job time.
    d={**app.DECISION_DEFAULTS,'action':'trade','trade_mode':'job','trade_item':'sweep_post','intention':'sweep','reason':'r'}
    st['trading']['jobs_done']['sweep_post']=app.now().isoformat();st['paused']=False
    app.start_action(d,1);assert st['pending']['duration']<=300
print('PASS v0.26.2: the sweep once a day, crates once per delivery; a job not needed costs a short visit.')
# v0.30.3: a favour that is the same work as a posted job follows that job's rule; deals are in whole silver;
# Edda's description no longer contradicts the world.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_jobs2',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,3,13,51,tzinfo=app.TZ);app.clock();st=app.state
    at=lambda h,m:datetime(2026,12,3,h,m,tzinfo=app.TZ).isoformat()
    sweep={'kind':'favour','item':'','quantity':1,'credit':1,'minutes':30,'task':'Sweep and tidy the trading post'}
    assert town.check_proposal(st,dict(sweep),st['day'])[0]
    town.apply_proposal(st,dict(sweep),at(13,51),st['day'])
    ok,why=town.check_proposal(st,{**sweep,'task':'Sweep and tidy the trading post (favour-26)'},st['day'])
    assert not ok and 'already agreed' in why, why
    r=town.trade(st,'job',town.keeper(st)['favours'][-1]['id'],1,at(14,18));assert r['success'] and st['trading']['credit']==1
    assert not town.job_open(st,'sweep_post',at(14,30))[0], 'sweeping for Edda is the sweep'
    ok,why=town.check_proposal(st,dict(sweep),st['day']);assert not ok and 'not needed' in why, why
    # Agreed before the work was done another way: it lapses, unpaid.
    st['trading']['last_delivery']=at(9,0)
    town.apply_proposal(st,{'kind':'favour','item':'','quantity':1,'credit':2,'minutes':60,'task':'Carry the delivered crates into the store room'},at(15,0),st['day'])
    assert town.trade(st,'job','carry_crates',1,at(15,10))['success'] and st['trading']['credit']==3
    r=town.trade(st,'job',town.keeper(st)['favours'][-1]['id'],1,at(16,0))
    assert not r['success'] and 'already done' in r['text'] and st['trading']['credit']==3 and not town.keeper(st)['favours']
    p={'kind':'gift','item':'','quantity':1,'credit':.26,'minutes':15,'task':''};town.check_proposal(st,p,st['day']);assert p['credit']==.3
    assert 'roof leaks' not in town.KEEPER_PERSONA and 'irregular' not in town.KEEPER_PERSONA and 'debts' not in town.KEEPER_PERSONA
    assert 'go by those entries exactly' in town.KEEPER_PERSONA
print('PASS v0.30.3: favours for posted work follow its rule; whole silver only; Edda goes by her book.')
# v0.30.16: short of money, Edda still keeps no tab, and lays out what the post can do, without choosing for him.
assert 'part now and part later' in town.KEEPER_PERSONA and 'post buys wood, stone, things he has made' in town.KEEPER_PERSONA
assert 'you do not tell him what to sell' in town.KEEPER_PERSONA
print('PASS v0.30.16: Edda declines a tab kindly and lays out the options.')
