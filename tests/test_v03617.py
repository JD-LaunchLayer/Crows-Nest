"""v0.36.17: a lookup that finds no article is what he found, not a fault that pauses his life."""
import contextlib, importlib.util, io, json, shutil, sys, tempfile, urllib.error
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))

QUERY = 'my notebook page 8 12-03 cord bundle line 1 12-06 source check'

def load(folder, name):
    shutil.copy(ROOT / 'crow.py', folder / 'crow.py')
    spec = importlib.util.spec_from_file_location(name, folder / 'crow.py')
    app = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(app)
    app.state['paused'] = False
    app.state['affect'] = {'valence': 0.2, 'arousal': 0.1, 'signals': []}
    app.runtime['failures'] = 0
    app.state['last_error'] = ''
    return app

class Reply:
    def __init__(self, obj):
        self.body = json.dumps(obj).encode()
    def __enter__(self):
        return self
    def __exit__(self, *a):
        pass
    def read(self, *a):
        return self.body

def choosing(app, action, query):
    def model(prompt, schema, limit=650, purpose='other', system=None):
        props = schema.get('properties', {}) if isinstance(schema, dict) else {}
        if 'action' in props:
            return {'action': action, 'intention': 'Check the line', 'reason': 'I want the source',
                    'next_step': '', 'wish': '', 'wish_reason': '', 'project': 'none', 'which_project': ''}, 1
        if purpose == 'parameters:' + action:
            return {'library_query': query, 'research_question': 'What does the line say?'}, 1
        if purpose == 'select_source':
            return {'page_id': 1, 'reason': 'The only one.'}, 1
        return {}, 1
    app.model_call = model

with tempfile.TemporaryDirectory() as td:
    folder = Path(td)
    app = load(folder, 'crow_no_article')
    def empty(req, timeout=25):
        return Reply({'query': {'search': []}})
    app.urllib.request.urlopen = empty
    choosing(app, 'read', QUERY)
    for _ in range(9):
        assert app.decide_and_start(app.runtime['generation']) is None
    assert app.state['paused'] is False and app.runtime.get('failures', 0) == 0
    assert app.state['last_error'] == ''
    assert app.state['affect']['valence'] == 0.2
    last = app.state['memories'][-1]
    assert last['kind'] == 'research_feedback' and 'no article' in last['event'] and QUERY in last['event']
    assert 'try ' not in last['event'].lower()
    assert len([m for m in app.state['memories'] if m.get('kind') == 'research_feedback']) == 9

    def blank(req, timeout=25):
        if 'list=search' in req.full_url:
            return Reply({'query': {'search': [{'pageid': 1, 'title': 'Cord', 'snippet': 'A rope.'}]}})
        return Reply({'query': {'pages': [{'title': 'Cord', 'extract': ''}]}})
    app.urllib.request.urlopen = blank
    assert app.decide_and_start(app.runtime['generation']) is None
    assert 'no text to read' in app.state['memories'][-1]['event']
    assert app.runtime.get('failures', 0) == 0 and app.state['paused'] is False

    def down(req, timeout=25):
        raise urllib.error.URLError('timed out')
    app.urllib.request.urlopen = down
    raised = 0
    for _ in range(8):
        try:
            app.decide_and_start(app.runtime['generation'])
        except Exception as exc:
            raised += 1
            app.note_problem(exc)
    assert raised == 8 and app.state['paused'] is True
    assert 'repeated problems' in app.runtime['status']
    assert 'timed out' in app.state['last_error']
    assert app.state['affect']['valence'] == 0.2

    app2 = load(folder, 'crow_api_error')
    def api_error(req, timeout=25):
        return Reply({'error': {'info': 'maxlag'}})
    app2.urllib.request.urlopen = api_error
    choosing(app2, 'read', 'plants')
    try:
        app2.decide_and_start(app2.runtime['generation'])
        raise AssertionError('an API error should still be a fault')
    except ValueError as exc:
        assert 'maxlag' in str(exc)
        app2.note_problem(exc)
    assert app2.runtime['failures'] == 1 and app2.state['paused'] is False

    app3 = load(folder, 'crow_web_empty')
    choosing(app3, 'browse', QUERY)
    app3.web.search = lambda q, settings=None: (_ for _ in ()).throw(app3.web.Refused('The search returned no results (or the search page refused an automated visitor).'))
    for _ in range(9):
        assert app3.decide_and_start(app3.runtime['generation']) is None
    assert app3.state['paused'] is False and app3.runtime.get('failures', 0) == 0
    assert app3.state['memories'][-1]['kind'] == 'research_feedback'
print('PASS v0.36.17: no article is logged and life goes on; a real fault still pauses him.')
