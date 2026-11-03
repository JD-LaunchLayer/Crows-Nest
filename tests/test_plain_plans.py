"""v0.26.5: a failed blueprint drawing is explained plainly, never as a 'solid parts' rule."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import world_state
for reason in ['A plan needs 1–16 solid parts','Invalid part dimension y','A part would be buried below ground','Unsupported part shape']:
    t=world_state.plain_drawing_problem(reason);assert 'solid part' not in t and 'needs no materials' in t, t
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_plans',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,27,11,0,tzinfo=app.TZ);app.clock();st=app.state
    d={**app.DECISION_DEFAULTS,'action':'plan','creation_name':'Monday trip plan','intention':'plan the trip','reason':'r'}
    st['paused']=False;app.start_action(d,1);app.tick(700);ev=app.finish_action({'invalid_geometry':'Invalid part dimension y'})['event']
    assert 'too high' in ev and 'solid part' not in ev, ev
print('PASS v0.26.5: blueprint failures are explained in plain words; no phantom "solid part" rule.')
