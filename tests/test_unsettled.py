"""A choice that does not fit is asked once more, then set aside. No network, no doze, no pause.

Insisting on food with an empty chest is still him going to look (v0.30.11). Any other illegal
action or detail, said again, is one honest moment and the clock keeps going. The paid model's
same-question retry for a wrong shape (v0.30.13) stays on calls that are not a choice; a choice
uses this one explained re-ask instead.
"""
import importlib.util, io, json, shutil, sys, tempfile, urllib.error
from datetime import timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(folder, name):
    shutil.copy(ROOT / 'crow.py', folder / 'crow.py')
    spec = importlib.util.spec_from_file_location(name, folder / 'crow.py')
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    return app


def arm(app):
    """His own clock, running, so a few minutes can be seen to pass."""
    app.CLOCK_OVERRIDE = None
    app.state['crow_clock'] = {'virtual': '2026-12-17T12:00:00+00:00', 'started_real': '2026-12-17T12:00:00+00:00', 'scale': 1}
    app.state['paused'] = False
    app.runtime['failures'] = 0
    app.runtime.pop('dozing_until', None)
    app.clock()
    return app.now()


def choice(action, **extra):
    base = {'action': action, 'intention': 'i', 'reason': 'r', 'next_step': '', 'wish': '', 'wish_reason': '',
            'project': 'none', 'which_project': ''}
    base.update(extra)
    return base, 1


def empty_chest(app):
    st = app.state
    st['provisions']['pantry'] = 0.
    st['provisions']['larder'] = []
    st['provisions']['berries'] = 0.
    assert 'eat' not in app.available_actions()


def still_living(app, start, moved=False):
    assert app.state['paused'] is False
    assert not app.runtime.get('dozing_until')
    assert app.runtime.get('failures', 0) == 0
    if moved:
        assert app.now() >= start + timedelta(seconds=60)


# He says eat, is told the chest is empty, and then rests. Eat is not put back on the list.
with tempfile.TemporaryDirectory() as td:
    app = load(Path(td), 'crow_eat_then_rest')
    empty_chest(app)
    start = arm(app)
    answers = iter(['eat', 'rest'])
    schemas = []
    def fake(prompt, schema, limit, *a, **k):
        schemas.append((prompt, schema))
        return choice(next(answers))
    app.model_call = fake
    started = app.decide_and_start(app.runtime['generation'])
    assert started['action'] == 'rest'
    assert 'eat' not in schemas[0][1]['properties']['action']['enum']
    assert 'eat' not in schemas[1][1]['properties']['action']['enum']
    assert 'nothing to eat' in schemas[1][0]
    assert app.state['visits'].get('eat', 0) == 0
    still_living(app, start)
print('PASS: eat, then rest — told why, eat stays off the list, no doze, not paused.')

# He keeps naming something that is not an action. Nine times is past the old pause-after-eight.
with tempfile.TemporaryDirectory() as td:
    app = load(Path(td), 'crow_keeps_illegal')
    empty_chest(app)
    start = arm(app)
    app.model_call = lambda *a, **k: choice('dance')
    for _ in range(9):
        assert app.decide_and_start(app.runtime['generation']) is None
    noted = [m for m in app.state['memories'] if m.get('kind') == 'unsettled']
    assert len(noted) == 9 and all('dance' in m['event'] for m in noted)
    still_living(app, start, moved=True)
    assert app.state.get('pending') is None
print('PASS: nine illegal actions — still not paused, still not dozing, the clock moved.')

# Insisting on food is still going to look (v0.30.11), not a stall and not a doze.
with tempfile.TemporaryDirectory() as td:
    app = load(Path(td), 'crow_insist_eat')
    empty_chest(app)
    arm(app)
    app.model_call = lambda *a, **k: choice('eat')
    d, _ = app.choose_action()
    assert d['action'] == 'eat'
    app.start_action({**app.DECISION_DEFAULTS, **d}, 1)
    app.state['pending']['remaining'] = 0
    m = app.finish_action(None)
    assert 'chest is empty' in m['event']
    assert app.state['paused'] is False and not app.runtime.get('dozing_until')
