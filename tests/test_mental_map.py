"""v0.26.4: carrying shows where things are as he knows them from his own experience; nothing goes inside a wall."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import world_state
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_map',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,26,11,0,tzinfo=app.TZ);app.clock();st=app.state
    st['memories']=[]
    assert world_state.mental_map(st,app.ACTIONS)==[], 'a stranger knows nowhere'
    st['memories']=[{'kind':'experience','action':'rest','event':'Finished a quiet rest in his cabin.'},
                    {'kind':'experience','action':'read','event':'Read at the reading cabin.'}]
    m=world_state.mental_map(st,app.ACTIONS);text=' '.join(m)
    assert 'inside your cabin' in text and 'reading cabin' in text and 'reading chair' in text, m
    assert 'trading post' not in text and 'café' not in text, 'places he has not been are not on his map'
    req=app.parameter_request({'action':'move_object'});assert req[2]['where_things_are_as_you_know_them']==m
    # The chair can go inside his cabin, but not into a wall.
    r=world_state.move(st,'library_chair',-10,-9);assert r['success'], r
    r=world_state.move(st,'library_chair',-13,-10);assert not r['success'] and 'wall' in r['text']
print('PASS v0.26.4: his map is only what he has been to and handled; the chair can go into his cabin, not into a wall.')
