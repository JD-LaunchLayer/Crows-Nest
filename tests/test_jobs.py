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
