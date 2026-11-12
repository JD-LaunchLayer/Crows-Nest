"""v0.36.22: Edda's replies end on whole sentences, and she can read him the request book as it stands."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import town
long = ' '.join(f'On 04-{10 + i} the ledger says: "Bought one bundle for 3 gold." That is line {i}.' for i in range(20))
r = town.whole_sentences(long, 900)
assert len(r) <= 900 and r.endswith('.') and len(r) > 400, r[-80:]
assert town.whole_sentences('Short and whole.') == 'Short and whole.'
st = {}
assert town.request_book(st) == ['(the book is empty)']
st['trading'] = {'requests': []}; st['trading']['requests'].append({'item': 'more bread', 'first': '2027-04-10T09:00', 'last': '2027-04-11T09:00', 'times': 2})
assert town.request_book(st) == ['2027-04-10: "more bread" (written 2 times)'], town.request_book(st)
P = town.KEEPER_PERSONA
assert 'request book is a different book' in P and 'read each one whole' in P
print('PASS v0.36.22: Edda reads whole lines, never fragments, and can read the request book as it stands.')
