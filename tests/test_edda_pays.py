"""v0.32.2: Edda cannot take his goods for nothing.

On 2026-12-19 a talk settled as "Edda took 4 kg of wood for nothing": the deal check had a ceiling on what the
post pays for goods but no floor. Now a deal for his goods must pay at least seven tenths of their worth.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import town, world_state, life
s = {'materials': 20., 'stone': 0., 'creations': []}
world_state.ensure(s); life.ensure(s); town.ensure(s)
free = {'kind': 'buy_goods', 'item': 'wood', 'quantity': 4, 'credit': 0, 'minutes': 0, 'task': ''}
ok, why = town.check_proposal(s, free, 1); assert not ok and 'pays' in why, why
fair = dict(free, credit=1.3); assert town.check_proposal(s, fair, 1)[0]
assert town.check_proposal(s, dict(free, credit=1), 1)[0], 'a little under the posted rate is still a fair deal'
print('PASS v0.32.2: the post pays for what it takes from him.')
