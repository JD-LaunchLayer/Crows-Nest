"""v0.31.0: every action is defined once (actions.REGISTRY); the old names are unchanged views of it."""
import contextlib, importlib.util, io, json, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import actions, inner
snap=json.loads((ROOT/'tests'/'registry_snapshot.json').read_text())
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_reg',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    # The same values, in the same order, as the separate tables they replace.
    assert list(app.ACTIONS.items())==list(snap['places'].items())
    assert app.DURATIONS==snap['durations'] and app.ACTION_MENU==snap['menu'] and inner.CHOICES==snap['choices']
    # The same reasons for the same impossibilities, in the same order.
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,19,9,0,tzinfo=app.TZ);app.clock();st=app.state
    st['provisions']['pantry']=0.;st['provisions']['larder']=[];st['provisions']['berries']=0.;st['materials']=0.
    r=app.unavailable_reasons()
    assert r['eat'].startswith('there is nothing to eat') and r['craft']=='I have no wood to carve' and 'hunt' in r
    assert list(r)==[k for k in actions.CHECK_ORDER if k in r]
    assert all(a not in app.available_actions() for a in r) and 'rest' in app.available_actions()
    st['possessions'].update(hunting_bow=1,arrows=3);assert 'hunt' in app.available_actions()
    # Every action has a place, his words and a menu line; anything that can be impossible says why.
    for k,a in actions.REGISTRY.items():
        assert a.place and a.menu and a.choice and (a.impossible is None or a.why), k
print('PASS v0.31.0: one action registry; the old tables, prompts and reasons are unchanged views of it.')
