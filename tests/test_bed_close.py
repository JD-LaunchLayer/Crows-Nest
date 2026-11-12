"""v0.36.24: he can kneel by a garden bed and look closely at it; the bed is not "an object that does not exist"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import garden
s = {}
g = garden.ensure(s)
r = garden.close_look(s, 'garden_bed_2')
assert r['success'] and 'Bed 2: bare soil' in r['text'] and 'no roots or leaves' in r['text'], r
g['beds'][0].update(crop='withered', item='radish_seeds', moisture=.9)
r = garden.close_look(s, 'garden_bed_1')
assert 'dead through' in r['text'] and 'nothing in them to eat' in r['text'] and 'Water stands' in r['text'], r
assert garden.close_look(s, 'garden_bed_9') is None and garden.close_look(s, 'garden_bed_x') is None
assert not any(ch.isdigit() for ch in r['text'].replace('bed 1', '').replace('Bed 1', '')), r['text']
print('PASS v0.36.24: a garden bed can be looked at closely, and says plainly what is left in it.')
