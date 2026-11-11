"""v0.36.21: asking for a notebook page by number opens that page. A word, a day, and a phrase such as "1 gold" do not."""
import copy
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import notebook

NOTHING = 'nothing he has written is about that'

pages = []
for i in range(1, 71):
    pages.append({'id': i, 'at': '2027-03-20T17:48:00', 'title': 'A note from the day', 'text': 'The clearing was quiet.'})
pages[1]['at'] = '2026-12-03T11:21:00'
pages[1]['title'] = '12-03 at the post'
pages[1]['text'] = 'Swept the post and bought the bread bundle.'
pages[64]['title'] = 'Cord bundle'
pages[64]['text'] = 'Bought the bread bundle.'
pages[68]['title'] = 'Before supper'
pages[68]['text'] = 'The yard was quiet before supper.'
pages[69]['title'] = 'Saturday 20 March 2027: What Edda told me today'
pages[69]['text'] = 'Edda spoke about the crates waiting in the yard. The pay was one gold.'
assert '69' not in pages[68]['title'] + pages[68]['text']
assert '70' not in pages[69]['title'] + pages[69]['text']
st = {'notebook': pages}
snap = copy.deepcopy(st['notebook'])

got = notebook.read(st, '69')
assert got['pages'] == [69] and 'The yard was quiet before supper.' in got['text'], got
assert got['text'].startswith('Read back his notebook:') and NOTHING not in got['text']
got = notebook.read(st, '70')
assert got['pages'] == [70] and 'What Edda told me today' in got['text'] and 'Edda spoke about the crates' in got['text'], got
assert 'Before supper' not in got['text']
got = notebook.read(st, 'page 69')
assert got['pages'] == [69] and 'Before supper' in got['text'], got
got = notebook.read(st, 'Page 69')
assert got['pages'] == [69], got
got = notebook.read(st, 'pages 69 and 70')
assert got['pages'] == [69, 70], got
assert got['text'].find('page 69') < got['text'].find('page 70')
assert 'before supper' in got['text'] and 'What Edda told me today' in got['text']
assert 'Cord bundle' not in got['text'] and NOTHING not in got['text']
got = notebook.read(st, 'PAGES 69 AND 70')
assert got['pages'] == [69, 70], got

miss = notebook.read(st, '71')
assert miss['pages'] == []
assert miss['text'] == 'Looked for page 71 in his notebook: there is no such page. He has written 70 pages in all.', miss
assert NOTHING not in miss['text']
miss = notebook.read(st, 'page 99')
assert miss['pages'] == [] and 'there is no such page' in miss['text'] and '99' in miss['text'] and '70 pages' in miss['text'], miss
assert NOTHING not in miss['text']
part = notebook.read(st, 'pages 69 and 99')
assert part['pages'] == [69] and 'before supper' in part['text'], part
assert 'there is no such page' in part['text'] and '99' in part['text'] and '70 pages' in part['text']
assert NOTHING not in part['text']

word = notebook.read(st, 'bundle')
assert word['pages'] == [2, 65] and 'bread bundle' in word['text'], word
word = notebook.read(st, 'Edda')
assert word['pages'] == [70], word
day = notebook.read(st, '12-03')
assert day['pages'] == [2] and 'Swept the post' in day['text'], day
assert 12 not in day['pages'] and 3 not in day['pages'] and 'no such page' not in day['text']
day = notebook.read(st, '12-03 cord bundle')
assert day['pages'] == [2], day
day = notebook.read(st, 'page 12-03')
assert day['pages'] == [2] and 12 not in day['pages'], day
gold = notebook.read(st, '1 gold')
assert gold['pages'] == [70] and 1 not in gold['pages'], gold
assert 'page 1 ' not in gold['text'] and 'one gold' in gold['text']
opened = notebook.read(st, '')
assert opened['pages'] == [67, 68, 69, 70] and opened['text'].startswith('Read back his notebook:'), opened
assert st['notebook'] == snap, 'reading must not rewrite saved pages'

kept = {'notebook': [{'id': '70', 'at': '2027-03-20T17:48:00', 'title': 'Kept as stored', 'text': 'The ink is dry.'}]}
before = copy.deepcopy(kept)
got = notebook.read(kept, '70')
assert got['pages'] == ['70'] and 'The ink is dry.' in got['text'], got
assert kept == before

made = {}
notebook.write(made, 'First', 'Only the river.', '2027-03-20T10:00:00')
notebook.write(made, 'Second', 'Only the bread.', '2027-03-20T11:00:00')
assert notebook.read(made, '2')['pages'] == [2]
second = notebook.read(made, 'page 2')
assert 'Only the bread.' in second['text'] and 'Only the river.' not in second['text'], second
assert notebook.read(made, 'pages 1 and 2')['pages'] == [1, 2]
assert notebook.read(made, '')['pages'] == [1, 2]
miss = notebook.read(made, '3')
assert miss['text'] == 'Looked for page 3 in his notebook: there is no such page. He has written 2 pages in all.', miss
assert NOTHING not in miss['text']
gold = notebook.read(made, '1 gold')
assert gold['pages'] == [] and NOTHING in gold['text'] and 'no such page' not in gold['text'], gold
assert 'Only the river.' not in gold['text']
day = notebook.read(made, '12-03')
assert day['pages'] == [] and NOTHING in day['text'] and 'no such page' not in day['text'], day
one = {'notebook': [{'id': 1, 'at': '2027-03-20T10:00:00', 'title': 'Only', 'text': 'One page of ink.'}]}
assert notebook.read(one, '2')['text'] == 'Looked for page 2 in his notebook: there is no such page. He has written 1 page in all.'
blank = notebook.read({}, '69')
assert 'empty' in blank['text'] and 'never written' in blank['text'] and blank['pages'] == []
print('PASS v0.36.21: a page number opens that page; a missing number is said plainly; words, dates and "1 gold" are unchanged.')
