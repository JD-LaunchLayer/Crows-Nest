"""Steady fast clock for the main Crow, and keeping the twin's life with an honest note and a backup."""
import importlib.util, json, shutil, sys, tempfile
from datetime import datetime, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import promote_twin

def load(folder,config=None):
    shutil.copy(ROOT/'crow.py',folder/'crow.py')
    if config:(folder/'crow-config.json').write_text(json.dumps(config))
    spec=importlib.util.spec_from_file_location('crow_speed_'+folder.name,folder/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    return app

with tempfile.TemporaryDirectory() as td:
    a=Path(td)/'fast';a.mkdir();app=load(a,{'time_scale':24})
    assert app.TIME_SCALE==24 and app.state['crow_clock']['scale']==24
    start=app.now();app.state['paused']=False
    app.tick(3600)  # one lived hour
    assert abs((app.now()-start).total_seconds()-3600)<1 and app.state['body']['active_hours']>=.99
    app.state['paused']=True;frozen=app.now();app.tick(3600);assert app.now()==frozen, 'no time passes while paused'
    app.persist();again=load(a,{'time_scale':1})
    assert again.now()==frozen and again.state['crow_clock']['scale']==1, 'his calendar is never wound back to real time'
    b=Path(td)/'normal';b.mkdir();plain=load(b)
    assert plain.TIME_SCALE==1 and 'crow_clock' not in plain.state and abs((plain.now()-datetime.now(plain.TZ)).total_seconds())<5

    # Keeping the twin's life: backup first, twin calendar kept, honest note, real spend ledger kept.
    real=Path(td)/'real';real.mkdir();twin=Path(td)/'twin';twin.mkdir()
    (real/'crow-save.json').write_text(json.dumps({'memories':[{'id':1,'event':'Real life.'}],'next_memory_id':2,'model_spend':{'total_usd':.4}}))
    (real/'crow-events.jsonl').write_text('{"id":1}\n')
    tw={'memories':[{'id':1,'event':'Real life.'},{'id':2,'event':'Twin life.'}],'next_memory_id':3,'day':40,'model_spend':{'total_usd':9},
        'twin':{'started_virtual':'2026-10-29T20:18:00+00:00','virtual_now':'2026-11-12T09:00:00+00:00'}}
    (twin/'crow-save.json').write_text(json.dumps(tw));(twin/'crow-events.jsonl').write_text('{"id":1}\n{"id":2}\n')
    backup=promote_twin.promote(real,twin,confirm=False)
    kept=json.loads((real/'crow-save.json').read_text())
    assert json.loads((backup/'crow-save.json').read_text())['memories'][-1]['event']=='Real life.'
    assert 'twin' not in kept and kept['crow_clock']['virtual'].startswith('2026-11-12') and kept['paused']
    assert kept['memories'][-1]['event'].startswith('His life continued from the time-lapse twin') and kept['model_spend']['total_usd']==.4
    assert (real/'crow-events.jsonl').read_text().count('\n')==3
    try:promote_twin.promote(real,real,confirm=False);raise AssertionError('a normal save is not a twin')
    except SystemExit:pass
print('PASS: steady scaled clock; lived time drives body and calendar; paused time frozen; calendar never wound back; '
      'twin life kept only after backup, with its calendar, an honest note and the real spending record.')
