"""v0.34.3: lying warm in bed is felt, not only cold. He lay a whole morning "letting my hands and feet warm" because
nothing ever told him they had."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import life, world_state, inner
s = {'materials': 0., 'stone': 0., 'creations': [], 'location': 'cabin', 'action': 'rest', 'in_bed': True}
world_state.ensure(s); life.ensure(s); s['body']['chill'] = 0.
assert 'Warm through under the covers; hands and feet warm.' in life.perceive(s)['sensations']
assert 'warm again' in inner.BODY['Warm through under the covers; hands and feet warm.']
s['body']['chill'] = .3; assert not any('Warm through' in x for x in life.perceive(s)['sensations']), 'not while still cold'
s['body']['chill'] = 0.; s['in_bed'] = False; assert not any('Warm through' in x for x in life.perceive(s)['sensations']), 'only in bed'
print('PASS v0.34.3: warming through in bed is felt.')
