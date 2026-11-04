"""v0.34.2: handling a thing keeps what he meant apart from what happened, so he never later recalls it as done."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import town, world_state, life, inner
s = {'materials': 0., 'stone': 0., 'creations': [], 'possessions': {'radish_seeds': 1}}
world_state.ensure(s); life.ensure(s); town.ensure(s)
t = town.use_item(s, 'radish_seeds', '', "I'm going to eat my bread now")['text']
assert t.startswith('Handled the radish seeds.') and 'did not come of it' in t and '(I' not in t, t
assert 'did not come of it' in inner.first_person(t)
assert town.use_item(s, 'radish_seeds', '', '')['text'] == 'Handled the radish seeds. Nothing in particular happened.'
print('PASS v0.34.2: what he meant is kept apart from what happened.')
