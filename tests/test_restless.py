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
# v0.36.1: deciding what to do next while still lying in bed is lying still, not moving about.
s['body']['still_hours'] = 0; s['body']['sleep_debt'] = 0; s['in_bed'] = True; s['action'] = 'rest'
for _ in range(12):
    life.advance(s, 17 * 60, 'rest'); life.advance(s, 4 * 60, 'reflect')
assert s['body']['still_hours'] > 4, s['body']['still_hours']
s['in_bed'] = False; s['action'] = 'craft'; before = s['body']['still_hours']
life.advance(s, 600, 'reflect'); assert s['body']['still_hours'] == before, 'thinking while up neither stiffens nor loosens'
# v0.36.1: lying awake is not sleep: a night of resting in bed, never sleeping, ends in sleepiness.
s['body']['sleep_debt'] = 0; s['in_bed'] = True; s['action'] = 'rest'; s['daylight'] = 0.
for h in range(10):
    s['minute'] = (17 + h) * 60 % 1440; life.advance(s, 3600, 'rest')
assert s['body']['sleep_debt'] > 4, s['body']['sleep_debt']
s['body']['sleep_debt'] = 9; life.advance(s, 3600, 'rest'); assert s['body']['sleep_debt'] < 9, 'a rest still eases real sleepiness'
print('PASS v0.34.4: hours lying awake stiffen and unsettle him; moving loosens him.')
