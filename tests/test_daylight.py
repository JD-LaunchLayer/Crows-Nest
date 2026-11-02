"""v0.21.4: usable light follows the real sky at Wickford (civil twilight, equation of time)."""
import sys, tempfile, shutil, importlib.util, contextlib, io
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py');sys.path.insert(0,str(ROOT))
    spec=importlib.util.spec_from_file_location('crow_daylight',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    tz=ZoneInfo('Europe/London')
    def light(y,m,d,h,mi):app.clock(datetime(y,m,d,h,mi,tzinfo=tz));return app.state['daylight']
    assert light(2026,11,8,7,44)>.12, 'real sunrise is about 07:05; by 07:44 it is light'
    assert light(2026,11,8,16,15)>.12 and light(2026,11,8,16,50)<.12, 'still light at real sunset (16:15); too dim by civil dusk'
    assert light(2026,11,8,6,0)==0 and light(2026,11,8,18,0)==0 and light(2026,11,8,0,0)==0
    assert light(2026,6,21,13,0)>.95 and light(2026,6,21,21,30)>.0 and light(2026,6,21,23,30)==0
print('PASS v0.21.4: daylight follows civil dawn and dusk at Wickford.')
