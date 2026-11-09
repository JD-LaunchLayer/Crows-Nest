"""v0.36.16: the ledger page can be read and copied; weather, Edda, the delivery and the deer vary from a saved seed.

Nothing here tells him what a page means, and nothing closes a question.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import garden, senses, story, town, wildlife, world_state, life, ecology

# Friday 26 February 2027. The following day he asks for Friday.
friday = datetime(2027, 2, 26, 9, 14)
saturday = datetime(2027, 2, 27, 11, 0)
s = {'materials': 0., 'stone': 0., 'creations': [], 'clock': {'iso': saturday.isoformat()},
     'threads': [{'id': 1, 'text': "I still don't know the full Friday ledger terms", 'status': 'open'}],
     'promises': [{'id': 1, 'text': 'I will hear every term before I spend', 'status': 'open', 'to': 'Edda Thorne'}],
     'affect': {'valence': 0., 'arousal': 0., 'signals': []}}
world_state.ensure(s); life.ensure(s); post = town.ensure(s)
post['ledger'] = [
    {'at': friday.isoformat(), 'text': 'Finished the posted job "Sweep and tidy the trading post" and earned 1 gold.', 'credit_after': 1},
    {'at': '2027-02-19T10:00:00', 'text': 'An older Friday: Bought 1 × Bundle of bread, cheese and dried fruit (4 servings) for 3 gold.', 'credit_after': 0},
]
before = [dict(l) for l in post['ledger']]
page = town.trade(s, 'ledger', 'Friday', 1, saturday.isoformat())['text']
assert 'Friday 26 February 2027' in page and 'Sweep and tidy' in page, page
assert 'older Friday' not in page and '3 gold' not in page
assert 'settled' not in page.lower() and s['threads'][0]['status'] == 'open' and s['promises'][0]['status'] == 'open'
assert post['ledger'] == before, 'reading does not write the book'
blank = town.trade(s, 'ledger', 'Thursday', 1, saturday.isoformat())['text']
assert 'blank' in blank and 'Nothing is written' in blank and 'no entry' in blank, blank
assert 'Sweep' in town.trade(s, 'ledger', 'sweep', 1, saturday.isoformat())['text']
copied = town.trade(s, 'ledger', 'Friday', 1, saturday.isoformat())
assert town.trade(s, 'ledger', 'copy', 1, saturday.isoformat())['success']
note = s['notebook'][-1]
assert note['title'] == 'Friday 26 February 2027' and 'Sweep and tidy' in note['text'] and 'older Friday' not in note['text']
shut = {'materials': 0., 'stone': 0., 'creations': [], 'clock': {'iso': saturday.isoformat()}}
world_state.ensure(shut); life.ensure(shut); town.ensure(shut)
assert 'shut' in town.trade(shut, 'ledger', 'copy', 1, saturday.isoformat())['text']
spoken = town.counter_reply(s, 'Please write out the Friday ledger line for me.')
assert spoken and 'Friday 26 February 2027' in spoken and 'Sweep and tidy' in spoken and 'settled' not in spoken.lower()
assert s['threads'][0]['status'] == 'open'
assert garden.CROPS['radish_seeds'][1] == 28 and garden.DAYS_TO_RIPE == 21.

# Weather stays the calendar when there is no seed, and a saved seed changes some days without touching mood.
plain = {'clock': {'iso': '2026-07-15T14:00:00'}}
assert senses.weather(plain) == senses.weather(dict(plain))
seeded = {'clock': {'iso': '2026-07-15T14:00:00'}, 'world_rolls': {'seed': 0xC0A15EED}, 'affect': {'valence': .2, 'arousal': .1, 'signals': []}}
differ = False
for day in range(1, 29):
    a = {'clock': {'iso': datetime(2026, 11, day, 15, 0).isoformat()}}
    b = {**a, 'world_rolls': {'seed': 0xC0A15EED}}
    if bool(senses.weather(a)['rain']) != bool(senses.weather(b)['rain']):
        differ = True
        break
assert differ, 'a saved seed changes some days'
assert senses.weather(seeded) == senses.weather(dict(seeded))
assert seeded['affect']['valence'] == .2
wet = {'garden': {'beds': [{'n': 1, 'crop': None, 'growth': 0., 'moisture': .2, 'weeds': 0., 'health': 1.}]}}
dry = {'garden': {'beds': [{'n': 1, 'crop': None, 'growth': 0., 'moisture': .2, 'weeds': 0., 'health': 1.}]}}
garden.advance(wet, 1, 200, 1.)
garden.advance(dry, 1, 200, 0.)
assert wet['garden']['beds'][0]['moisture'] > dry['garden']['beds'][0]['moisture']

# Edda away: the book and the board still work. She is present at the hours the existing talks use.
s['world_rolls'] = {'seed': 0xC0A15EED}
away = None
for n in range(60):
    day = datetime(2027, 3, 1) + timedelta(days=n)
    for hour in range(8, 19):
        s['clock'] = {'iso': day.replace(hour=hour).isoformat()}
        if not town.keeper_here(s):
            away = s['clock']['iso']
            break
    if away:
        break
assert away is not None
s['clock'] = {'iso': away}
assert 'not behind it' in senses.edda_line(s)
s['trading']['credit'] = 5
bought = town.trade(s, 'buy', 'arrows', 1, s['clock']['iso'])
assert bought['success'] and s['trading']['credit'] == 4
for iso in ('2026-11-01T12:00:00+00:00', '2027-01-13T11:00:00+00:00', '2026-12-09T14:00:00+00:00'):
    s['clock'] = {'iso': iso}
    assert town.keeper_here(s), iso

# A delivery can be late, and the lateness is saved on the post.
late = 0
when = None
for n in range(1, 40):
    when = datetime(2027, 4, 1, 9, 0) + timedelta(days=n)
    post['last_delivery'] = (when - timedelta(days=7)).isoformat()
    post['delivery_late_days'] = 0
    assert town.weekly_delivery(s, when)
    late = post['delivery_late_days']
    if late:
        break
assert late in (1, 2) and when is not None
post['stock']['arrows']['qty'] = 0
assert town.weekly_delivery(s, datetime.fromisoformat(post['last_delivery']) + timedelta(days=7, hours=1)) is None
assert town.weekly_delivery(s, datetime.fromisoformat(post['last_delivery']) + timedelta(days=7 + late, hours=1))
assert post['stock']['arrows']['qty'] > 0

# Deer: with the seed, some day is not the unseeded round. Ids stay.
base = {'clock': {'iso': '2026-11-16T13:00:00'}, 'wildlife': {'deer': [
    {'id': 'deer-1', 'role': 'buck', 'alive': True}, {'id': 'deer-2', 'role': 'doe', 'alive': True}],
    'trust': {}, 'carcasses': [], 'spooked_until': 0.}}
moved = False
for doy in range(1, 40):
    iso = datetime(2026, 1, 1) + timedelta(days=doy - 1)
    iso = iso.replace(hour=13)
    plain_h = wildlife.herd_area({**base, 'clock': {'iso': iso.isoformat()}}, ecology, .8)[0]
    seeded_h = wildlife.herd_area({**base, 'clock': {'iso': iso.isoformat()}, 'world_rolls': {'seed': 0xC0A15EED}}, ecology, .8)[0]
    if plain_h != seeded_h:
        moved = True
        break
assert moved
assert [d['id'] for d in base['wildlife']['deer']] == ['deer-1', 'deer-2']
print('PASS v0.36.16: a named day is the page itself, and the world varies without telling him how to feel.')
