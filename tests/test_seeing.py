"""v0.35.0 (mapping phase 2): he sees like a person: from where he stands, blocked by walls, shortened by dark, a few
things noticed, in plain words; no coordinates, ids, metres or percentages anywhere in what he is shown."""
import contextlib, copy, importlib.util, io, json, re, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tests'))
td = tempfile.mkdtemp(); shutil.copy(ROOT / 'crow.py', Path(td) / 'crow.py')
spec = importlib.util.spec_from_file_location('crow_seeing', Path(td) / 'crow.py'); app = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(app)
import perception, layout, lived_fixture, inner
NUMBERS = [r'\(-?\d+(\.\d+)?,\s*-?\d+', r'\b(tree|res|bird|deer|heap|bramble|bracken|ivy)-\d+\b', r'\d+(\.\d+)?\s?m\b', r'°', r'\bmetres?\b', r'\d+\s?%']
def clean(where, text):
    for p in NUMBERS:
        assert not re.search(p, text), f'{where}: /{p}/ in {text[:400]}'
def at(h, loc, action='rest', bed=False):
    app.CLOCK_OVERRIDE = lambda: datetime(2026, 12, 21, h, 0, tzinfo=app.TZ); app.clock()
    st = app.state; st['location'] = loc; st['action'] = action; st['in_bed'] = bed; layout.follow(st)
    return st
st = at(11, 'workbench', 'craft'); lived_fixture.populate(st)
# Plain words, no numbers or ids; the same moment always gives the same view; reading changes nothing.
for h, loc, act, bed in ((11, 'cabin', 'rest', True), (11, 'workbench', 'craft', False), (11, 'woods', 'explore', False),
                         (22, 'garden', 'garden', False), (11, 'library', 'read', False), (15, 'range', 'practise', False)):
    st = at(h, loc, act, bed); before = json.dumps(st, sort_keys=True, default=str)
    lines = perception.lines(st); clean(f'view at {loc}', ' '.join(lines))
    assert lines == perception.lines(st), 'same moment, same view'
    assert json.dumps(st, sort_keys=True, default=str) == before, 'seeing changes nothing'
# A wall hides what is behind it: inside the trading post facing its back wall, no tree of the wood behind it is seen.
st = at(11, 'shop', 'trade')
assert not [s for s in perception.view(st) if s['kind'] == 'tree'], perception.view(st)[:3]
# In the dark he makes out only what is close, and lit windows.
st = at(2, 'workbench', 'craft'); st['possessions'].pop('lantern', None); st['position']['heading'] = -1.6
seen = perception.view(st)
assert all(s['d'] < 4 or 'light' in s['phrase'] for s in seen), seen
assert any('light in the window of the reading cabin' in s['phrase'] for s in seen)
# Thirst draws the eye to water; cold to light and warmth.
st = at(11, 'cabin', 'eat'); st['position'].update(x=-14., z=-1., heading=-1.6)
plain_rank = [s['handle'] for s in perception.view(st)]
st['body']['hydration'] = 30
thirsty_rank = [s['handle'] for s in perception.view(st)]
assert 'spring' in thirsty_rank and thirsty_rank.index('spring') <= plain_rank.index('spring')
assert thirsty_rank.index('spring') < 3, thirsty_rank[:5]
st['body']['hydration'] = 90
# His whole view when choosing: no coordinates, ids, metres or per cent; within its budget.
st = at(11, 'workbench', 'craft')
seen_prompts = []
app.model_call = lambda p, s, *a, **k: (seen_prompts.append(p) or ({'action': 'rest', 'intention': 'i', 'reason': 'r', 'next_step': '', 'wish': '',
                                                                     'wish_reason': '', 'project': 'none', 'which_project': ''}, 0))
app.choose_action()
clean('choose_action prompt', seen_prompts[-1])
assert 'What I can make out around me:' in seen_prompts[-1]
assert len(json.dumps(app.decision_context(), ensure_ascii=False)) <= app.CONTEXT_BUDGET + 400
assert len(' '.join(perception.lines(st, wide=False))) <= perception.BUDGET['local'] + 120
# He picks a thing by his own words for it; the world maps them back. A tree to fell is one he can see from the woods.
app.model_call = lambda p, s, *a, **k: ({'object_id': 'my purse'}, 0)
d = app.choose_parameters({**app.DECISION_DEFAULTS, 'action': 'inspect', 'intention': 'count my money', 'reason': 'r', 'project': 'none'})
assert d['object_id'] == 'purse', d['object_id']
req = app.parameter_request({**app.DECISION_DEFAULTS, 'action': 'fell_tree', 'intention': 'x', 'reason': 'y'})
phrases = req[1]['object_id']['enum']; clean('trees to fell', ' '.join(phrases))
pick = phrases[0]; app.model_call = lambda p, s, *a, **k: ({'object_id': pick}, 0)
d = app.choose_parameters({**app.DECISION_DEFAULTS, 'action': 'fell_tree', 'intention': 'x', 'reason': 'y', 'project': 'none'})
assert app.state['built_world']['trees'][d['object_id']]['stage'] == 'standing'
# Retelling the world's own measurements in plain words.
t = inner.plain('tree-93 is an oak, about 7.3 m tall, with autumn leaves, about 30% still on the branches. A stone 3 m off.')
clean('plain', t); assert 'very tall' in t and 'about a third' in t and 'a few steps away' in t, t
print('PASS v0.35.0: he sees from where he stands, walls hide, dark shortens sight, needs draw the eye; plain words, no numbers or ids.')
