"""v0.36.19: the book only records what happened; a delivery day includes its lateness;
a new favour is the sweep or the crates; six open favours stay six; agreeing work keeps only that work's promise."""
import sys
from datetime import datetime, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import life, story, town, world_state

assert ('A line appears in the book only when something is bought, sold, paid or delivered, and you cannot write '
        "a job's terms, or anything else, onto a page.") in town.KEEPER_PERSONA
assert 'you should' not in town.KEEPER_PERSONA.lower()

s = {'materials': 0., 'stone': 0., 'creations': [], 'clock': {'iso': '2027-03-01T10:00:00+00:00'}}
world_state.ensure(s); life.ensure(s)
post = town.ensure(s)
last = datetime.fromisoformat('2027-03-01T10:00:00+00:00')
post['last_delivery'] = last.isoformat()
post['delivery_late_days'] = 0
assert town.next_delivery(s).startswith('Monday 08 March'), town.next_delivery(s)
post['delivery_late_days'] = 2
assert town.next_delivery(s).startswith('Wednesday 10 March, around 10:00'), town.next_delivery(s)
assert town.weekly_delivery(s, last + timedelta(days=9, hours=-1)) is None
assert town.next_delivery(s).startswith('Wednesday 10 March'), 'naming the day did not move it'
assert town.weekly_delivery(s, last + timedelta(days=9))

day = '2027-03-11'
s['clock'] = {'iso': '2027-03-11T09:00:00+00:00'}
odd = {'kind': 'favour', 'item': '', 'quantity': 1, 'credit': 1, 'minutes': 30, 'task': 'Patch the store-room roof'}
ok, why = town.check_proposal(s, dict(odd), day)
assert not ok and why == 'that is not posted work at the post', why
settled = town.apply_proposal(s, dict(odd), s['clock']['iso'], day)
assert not settled['success'] and 'that is not posted work at the post' in settled['text']
assert town.keeper(s)['favours'] == []

sweep = {'kind': 'favour', 'item': '', 'quantity': 1, 'credit': 1, 'minutes': 30, 'task': 'Sweep the trading post'}
assert town.check_proposal(s, dict(sweep), day)[0]
agreed = town.apply_proposal(s, dict(sweep), s['clock']['iso'], day)
assert agreed['success'] and 'whatever the work needs is there' not in agreed['text']
assert 'job favour-1' in agreed['text'] and len(town.keeper(s)['favours']) == 1

stored = {'id': 'favour-9', 'task': 'Count the 1 gold into my hand', 'minutes': 15, 'credit': 1, 'agreed': s['clock']['iso']}
town.keeper(s)['favours'].append(stored)
before = post['credit']
done = town.trade(s, 'job', 'favour-9', 1, s['clock']['iso'])
assert done['success'] and abs(post['credit'] - (before + 1)) < 1e-9, done
assert all(f['id'] != 'favour-9' for f in town.keeper(s)['favours'])
assert any(f['id'] == 'favour-1' for f in town.keeper(s)['favours']), 'the sweep he agreed is still there'

full = {'materials': 0., 'stone': 0., 'creations': [], 'clock': {'iso': '2027-03-12T09:00:00+00:00'}}
world_state.ensure(full); life.ensure(full); town.ensure(full)
kept = [{'id': f'favour-{i}', 'task': f'Old task {i}', 'minutes': 15, 'credit': 0, 'agreed': full['clock']['iso']}
        for i in range(1, 7)]
town.keeper(full)['favours'] = list(kept)
town.keeper(full)['next_favour'] = 7
ok, why = town.check_proposal(full, dict(sweep), '2027-03-12')
assert not ok and why == 'six favours are already agreed', why
refused = town.apply_proposal(full, dict(sweep), full['clock']['iso'], '2027-03-12')
assert not refused['success'] and 'six favours are already agreed' in refused['text']
assert town.keeper(full)['favours'] == kept

promises = {'stories': [], 'threads': [], 'next_story_id': 1, 'promises': [
    {'id': 1, 'text': "I'll give you a clear answer on the crate carrying once I've eaten.", 'status': 'open'},
    {'id': 2, 'text': "I'll come back when terms are written on the Friday 5 March page.", 'status': 'open'},
    {'id': 3, 'text': "I'll hear the sweeping terms before I agree.", 'status': 'open'}]}
story.work_agreed(promises, 'carry_crates', '2027-03-06T08:00:00+00:00')
assert promises['promises'][0]['status'].startswith('kept')
assert promises['promises'][1]['status'] == 'open' and promises['promises'][2]['status'] == 'open'
assert promises['promises'][1]['text'] == "I'll come back when terms are written on the Friday 5 March page."
print('PASS v0.36.19: the book records what happened; the delivery day includes its lateness; '
      'a new favour is posted work; six open favours stay; a promise is kept only for the work agreed.')
