"""v0.29.1: a notebook he can write in and read back; it starts empty, keeps pages for good, and pages can come back to mind."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import notebook, memory_recall
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_nb',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,6,10,0,tzinfo=app.TZ);app.clock();st=app.state;st['paused']=False
    assert 'notebook' in app.available_actions()
    d={**app.DECISION_DEFAULTS,'action':'notebook','notebook_mode':'read','note_query':'12-03 cord bundle','intention':'check my notes','reason':'r'}
    app.start_action(d,1);app.tick(1000);ev=app.finish_action()['event']
    assert 'nothing he has written' in ev or 'empty' in ev, ev
    d={**app.DECISION_DEFAULTS,'action':'notebook','notebook_mode':'write','note_title':'12-03 at the post','note_text':'Swept the post for 1 gold. Bought the bread bundle for 3 gold.','intention':'write it down','reason':'r'}
    app.start_action(d,1);app.tick(1000);ev=app.finish_action()['event'];assert 'page 1' in ev, ev
    assert 'bread bundle' in notebook.read(st,'bundle')['text'] and 'page 1' in notebook.read(st,'12-03')['text']
    st['current_intention']='check the bread bundle price';r=memory_recall.recall(st,3000,limit=8)
    assert any(x['type']=='note' for x in r), r
print('PASS v0.29.1: notebook written and read back; empty at first; pages can come back to mind.')
