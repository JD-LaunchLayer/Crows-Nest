"""v0.28.2: beds can be dug over; dug soil gives sown crops an easier start, and slowly packs down again."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import garden
def fresh():
    st={'provisions':{'water_litres':40.,'pantry':0.},'possessions':{'radish_seeds':2}};garden.ensure(st);return st
st=fresh();r=garden.work(st,2,'dig');assert r['success'] and 'Dug over bed 2' in r['text'] and 'crumbly' in r['text'], r
b=st['garden']['beds'][1];assert b['tilth']>.5 and b['weeds']==0
garden.advance(st,24*30,200);assert b['tilth']<.2, 'dug soil packs down over a month'
# Dug beds grow faster than undug ones.
a=fresh();d=fresh();garden.work(d,1,'dig')
for s in (a,d):
    garden.work(s,1,'sow','radish_seeds');s['garden']['beds'][0]['moisture']=1.
    for _ in range(10):garden.advance(s,24,190);s['garden']['beds'][0]['moisture']=1.
assert d['garden']['beds'][0]['growth']>a['garden']['beds'][0]['growth']
assert not garden.work(d,1,'dig')['success'], 'cannot dig a bed with plants in it'
print('PASS v0.28.2: digging over a bed; easier start for what is sown; dug soil settles again.')
