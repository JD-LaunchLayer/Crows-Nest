"""v0.32.1: wood and stone are sold by the kilograms he names, not by the gold he hopes for.

On 2026-12 he promised Edda about 4 kg of wood, asked to sell 4, and the post took 12 kg for 4 gold.
Now the number is kilograms; he is paid in whole silver at the posted rate.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import town, world_state, life
s = {'materials': 20., 'stone': 12., 'creations': []}
world_state.ensure(s); life.ensure(s); post = town.ensure(s)
r = town.trade(s, 'sell', 'wood', 4, 't')
assert r['success'] and s['materials'] == 16 and abs(post['credit'] - 1.3) < 1e-9, (r, s['materials'], post['credit'])
assert '4 kg of wood' in r['text'] and '1 gold 3 silver' in r['text'], r['text']
r = town.trade(s, 'sell', 'stone', 5, 't')
assert r['success'] and s['stone'] == 7 and abs(post['credit'] - 2.3) < 1e-9
# Asking for more than he has sells what he has, no more.
r = town.trade(s, 'sell', 'stone', 50, 't'); assert r['success'] and s['stone'] == 0 and abs(post['credit'] - 3.7) < 1e-9
# Too little to earn a silver is refused, and nothing leaves him.
s['materials'] = .2; r = town.trade(s, 'sell', 'wood', 1, 't'); assert not r['success'] and s['materials'] == .2
print('PASS v0.32.1: wood and stone sold by the kilogram he names, paid in silver at the posted rate.')
