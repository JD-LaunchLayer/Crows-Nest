"""v0.36.20: Edda's replies, and the whole slate sentence, can be recalled. A glance inside the post shows that sentence."""
import json
import sys
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import inner, life, memory_recall, perception, town, world_state

said = ('Carrying the crates is 60 minutes and pays 2 gold, once a day for the sweeping and per delivery for the crates.')
opening = 'I will not agree until the terms are written out and read back to me word for word.'
talk = {'current_intention': 'what the carrying pays, and how often the delivery comes',
        'threads': [{'id': 1, 'text': 'Whether the full terms say anything beyond the thirty minutes and 1 gold', 'status': 'open'}],
        'memories': [{'id': 5, 'kind': 'experience', 'action': 'talk', 'at': '2027-03-12T18:00:00',
                      'intention': 'hear the carrying terms', 'reason': 'I want every term.',
                      'event': 'Talked with Edda Thorne at the trading post. Crow: “' + opening + '”',
                      'world_result': {'conversation': [{'who': 'Crow', 'text': opening}, {'who': 'Edda', 'text': said}]}}]}
assert '2 gold' not in talk['memories'][0]['event'] and 'per delivery' not in talk['memories'][0]['event']
before = json.dumps(talk['threads'])
got = ' '.join(x.get('text', '') for x in memory_recall.recall(talk, 2000, limit=8))
assert '60 minutes' in got and '2 gold' in got and 'once a day' in got and 'per delivery' in got, got
assert json.dumps(talk['threads']) == before and talk['threads'][0]['status'] == 'open'

slate = ('The slate shows: Sweep and tidy the trading post: 30 minutes, pays 1 gold; needs doing today. '
         'Carry delivered crates into the store room: 60 minutes, pays 2 gold; '
         + ('waiting in the yard, ' * 8) + 'per delivery.')
assert len(slate) > 200, len(slate)
look = {'current_intention': 'what the slate says about the delivery',
        'memories': [{'id': 9, 'kind': 'experience', 'action': 'inspect', 'at': '2027-03-12T16:00:00',
                      'intention': 'look at the slate', 'reason': 'To read it.',
                      'event': 'Inspected the trading post. Shelves of jars and a counter.',
                      'world_result': {'findings': [
                          {'about': 'trading_post', 'text': 'Shelves of jars, a counter, and a slate board of posted rates.'},
                          {'about': 'trading_post', 'text': slate}]}}]}
recalled = [x for x in memory_recall.recall(look, 4000, limit=8) if str(x.get('text', '')).startswith('The slate shows:')]
assert recalled and recalled[0]['text'] == slate and not recalled[0]['text'].endswith('…'), recalled
voice = inner.memory_line({'type': 'observed', 'text': slate, 'when': '2027-03-12T16:00'}, '2027-03-13T02:00')
assert 'per delivery' in voice and '60 minutes' in voice and '2 gold' in voice, voice

long = 'Bramble with hooked prickles. ' + ('along the stem ' * 30) + 'UNIQUEEND'
assert len(long) > 200
clipped = {'current_intention': 'the bramble prickles',
           'memories': [{'id': 3, 'kind': 'experience', 'action': 'observe', 'at': '2027-03-01T12:00:00',
                         'event': 'Observed the edge.', 'intention': 'the bramble',
                         'world_result': {'findings': [{'text': long}]}}]}
bit = next(x['text'] for x in memory_recall.recall(clipped, 2000, limit=8) if 'Bramble' in x.get('text', ''))
assert 'UNIQUEEND' not in bit and bit.endswith('…'), bit

s = {'materials': 0., 'stone': 0., 'creations': [], 'clock': {'iso': '2027-03-12T15:00:00+00:00'},
     'daylight': .8, 'location': 'shop', 'possessions': {}}
world_state.ensure(s); life.ensure(s); town.ensure(s)
perception.lines(s)  # an existing first look may note the hearth; the glance itself must not
snap = json.dumps(s, sort_keys=True, default=str)
sentence = town.slate_sentence(s)
lines = perception.lines(s)
assert json.dumps(s, sort_keys=True, default=str) == snap, 'a glance changes nothing'
assert sentence in lines, lines
assert '60 minutes' in sentence and '2 gold' in sentence and 'weekly delivery' in sentence
ins = town.inspect(s, 'trading_post', datetime.fromisoformat(s['clock']['iso']), .8)
assert sentence in [f['text'] for f in ins['findings']]
assert 'you should' not in sentence.lower() and 'worth' not in sentence.lower()
s['daylight'] = 0.
assert all(not x.startswith('The slate shows:') for x in perception.lines(s))
s['possessions']['lantern'] = 1
assert any(x.startswith('The slate shows:') for x in perception.lines(s))
s['location'] = 'cabin'; s['daylight'] = .8
assert all('The slate shows:' not in x for x in perception.lines(s))
print('PASS v0.36.20: a reply and the whole slate can be recalled; inside the post, in the light, the glance shows that sentence.')
