"""v0.34.1: what he cannot do just now is shown plainly beside what he can, and eating the last of the food says so.

On 2026-12-20 he ate the last serving at 06:24, slept, woke believing he still had bread, and tried to eat it by
handling his radish seeds and reaching into a heap that was not there. Eating was simply missing from his list.
"""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
td = tempfile.mkdtemp(); shutil.copy(ROOT / 'crow.py', Path(td) / 'crow.py')
spec = importlib.util.spec_from_file_location('crow_cannot', Path(td) / 'crow.py'); app = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(app)
app.CLOCK_OVERRIDE = lambda: datetime(2026, 12, 20, 15, 0, tzinfo=app.TZ); app.clock()
import foods
st = app.state
st['provisions']['larder'] = [{'food': 'provisions', 'servings': 1., 'spoils_at': None}]; st['provisions']['pantry'] = 1.
st['provisions']['berries'] = 0; st['body']['stomach'] = 5
r = app.life.consume(st, 'eat', 'food_store'); assert r['success'] and 'the last of it' in r['text'], r
seen = []
app.model_call = lambda p, s, *a, **k: (seen.append(p) or ({'action': 'rest', 'intention': 'i', 'reason': 'r', 'next_step': '', 'wish': '',
                                                             'wish_reason': '', 'project': 'none', 'which_project': ''}, 0))
app.choose_action()
assert 'Not possible just now:' in seen[-1] and 'nothing to eat' in seen[-1], seen[-1][:1500]
print('PASS v0.34.1: what he cannot do just now is shown beside what he can; the last serving says it was the last.')
