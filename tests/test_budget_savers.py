"""v0.36.7: routine repeats are not reflected on; a quiet night in bed is a longer stretch. Both save his budget."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
td = tempfile.mkdtemp(); shutil.copy(ROOT / 'crow.py', Path(td) / 'crow.py')
spec = importlib.util.spec_from_file_location('crow_budget', Path(td) / 'crow.py'); app = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(app)
def at(h):
    app.CLOCK_OVERRIDE = lambda: datetime(2026, 12, 21, h, 0, tzinfo=app.TZ); app.clock()
    return app.state
st = at(2); b = st['body']; b.update(chill=0., sleep_debt=1., hydration=90., reserve=90., stomach=20.)
rest = {**app.DECISION_DEFAULTS, 'action': 'rest', 'intention': 'stay under the covers', 'reason': 'r'}
app.start_action(rest, 1); assert st['pending']['duration'] == 45 * 60, st['pending']['duration']
app.finish_action(); first = st['reflection_pending']
app.start_action(rest, 1); app.finish_action()
assert first is not None and st['reflection_pending'] is None, 'the second rest in a row is not reflected on'
b['hydration'] = 40
app.start_action(rest, 1); assert st['pending']['duration'] != 45 * 60, 'thirsty: an ordinary rest'
app.finish_action()
st = at(14); b['hydration'] = 90
app.start_action(rest, 1); assert st['pending']['duration'] != 45 * 60, 'by day: an ordinary rest'
app.finish_action()
drink = {**app.DECISION_DEFAULTS, 'action': 'drink', 'intention': 'drink', 'reason': 'r'}
app.start_action(drink, 1); app.finish_action(); assert st['reflection_pending'] is not None, 'a change of activity is reflected on'
print('PASS v0.36.7: routine repeats are not reflected on; a quiet night in bed is a longer stretch.')
