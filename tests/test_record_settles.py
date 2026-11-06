"""v0.36.15: a question he is still carrying is answered when he has checked and the record agrees.

His words stay. A paid price is not a debt. When the purse and the book disagree, or she names a different sum,
the question stays open or opens again. Food he bought is what the chest shows.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import story, town, world_state, life, foods

def base():
    s = {'materials': 0, 'stone': 0, 'creations': [], 'memories': [], 'location': 'shop',
         'clock': {'iso': '2026-01-31T12:00:00+00:00'}}
    world_state.ensure(s)
    life.ensure(s)
    town.ensure(s)
    story.ensure(s)
    s['trading']['credit'] = 2
    s['trading']['ledger'] = [{'at': '2026-01-31T11:00:00+00:00', 'text': 'His purse, by the ledger: 2 gold.',
                                'credit_after': 2}]
    return s

def remembered(s, at, event, action='inspect', conversation=None):
    s['memories'].append({'id': len(s['memories']) + 1, 'at': at, 'event': event, 'action': action, 'kind': 'experience',
                           'world_result': {'conversation': conversation} if conversation else {}})

words = "Whether I actually owe the 3 credit, or whether Edda’s offer to let it go should be accepted. No deal was made."
price = 'Whether the 3 gold is a new purchase or a payment on the 13 November line, which Edda has not answered directly.'
sweep = 'I owe Edda the sweeping.'
cost = 'What is the posted price of the bread bundle?'
empty = 'Whether the provisions chest is empty and the last bread is gone.'
home = 'Head home by the dark path.'

s = base()
assert town.post_owes(s)['total'] == 0
story.add_thread(s, words, 'shop', 1, '2026-01-31T11:50:00+00:00')
story.add_thread(s, price, 'shop', 1, '2026-01-31T11:50:00+00:00')
story.add_promise(s, sweep, 'Edda Thorne', '2026-01-31T11:50:00+00:00')
story.add_thread(s, cost, 'shop', 1, '2026-01-31T11:50:00+00:00')
st = {'id': 1, 'title': words, 'variants': [words], 'stage': 'pursuing', 'count': 4, 'steps': [],
      'started': '2026-01-31T11:40:00+00:00', 'updated_hours': 1}
s['stories'] = [st]
kept = words
# Purse counted, but she has not confirmed: still open.
remembered(s, '2026-01-31T11:55:00+00:00', 'Opened his purse and counted what is in it: 2 gold.')
story.settle_by_evidence(s, '2026-01-31T11:55:00+00:00')
assert s['threads'][0]['status'] == 'open' and s['threads'][0]['text'] == kept
# She confirms the same sum. The account questions are answered; the sweeping promise and the price are not.
remembered(s, '2026-01-31T11:58:00+00:00',
           'Talked with Edda Thorne. Edda: “No, nothing is owed. You have 2 gold.”',
           action='talk', conversation=[{'who': 'Edda', 'text': 'No, nothing is owed. You have 2 gold.'}])
story.settle_by_evidence(s, '2026-01-31T11:58:00+00:00')
assert s['threads'][0]['status'] == 'followed' and s['threads'][0]['text'] == kept
assert s['threads'][1]['status'] == 'followed' and s['threads'][1]['text'] == price
assert s['promises'][0]['status'] == 'open', 'a promise to sweep is not a debt'
assert s['threads'][2]['status'] == 'open', 'what a thing costs is not money still owed'
assert st['stage'] == 'answered' and st['title'] == words
assert not any(t['text'] == words for t in story.open_items(s)['threads'])
# Saying it again, with nothing new against the book, does not bring it back.
story.settle_by_evidence(s, '2026-01-31T14:58:00+00:00')
assert s['threads'][0]['status'] == 'followed' and not any(t['text'] == words for t in story.open_items(s)['threads'])
# She names a different sum: the question opens again. The words are still his.
remembered(s, '2026-01-31T15:00:00+00:00', 'Talked with Edda. Edda: “You have 5 gold.”',
           action='talk', conversation=[{'who': 'Edda', 'text': 'You have 5 gold.'}])
story.settle_by_evidence(s, '2026-01-31T15:00:00+00:00')
assert s['threads'][0]['status'] == 'open' and s['threads'][0]['text'] == kept
assert st['stage'] == 'pursuing'
# The book itself disagrees with the purse: it stays open even if she agrees.
s2 = base()
s2['trading']['credit'] = .1
story.add_thread(s2, words, 'shop', 1, '2026-01-31T11:50:00+00:00')
remembered(s2, '2026-01-31T11:55:00+00:00', 'Opened his purse and counted what is in it: 1 silver.')
remembered(s2, '2026-01-31T11:58:00+00:00', 'Edda: “You have 1 silver. Nothing is owed.”',
           action='talk', conversation=[{'who': 'Edda', 'text': 'You have 1 silver. Nothing is owed.'}])
story.settle_by_evidence(s2, '2026-01-31T11:58:00+00:00')
assert s2['threads'][0]['status'] == 'open', 'the book still says 2 gold'

# Food he bought is in the chest he is shown, and a story that the chest is empty is answered.
# A question about the price is not.
s3 = base()
s3['location'] = 'shop'
foods.add(s3, 'provisions', 4)
shown = foods.view(s3)
assert any('bread' in name for name in shown) and sum(shown.values()) >= 4, shown
assert 'bread' in str(life.perceive(s3)['supplies']['in_the_provisions_chest'])
story.add_thread(s3, empty, 'cabin', 1, '2026-01-31T14:00:00+00:00')
story.add_thread(s3, cost, 'shop', 1, '2026-01-31T14:00:00+00:00')
empty_story = {'id': 2, 'title': empty, 'variants': [], 'stage': 'pursuing', 'count': 3, 'steps': [],
               'started': '2026-01-31T14:00:00+00:00', 'updated_hours': 1}
s3['stories'] = [empty_story]
story.settle_by_evidence(s3, '2026-01-31T14:28:00+00:00')
assert s3['threads'][0]['status'] == 'followed' and s3['threads'][0]['text'] == empty
assert s3['threads'][1]['status'] == 'open'
assert empty_story['stage'] == 'answered'
# Eaten down to nothing: the emptiness can be an open question again.
s3['provisions']['pantry'] = 0
s3['provisions']['larder'] = []
story.settle_by_evidence(s3, '2026-01-31T18:00:00+00:00')
assert s3['threads'][0]['status'] == 'open' and empty_story['stage'] == 'pursuing'

# Already home: heading home is not still something he has to do. At the post, it is.
s4 = base()
s4['location'] = 'cabin'
story.add_thread(s4, home, 'shop', 1, '2026-01-31T12:00:00+00:00')
story.settle_by_evidence(s4, '2026-01-31T12:10:00+00:00')
assert s4['threads'][0]['status'] == 'followed' and s4['threads'][0]['text'] == home
s5 = base()
s5['location'] = 'shop'
story.add_thread(s5, home, 'shop', 1, '2026-01-31T12:00:00+00:00')
story.settle_by_evidence(s5, '2026-01-31T12:10:00+00:00')
assert s5['threads'][0]['status'] == 'open'
print('PASS v0.36.15: the record answers a checked account and an empty chest, and a real disagreement stays open.')
