"""v0.33.2: "what is near me" is measured from where he really is at every place, never from the middle of the green."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import actions, world_state, life, town
s = {'materials': 0., 'stone': 0., 'creations': []}
world_state.ensure(s); life.ensure(s); town.ensure(s)
for place in set(actions.places().values()) | {'cafe', 'shop', 'garden'}:
    assert place in world_state.PLACE_SPOTS, f'{place} has no spot, so nearby() would measure from the green'
s['location'] = 'cafe'; assert world_state.nearby(s)['objects'][0]['id'] == 'internet_cafe'
s['location'] = 'shop'; assert world_state.nearby(s)['objects'][0]['id'] == 'trading_post'
print('PASS v0.33.2: every place measures "near me" from where he stands there.')
