"""Reading timing, honest history, durable processing and private HTTP access."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import urllib.error
import urllib.request

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))
import reading_journal

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    shutil.copy(SRC / 'crow.py', root / 'crow.py')
    (root / 'crow-reading').mkdir()
    source = {'query': 'wood grain', 'title': 'Wood grain',
              'url': 'https://en.wikipedia.org/wiki/Wood_grain',
              'text': 'Wood grain describes the longitudinal arrangement of wood fibres. ' * 70,
              'retrieved': '2026-10-29T10:00:00+00:00'}
    (root / 'crow-reading' / 'article-3.json').write_text(json.dumps(source))
    (root / 'crow-reading' / 'article-4.json').write_text(json.dumps({**source, 'title': 'Earlier source'}))
    decision = {'action': 'read', 'reason': 'I want to understand this material.',
                'intention': 'Test a small carving.', 'wish': '', 'wish_reason': '',
                'library_query': 'wood grain', 'creation_name': '', 'creation_shape': 'orb',
                'project_id': 0, 'project_title': '', 'project_status': 'active',
                'target_action': 'read', 'target_sessions': 1}
    old = {'day': 2, 'materials': 6, 'skills': {'archery': 0, 'craft': 0}, 'next_memory_id': 10,
           'memories': [{'id': 3, 'at': source['retrieved'], 'event': 'Read an excerpt.',
                         'reason': 'An old question.', 'source': source}],
           'pending': {'decision': decision, 'remaining': 800, 'duration': 900,
                       'start': source['retrieved'], 'reading': source, 'project_id': None}}
    old['pending']['decision']['reading_mode']='leisure'
    old['pending']['decision']['research_question']='How is grain arranged?'
    (root / 'crow-save.json').write_text(json.dumps(old))
    spec = importlib.util.spec_from_file_location('crow_research_test', root / 'crow.py')
    app = importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    assert json.loads((root / 'crow-save-before-v0.4.json').read_text()) == old
    assert len(app.state['reading_log']) == 2 and app.state['reading_log'][0]['summary'] == ''
    assert all(record['status'] == 'legacy' for record in app.state['reading_log'])
    assert app.state['pending']['remaining'] == 0 and app.state['pending']['reading'] == source
    assert app.state['materials'] == 6

    app.state['paused'] = False
    memory = app.finish_action()
    record = app.state['reading_log'][-1]
    assert record['status'] == 'awaiting_note' and record['summary'] == ''
    assert app.state['reflection_pending'] == memory['id']
    assert record['url'] == source['url'] and record['mode'] == 'lookup'
    result = {'feeling': 'I have a useful question to test.',
              'lesson': 'I need to observe the grain before cutting.', 'topic': 'wood grain',
              'enjoyment': 0, 'personality_note': '',
              'next_step': 'Inspect the material at my workbench.',
              'reading_summary': 'The excerpt describes the arrangement of wood fibres.',
              'answer_status': 'partial'}
    result.update({key + '_delta': 0 for key in app.state['emotions']})
    app.model_call = lambda *args, **kwargs: (copy.deepcopy(result), 1)
    app.state['paused'] = True
    assert app.reflect(memory) is False and record['status'] == 'awaiting_note'
    app.state['paused'] = False
    def interrupted(*args, **kwargs):
        app.runtime['generation'] += 1
        return copy.deepcopy(result), 1
    app.model_call = interrupted
    assert app.reflect(memory) is False and app.state['reflection_pending'] == memory['id']
    app.model_call = lambda *args, **kwargs: (copy.deepcopy(result), 1)
    assert app.reflect(memory) is True
    assert record['status'] == 'processed' and record['processed_chars'] == reading_journal.CONTEXT_CHARS
    assert record['summary'] == result['reading_summary'] and record['answer_status'] == 'partial'
    assert app.state['next_step'] == result['next_step'] and app.state['reflection_pending'] is None
    assert app.state['skills'] == {'archery': 0, 'craft': 0}
    count = len(app.state['appraisals']);assert app.reflect(memory) is True
    assert len(app.state['appraisals']) == count  # No duplicate emotional/interest update on retry.
    payload = reading_journal.article(root, memory['id'])
    assert payload['text'] == source['text'] and payload['journal']['summary'] == result['reading_summary']

    leisure = {**decision, 'reading_mode': 'leisure', 'next_step': '', 'research_question': ''}
    app.start_action(leisure, 1, source)
    assert app.state['pending']['duration'] == 900 and app.state['next_step'] == ''
    app.tick(30);assert app.state['pending']['remaining'] == 870
    app.state['paused'] = True;app.tick(100);assert app.state['pending']['remaining'] == 870
    app.state['paused'] = False
    lookup = {**leisure, 'reading_mode': 'lookup', 'research_question': 'How is grain arranged?'}
    app.start_action(lookup, 1, source);assert app.state['pending']['remaining'] == 0
    app.start_action({**decision, 'action': 'craft'}, 1)
    assert app.state['pending']['duration'] == 2700  # Physical work was not accelerated.

    for memory_id in range(100, 130):
        app.state['reading_log'].append({**copy.deepcopy(record), 'id': memory_id})
    app.persist()
    before = copy.deepcopy(app.state['reading_log']);reading_journal.ensure(app.state, root)
    assert app.state['reading_log'] == before  # No repeated migration, no lost old cache entries.
    app.ACCESS_TOKEN = 'test-private-reading-token'
    server = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:' + str(server.server_port)
    def get(path, authenticated=True):
        headers = {'Authorization': 'Bearer ' + app.ACCESS_TOKEN} if authenticated else {}
        with urllib.request.urlopen(urllib.request.Request(base + path, headers=headers)) as response:
            return json.load(response)
    for path in ['/api/reading', '/api/reading/' + str(memory['id'])]:
        try:get(path, False);raise AssertionError('Private reading exposed')
        except urllib.error.HTTPError as error:assert error.code == 401
    state = get('/api/state');assert len(state['reading_log']) == 20 and state['reading_count'] == len(before)
    first = get('/api/reading');assert first['has_more'] and len(first['items']) == 20
    second = get('/api/reading?before=' + str(first['items'][-1]['id']))
    assert not ({item['id'] for item in first['items']} & {item['id'] for item in second['items']})
    assert get('/api/reading/' + str(memory['id']))['journal']['processed_chars'] == reading_journal.CONTEXT_CHARS
    for path, code in [('/api/reading?before=invalid', 400), ('/api/reading/99999', 404),
                       ('/api/reading/../../crow-save.json', 404)]:
        try:get(path);raise AssertionError('Bad reading request accepted')
        except urllib.error.HTTPError as error:assert error.code == code
    server.shutdown();server.server_close()
    print('PASS: instant lookup and optional leisure; physical time unchanged; truthful legacy history; '
          'source/summary distinction; pause/retry and one-time appraisal; persistent notes; authenticated paginated history/excerpts.')
