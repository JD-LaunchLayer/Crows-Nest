"""v0.36.0 (mapping phase 3): his remembered map: only what he perceived or did; sharper with use, fading with
disuse; out of date until he looks again; brought to mind by what he sees, needs and means to do; never advice."""
import contextlib, importlib.util, io, json, re, shutil, sys, tempfile
from datetime import datetime, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
td = tempfile.mkdtemp(); shutil.copy(ROOT / 'crow.py', Path(td) / 'crow.py')
spec = importlib.util.spec_from_file_location('crow_map', Path(td) / 'crow.py'); app = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(app)
import mind_map, perception, layout
T = [datetime(2026, 12, 21, 11, 0)]
def at(dt=None, loc=None, action='rest'):
    if dt: T[0] = dt
    app.CLOCK_OVERRIDE = lambda: T[0].replace(tzinfo=app.TZ); app.clock()
    st = app.state
    if loc: st['location'] = loc; st['action'] = action; st['in_bed'] = False; layout.follow(st)
    return st
st = at(loc='workbench', action='craft')
# A fresh life knows no places and no landmarks.
m = mind_map.ensure(st); assert not m['landmarks'] and not m['places'], m
assert mind_map.recall(st) == []
# What he noticed becomes remembered; nothing he did not perceive is added.
mind_map.update(st, 'craft', 12.)
seen = {s['handle'] for s in perception.view(st)[:8]}
assert set(m['landmarks']) == seen and seen, (set(m['landmarks']), seen)
assert 'workbench' in m['places'] and 'shop' not in m['places']
# Cold brings back somewhere he was warm, but only somewhere he has really been warm.
st['body']['chill'] = .5
assert not any('warm' in x for x in mind_map.recall(st)), 'never been warm anywhere yet: nothing to remember'
st = at(loc='shop', action='trade'); mind_map.update(st, 'trade', 17.)
st = at(T[0] + timedelta(hours=1), loc='cabin', action='rest'); st['body']['chill'] = .5
r = mind_map.recall(st); assert any("warm in the trading post, by Edda's stove" in x for x in r), r
# Thirst brings back the spring only once he has drunk there.
st['body']['chill'] = 0; st['body']['hydration'] = 40
assert not any('drinking' in x for x in mind_map.recall(st))
mind_map.update(st, 'drink', 8.); st['location'] = 'workbench'
assert any('drinking at the spring basin' in x for x in mind_map.recall(st)), mind_map.recall(st)
st['body']['hydration'] = 90
# Out of date until he looks again: a tree he remembers is felled; the old memory stands, then he notices.
st = at(T[0] + timedelta(hours=1), loc='woods', action='explore'); mind_map.update(st, 'explore', 10.)
tree = next(h for h, v in m['landmarks'].items() if v['kind'] == 'tree' and app.state['built_world']['trees'].get(h, {}).get('stage') == 'standing')
before = m['landmarks'][tree]['words']
app.world_state.fell_tree(st, tree)
assert m['landmarks'][tree]['words'] == before, 'he does not know until he sees it'
st = at(T[0] + timedelta(minutes=20)); mind_map.update(st, 'explore', 10.)
assert tree in {s['handle'] for s in perception.view(st)[:8]}, 'the felled tree is still in sight'
assert any('stump' in c for c in mind_map.changes(st)), m['changes']
# Fading: weeks without seeing them and the landmarks are gone; recall stays within its budget and in plain words.
st = at(T[0] + timedelta(days=70), loc='cabin', action='rest'); old = set(m['landmarks'])
mind_map.update(st, 'rest', 8.)
now_seen = {s['handle'] for s in perception.view(st)[:8]}
assert old - now_seen and not ((old - now_seen) & set(m['landmarks'])), 'what he has not seen for weeks is forgotten'
assert all(mind_map.strength(st, v) >= mind_map.FORGET for v in m['landmarks'].values())
st['current_intention'] = 'look again at the workbench and the bronze dial'; st['body']['chill'] = .5; st['body']['hydration'] = 40
text = ' '.join(mind_map.recall(st)); assert len(text) <= 260 and not re.search(r'\d|\b[a-z]+-\d+\b', text), text
before = json.dumps(st, sort_keys=True, default=str); mind_map.recall(st); mind_map.changes(st)
assert json.dumps(st, sort_keys=True, default=str) == before, 'remembering changes nothing'
# Seeding from a lived life adds only what it shows he did.
s2 = {'memories': [{'kind': 'experience', 'action': 'browse', 'at': '2026-12-01T15:00:00+00:00'},
                   {'kind': 'experience', 'action': 'drink', 'at': '2026-12-01T16:00:00+00:00'}]}
mind_map.seed(s2); assert set(s2['mind_map']['places']) == {'cafe', 'spring'} and s2['mind_map']['places']['cafe']['warm'] == 1
print('PASS v0.36.0: he remembers only what he perceived and did; memories fade, go out of date, and come back on cue.')
