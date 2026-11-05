"""v0.34.5: Edda is an elf woman, drawn with care for Jordan and seen plainly by Crow; and a warmth meter for Jordan."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import senses, town
for hour in (3, 8, 10, 13, 15, 18, 22):
    line = senses.outside({'location': 'shop', 'clock': {'iso': f'2026-12-21T{hour:02d}:30:00+00:00'}})
    assert 'a tall elf woman' in line and 'she is ' in line, line
assert 'Edda' not in senses.outside({'location': 'cabin', 'clock': {'iso': '2026-12-21T10:30:00+00:00'}})
assert 'You are an elf woman' in town.KEEPER_PERSONA and 'never remark on it' in town.KEEPER_PERSONA
js = (ROOT / 'world.js').read_text(); html = (ROOT / 'index.html').read_text()
assert 'eddaHead' in js and 'braid' in js and 'E_SHAWL' in js, 'she is modelled'
assert 'id="warmthMark"' in html and "$('warmthMark')" in js and 'never sees' in html, 'the warmth meter is for Jordan only'
print('PASS v0.34.5: Edda is an elf woman he can see; Jordan has a warmth meter.')
# v0.36.2: asked plainly about work, she answers plainly (asked, not volunteered).
assert 'When he asks you plainly about work' in town.KEEPER_PERSONA and 'Do not put him off' in town.KEEPER_PERSONA
print('PASS v0.36.2: Edda answers plain questions about work plainly.')
# v0.36.5: she offers no food that is not on her shelves; and warmth by a stove is felt.
assert 'there is no soup, tea or meal of yours to offer' in town.KEEPER_PERSONA
import life, world_state, inner
b = {'materials': 0., 'stone': 0., 'creations': [], 'location': 'shop', 'action': 'talk', 'clock': {'iso': '2026-12-23T12:00:00+00:00'}}
world_state.ensure(b); life.ensure(b); b['body']['chill'] = 0
assert 'Warm through by the stove; hands and feet warm.' in life.perceive(b)['sensations']
assert 'Warm through by the stove; hands and feet warm.' in inner.BODY
b['body']['chill'] = .4; assert not any('Warm through' in x for x in life.perceive(b)['sensations'])
b['body']['chill'] = 0; b['location'] = 'woods'; assert not any('Warm through' in x for x in life.perceive(b)['sensations'])
print('PASS v0.36.5: no invented food from Edda; warm through by a stove is felt.')
# v0.36.11: at night her stove is banked, not out: the post is cool but sheltered, never as cold as outside.
import senses
night = {'location': 'shop', 'clock': {'iso': '2027-01-12T03:00:00+00:00'}}
assert senses.felt_temp(night, 'talk') >= 12 and 'banked low' in senses.inside_line(night)
print('PASS v0.36.11: the post at night is cool but sheltered by the banked stove.')
# v0.36.11: an agreed favour is said to be agreed; the same question asked over and over gets a kind, plain end.
assert 'it is agreed and' in town.KEEPER_PERSONA and 'do not keep offering to go over it again' in town.KEEPER_PERSONA
print('PASS v0.36.11: Edda says what is agreed, and ends a loop kindly.')
