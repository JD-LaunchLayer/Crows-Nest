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