print('PASS: insisting on food still finds the empty chest, and does not doze or pause.')

# The detail step: a place that is not a place, twice, then a real one.
with tempfile.TemporaryDirectory() as td:
    app = load(Path(td), 'crow_bad_detail')
    start = arm(app)
    actions = iter(['observe', 'observe'])
    areas = iter(['nowhere', 'nowhere', 'grove'])
    prompts = []
    def fake(prompt, schema, limit, *a, **k):
        prompts.append(prompt)
        if 'action' in schema.get('properties', {}):
            return choice(next(actions))
        return {'observe_area': next(areas), 'focus': ''}, 1
    app.model_call = fake
    assert app.decide_and_start(app.runtime['generation']) is None
    assert any('nowhere' in m['event'] for m in app.state['memories'] if m.get('kind') == 'unsettled')
    assert any("nowhere" in p for p in prompts)
    still_living(app, start, moved=True)
    started = app.decide_and_start(app.runtime['generation'])
    assert started['action'] == 'observe' and started['observe_area'] == 'grove'
    still_living(app, start, moved=True)
print('PASS: a bad detail is asked once more, then set aside; the next pass uses a real place.')

with tempfile.TemporaryDirectory() as td:
    app = load(Path(td), 'crow_keeps_bad_detail')
    start = arm(app)
    def fake(prompt, schema, limit, *a, **k):
        if 'action' in schema.get('properties', {}):
            return choice('observe')
        return {'observe_area': 'nowhere', 'focus': ''}, 1
    app.model_call = fake
    for _ in range(9):
        assert app.decide_and_start(app.runtime['generation']) is None
    assert sum(1 for m in app.state['memories'] if m.get('kind') == 'unsettled') == 9
    still_living(app, start, moved=True)
print('PASS: nine bad details — still not paused, still not dozing, the clock still moving.')

# A choice sent to the paid model in the wrong shape is the explained re-ask, not a doze.
# An outage still dozes. The same-question retry for other calls is test_provider's v0.30.13 case.
with tempfile.TemporaryDirectory() as td:
    app = load(Path(td), 'crow_cloud_shape')
    arm(app)
    app.PROVIDER = 'anthropic'
    app.SETTINGS['anthropic_api_key'] = 'sk-ant-test-not-real'
    mode = {'down': False}
    calls = []
    class Reply(io.BytesIO):
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
    def urlopen(req, timeout):
        calls.append(1)
        if mode['down']:
            raise urllib.error.HTTPError(req.full_url, 529, 'Overloaded', {}, None)
        body = {'action': 'dance', 'intention': 'i', 'reason': 'r', 'next_step': '', 'wish': '',
                'wish_reason': '', 'project': 'none', 'which_project': ''}
        payload = {'content': [{'type': 'tool_use', 'name': 'respond', 'input': body}],
                   'usage': {'input_tokens': 10, 'output_tokens': 10}, 'stop_reason': 'end_turn'}
        return Reply(json.dumps(payload).encode())
    app.urllib.request.urlopen = urlopen
    schema = app.fields_schema({'action': {'type': 'string', 'enum': ['rest', 'trade']},
                                'project': {'type': 'string', 'enum': ['none']}})
    try:
        app.ask_allowed('Choose.', schema, 80, 'choose_action')
        raise AssertionError('dance should not be accepted')
    except app.Unsettled as exc:
        assert 'dance' in str(exc)
    # One explained re-ask: two cloud calls, not a blind retry stacked on top (that would be four).
    assert len(calls) == 2
    assert not app.runtime.get('dozing_until') and app.runtime.get('failures', 0) == 0 and app.state['paused'] is False
    mode['down'] = True
    try:
        app.model_call('Again.', schema, 80, 'choose_action')
        raise AssertionError('an outage should doze')
    except app.MindAway:
        pass
    assert not app.runtime.get('dozing_until')
print('PASS: a paid-model choice that does not fit is asked once and set aside; an outage still dozes.')
