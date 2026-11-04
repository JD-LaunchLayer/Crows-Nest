"""v0.33.1: when the post's own book shows it took his goods underpaid, Edda is told and can make it good.

Before v0.32.2 a deal could take his goods for nothing (the 2026-12-19 18:48 line). The book is read, never changed;
a payment back goes through the same checks as every deal and is recorded as a new line.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import town, world_state, life
s = {'materials': 20., 'stone': 0., 'creations': []}
world_state.ensure(s); life.ensure(s); post = town.ensure(s)
assert town.post_owes(s)['total'] == 0 and not town.check_proposal(s, {'kind': 'make_good', 'credit': .5}, 1)[0]
post['ledger'].append({'at': '2026-12-19T18:48:00', 'text': 'Edda took 4 kg of wood for nothing.', 'credit_after': 1.3})
post['ledger'].append({'at': '2026-12-19T18:57:00', 'text': 'Edda took 6 kg of wood for 2 gold.', 'credit_after': 3.3})
before = [dict(l) for l in post['ledger']]
owed = town.post_owes(s); assert owed['total'] == 1.3 and len(owed['entries']) == 1, owed
assert not town.check_proposal(s, {'kind': 'make_good', 'credit': 1.5}, 1)[0], 'not more than it owes'
credit = post['credit']
r = town.apply_proposal(s, {'kind': 'make_good', 'item': '', 'quantity': 1, 'credit': 1.3, 'minutes': 0, 'task': ''}, '2026-12-20T10:00', 2)
assert r['success'] and abs(post['credit'] - credit - 1.3) < 1e-9 and 'owed him' in r['text']
assert town.post_owes(s)['total'] == 0 and not town.check_proposal(s, {'kind': 'make_good', 'credit': .1}, 2)[0]
assert post['ledger'][:2] == before, 'the old lines are never changed'
print('PASS v0.33.1: what the post owes him by its own book can be paid back, once, and only that.')
