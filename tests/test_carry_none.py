"""v0.25.1: carrying offers 'none', so a wished-for thing that cannot be picked up never moves something else."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_carry',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,12,11,0,tzinfo=app.TZ);app.clock();st=app.state
    import world_state
    objs=world_state.ensure(st)['objects'];portable=[i for i,o in objs.items() if o.get('portable')]
    assert portable, 'the starting world has something portable'
    before={i:(o['x'],o['z']) for i,o in objs.items()}
    where=st.get('location')
    req=app.parameter_request({'action':'move_object'})
    assert 'none' in req[1]['object_id']['enum'] and 'near you' in req[0]
    # A portable thing far from him is not offered as if it were here.
    far=next(iter(portable))
    objs[far]['x'],objs[far]['z']=80,80
    req=app.parameter_request({'action':'move_object'})
    assert far not in req[1]['object_id']['enum'], req[1]['object_id']['enum']
    d={**app.DECISION_DEFAULTS,'action':'move_object','object_id':'none','destination_x':1,'destination_z':1,'intention':'carry the crates','reason':'r'}
    st['paused']=False;app.start_action(d,1)
    assert st['location']==where, 'choosing to carry nothing does not move him'
    app.tick(120);ev=app.finish_action()['event']
    assert ev.startswith('Nothing was carried') and objs[far]['name'] not in ev, ev
    assert {i:(o['x'],o['z']) for i,o in objs.items()}=={**before,far:(80,80)}, 'nothing moved'
    assert st['location']==where
print('PASS v0.25.1: carrying can choose none; nothing else moves; he is not relocated; only what is near is named.')
