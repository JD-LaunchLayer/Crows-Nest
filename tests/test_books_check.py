"""tools/books_check.py: the post's book checked against his purse, read-only."""
import contextlib, importlib.util, io, json, shutil, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_books',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,3,13,0,tzinfo=app.TZ);app.clock();st=app.state;t=app.town
    at=lambda h:datetime(2026,12,3,h,0,tzinfo=app.TZ).isoformat()
    st['materials']=40
    t.trade(st,'sell','wood',3,at(13));t.trade(st,'job','sweep_post',1,at(14))
    t.trade(st,'buy',next(k for k,v in st['trading']['stock'].items() if v['price']<=3),1,at(15))
    t.apply_proposal(st,{'kind':'favour','item':'','quantity':1,'credit':1.5,'minutes':30,'task':'Tie the kindling'},at(16),st['day'])
    t.trade(st,'job',t.keeper(st)['favours'][-1]['id'],1,at(17))
    p=Path(td)/'save.json';p.write_text(json.dumps(st));before=p.read_text()
    run=lambda q:subprocess.run([sys.executable,str(ROOT/'tools/books_check.py'),q,'--save',str(p)],capture_output=True,text=True).stdout
    out=run('12-03')
    assert 'none: every amount in the book matches' in out and 'they agree' in out and out.count('· ')>=5, out
    assert p.read_text()==before, 'read-only'
    app.event('Talked with Edda Thorne. Crow: “I think there is a 5 silver gap.” Edda: “Let us look.”','checking',action='talk')
    out=run('5 silver');assert 'first comes up' in out and '5 silver gap' in out, out
    p.write_text(json.dumps(st));before=p.read_text()
    st['trading']['ledger'][-1]['credit_after']+=.5;st['trading']['credit']+=.5;p.write_text(json.dumps(st))
    out=run('12-03');assert 'the purse moved 2 gold, the entry says 1 gold 5 silver' in out, out
    st['trading']['credit']+=.3;p.write_text(json.dumps(st))
    assert 'THEY DIFFER' in run('12-03')
print('PASS tools/books_check: the post\'s book and his purse checked against each other, read-only.')
