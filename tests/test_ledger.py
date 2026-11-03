"""v0.28.3: the post's book keeps its whole history and he can look up any day or word in it."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import town
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_ledger',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,6,10,0,tzinfo=app.TZ);app.clock();st=app.state
    town.trade(st,'job','sweep_post',1,'2026-12-03T14:28:00+00:00')
    for d in range(80):town._record(st['trading'],f'filler {d}','2026-12-05T10:00:00+00:00')
    from datetime import timedelta
    for k in range(9):town.weekly_delivery(st,datetime(2026,12,6,10,tzinfo=app.TZ)+timedelta(days=7*k))
    assert any('sweep' in l['text'].lower() for l in st['trading']['ledger']), 'deliveries no longer cut the book short'
    for q in ['2026-12-03','12-03','3 December','December 3rd']:
        r=town.trade(st,'ledger',q,1,'t');assert 'Sweep' in r['text'], (q,r)
    assert 'Sweep' in town.trade(st,'ledger','sweep',1,'t')['text']
    assert 'no entry' in town.trade(st,'ledger','2026-11-01',1,'t')['text']
    assert 'ledger' in app.parameter_request({'action':'trade'})[1]['trade_mode']['enum']
print('PASS v0.28.3: the post keeps its whole book; any day or word can be looked up.')
