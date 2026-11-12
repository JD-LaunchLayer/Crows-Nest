"""v0.36.23: asked to read the posted terms in full, Edda reads the slate word for word, every time."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import life, town, world_state
s = {'materials': 0., 'stone': 0., 'creations': [], 'clock': {'iso': '2027-04-14T10:00:00'}}
world_state.ensure(s); life.ensure(s); town.ensure(s)
ask = ("Edda, I'm still not agreeing to the bundle or the crate work. Before I agree to any work or spend any coin, "
       "I'd like you to read the full posted food work terms aloud, term by term, from start to finish.")
r = town.counter_reply(s, ask)
assert r and town.slate_text(s) in r and 'no other terms' in r, r
assert 'Sweep' in r and 'Carry' in r and 'pays' in r, r
assert town.counter_reply(s, ask) == r, 'read again, the same words'
assert town.counter_reply(s, 'What does the crate job pay?') is None
assert not town.asks_terms('I agreed to those terms yesterday.')
print('PASS v0.36.23: the slate is read to him as written whenever he asks for the posted terms in full.')
