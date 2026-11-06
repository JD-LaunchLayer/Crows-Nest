"""v0.36.15: a building is too big to carry. What he built or was given can be taken apart; Edda's post cannot.

The work takes time in proportion to the material. About half is left on the ground as usable wood or stone;
the rest is split and full of bent nails. Nothing in the result tells him what to make next.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import world_state as w
import materials

s = {'materials': 0, 'stone': 0, 'creations': []}
world = w.ensure(s)
r = w.move(s, 'library', 0, 0)
assert not r['success'] and 'too big and heavy' in r['text'], r
# The post is furnished by town.ensure; the shell is already a building once the town is there.
import life
import town
life.ensure(s)
town.ensure(s)
post = s['built_world']['objects']['trading_post']
assert w.too_big_to_carry(post)
moved = w.move(s, 'trading_post', 1, 1)
assert not moved['success'] and 'too big and heavy' in moved['text'], moved
assert post['x'] == s['built_world']['objects']['trading_post']['x']
try:
    w.propose(s, 'Strip the post', 'remove', 'trading_post', 0, 0, remove_part='')
    raise SystemExit('the trading post was offered up to be taken apart')
except ValueError as exc:
    assert 'not his to take apart' in str(exc), exc
try:
    w.propose(s, 'Take the café', 'remove', 'internet_cafe', 0, 0, remove_part='counter')
    raise SystemExit('the café was offered up to be taken apart')
except ValueError as exc:
    assert 'not his to take apart' in str(exc), exc

# Something he built: a small box, then the whole of it, then a heavier one takes longer.
parts = [{'shape': 'box', 'material': 'wood', 'color': '#aabbcc', 'x': 0, 'y': .1, 'z': 0, 'width': .2, 'height': .2, 'depth': .2}]
s['materials'] = 4
built = w.construct(s, w.propose(s, 'Small box', 'new', '', 2, 2, parts)['id'])
assert built['success']
ident = built['object_id']
small = w.propose(s, 'Take the box apart', 'remove', ident, 0, 0, remove_part='')
assert small['remove_all'] and small['minutes'] >= 15 and small['salvage'].get('wood', 0) > 0
before = s['materials']
done = w.construct(s, small['id'])
assert done['success'] and ident not in s['built_world']['objects'], done
assert s['materials'] > before
assert 'bent nails' in done['text'] and 'ground' in done['text']
for banned in ('recipe', 'you can', 'you should', 'hint', 'build a'):
    assert banned not in done['text'].lower(), done['text']
lots = [l for l in s.get('stock', {}).get('lots', []) if 'taken apart' in l.get('source', '')]
assert lots and abs(sum(l['mass_kg'] for l in lots) - (s['materials'] - before)) < .05, lots

# A heavier piece of his own work takes longer than the box.
big = [{'shape': 'box', 'material': 'wood', 'color': '#aabbcc', 'x': 0, 'y': .5, 'z': 0, 'width': 1, 'height': 1, 'depth': 1}]
s['materials'] = 500
shed = w.construct(s, w.propose(s, 'Shed', 'new', '', 8, 0, big)['id'])
heavy = w.propose(s, 'Take the shed apart', 'remove', shed['object_id'], 0, 0, remove_part='')
assert heavy['minutes'] > small['minutes']
# One short session does not finish it, and the shed is still standing.
step = w.construct(s, heavy['id'], 10)
assert step['success'] and not step.get('built') and shed['object_id'] in s['built_world']['objects'], step

# One part of the reading cabin, which he was given, still comes away. The post's rates are not involved.
wall = next(p['id'] for p in s['built_world']['objects']['library']['parts'])
one = w.propose(s, 'One wall', 'remove', 'library', 0, 0, remove_part=wall)
wood_before = s['materials']
part = w.construct(s, one['id'])
assert part['success'] and not any(p['id'] == wall for p in s['built_world']['objects']['library']['parts'])
assert s['materials'] > wood_before and 'bent nails' in part['text']
print('PASS v0.36.15: buildings stay put; what is his comes apart on the ground; the post does not.')
