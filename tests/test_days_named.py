"""v0.36.8: the days he names, however he names them, are looked up in Edda's book. On 2 January he asked about "the
27th, 28th and 29th"; only "12-27" was understood, so she was shown nothing and told him her book had no entries for
those days, though it did, and he went looking for missing coin."""
import sys
from datetime import date
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import town, world_state, life
today = date(2027, 1, 2)
assert town.days_mentioned("starting with the 27th, 28th and 29th", today) == ['12-27', '12-28', '12-29']
assert town.days_mentioned("the 27th of December and 3 Jan", today) == ['12-27', '01-03']
assert town.days_mentioned("12-03 cord bundle", today) == ['12-03']
assert town.days_mentioned("December 30", today) == ['12-30']
assert town.days_mentioned("the 2nd", today) == ['01-02'], 'a bare day is the most recent one up to today'
assert town.days_mentioned("my first thing", today) == []
s = {'materials': 0., 'stone': 0., 'creations': []}; world_state.ensure(s); life.ensure(s); post = town.ensure(s)
post['ledger'].append({'at': '2026-12-27T09:57:00+00:00', 'text': 'Bought 1 × Bundle of bread for 3 gold.', 'credit_after': 6.8})
for q in town.days_mentioned("the 27th", today):
    assert town.ledger_lookup(s, q) and 'Bought' in town.ledger_lookup(s, q)[0]
assert town.ledger_lookup(s, 'the 27th of december'), 'a day with "of" is found too'
print('PASS v0.36.8: days he names in any wording are looked up in her book.')
# v0.36.9: the request book says plainly what it is for and that it gives no reply.
r = town.trade(s, 'ask', 'paid work for today', 1, '2027-01-06T15:13:00+00:00')
assert 'things people would like her to stock' in r['text'] and 'gives no reply' in r['text'], r['text']
print('PASS v0.36.9: the request book says what it is for.')
