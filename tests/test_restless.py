"""v0.34.4: lying awake for hours stiffens and unsettles him, as it would anyone; moving about loosens him again.

On 21 December he lay in bed resting from midnight to dusk, warm, fed enough and not sleepy, and nothing in his body
ever changed. A real body would have grown stiff and restless long before.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import life, world_state, inner
s = {'materials': 0., 'stone': 0., 'creations': [], 'location': 'cabin', 'action': 'rest', 'in_bed': True,
     'clock': {'iso': '2026-12-21T12:00:00+00:00'}, 'daylight': .5}
world_state.ensure(s); life.ensure(s); s['body']['sleep_debt'] = 0.
feel = lambda: ' '.join(life.perceive(s)['sensations'])
life.advance(s, 2 * 3600, 'rest'); assert 'stiff' not in feel(), 'a couple of hours is fine'
life.advance(s, 3600, 'rest'); assert 'Limbs stiff' in feel()
life.advance(s, 3 * 3600, 'rest'); assert 'Restless and stiff' in feel()
assert all(x in inner.BODY for x in ('Limbs stiff from lying still a long while.', 'Restless and stiff from lying still for hours.'))
life.advance(s, 3600, 'explore'); assert 'stiff' not in feel(), 'an hour up and about loosens him'
s['body']['still_hours'] = 6; s['body']['sleep_debt'] = 6; assert 'stiff' not in feel(), 'lying still is no bother when he is sleepy'
life.advance(s, 3 * 3600, 'sleep'); assert s['body']['still_hours'] == 6, 'sleeping neither stiffens nor loosens'
print('PASS v0.34.4: hours lying awake stiffen and unsettle him; moving loosens him.')
