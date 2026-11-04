"""v0.32.0: pile, strike, feed, heat, dry. Sparks only from glassy stone on steel; they take only in fine, dry stems;
a fire burns its wood, warms him, and goes out; rain puts out a fire in the open; knapping gives sharp flakes.
Every outcome is sensory and free of hints."""
import contextlib, importlib.util, io, re, shutil, sys, tempfile
from datetime import datetime, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
td=tempfile.mkdtemp();shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
spec=importlib.util.spec_from_file_location('crow_hand',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
import handwork, materials, senses
FORBIDDEN=[r'\bunlock',r'\byou (can|could) now\b',r'\blearn(ed|t) (how|to)\b',r'\brecipe',r'\bcrafting\b',r'\btry (making|building)\b',r'\byou should\b',r'\bhint\b',r'\btip:',r'\bfire.?starting\b',r'\btinder\b',r'\bknapp',r'\bflint\b',r'\bcharcoal\b']
texts=[]
def say(r):texts.append(r['text']);return r
T=[datetime(2026,12,21,11,0)]
def at(dt):T[0]=dt;app.CLOCK_OVERRIDE=lambda:T[0].replace(tzinfo=app.TZ);app.clock()
def dry_day(start):
    d=start
    while senses.weather({'clock':{'iso':d.isoformat()}})['rain']:d+=timedelta(hours=1)
    return d
at(dry_day(datetime(2026,12,21,11)));st=app.state;st['location']='workbench';st['daylight']=1.
lot=lambda m,kg,moist,src='':materials.add(st,m,kg,moisture=moist,source=src)['id']
flint=lot('flint',3,0.);stone=lot('stone',2,0.);wood_id=min(l['id'] for l in st['stock']['lots'] if l['material']=='mixed_wood') if st['materials'] else lot('mixed_wood',10,.15)
damp_reed=lot('reed',.3,.3);dry_flax=lot('flax',.2,.05)
axe=('tool','axe')
# What he has to hand, by how he knows it; no material names.
words=list(handwork.to_hand(st));assert 'my axe' in words and not any(re.search(r'\b(flint|flax|reed|clay)\b',w) for w in words), words
# Sparks only from the glassy stone on steel; plain stone on steel only knocks.
r=say(handwork.strike(st,('lot',flint),axe));assert 'sparks' in r['text']
r=say(handwork.strike(st,('lot',stone),axe));assert 'sparks' not in r['text']
# Damp stems never take a spark.
say(handwork.pile(st,damp_reed,.3));say(handwork.pile(st,wood_id,3))
heap=handwork.ensure(st)['heaps'][-1]['id']
for i in range(12):
    at(T[0]+timedelta(minutes=5));st['location']='workbench';r=say(handwork.strike(st,('lot',flint),axe,heap))
    assert not handwork._heap(st,heap)['lit'], r
# Fine, dry stems do, sooner or later, and the wood above catches.
say(handwork.pile(st,dry_flax,.2));lit=False
for i in range(40):
    at(T[0]+timedelta(minutes=5));r=say(handwork.strike(st,('lot',flint),axe,heap))
    if handwork._heap(st,heap)['lit']:lit=True;break
assert lit and 'flame' in r['text'], 'dry stems take a spark in the end'
# Beside it he is warm; the fire burns its wood about 1.5 kg an hour and goes out when it is gone.
assert handwork.lit_here(st) and senses.felt_temp(st,'rest')>=15 and 'fire is burning' in handwork.line_here(st)
fuel=handwork._fuel(handwork._heap(st,heap));handwork.advance(st,1.);assert abs((fuel-handwork._fuel(handwork._heap(st,heap)))-1.5)<.31
say(handwork.feed(st,heap,wood_id,1.5));handwork.advance(st,10.)
assert not handwork._heap(st,heap)['lit'] and 'ash' in handwork.line_here(st)
# Heating and drying change dampness.
r=say(handwork.heat(st,heap,damp_reed if handwork._lot(st,damp_reed) else wood_id,30));assert not r['success'], 'no fire, no heat'
wet=lot('reed',.5,.3);before=handwork._lot(st,wet)['moisture'];st['location']='cabin';r=say(handwork.dry(st,wet,120))
assert handwork._lot(st,wet)['moisture']<before
# Rain puts out a fire in the open.
st['location']='workbench';wet_hour=T[0]
rains=lambda d:senses.weather({'clock':{'iso':d.isoformat()}})['rain'] in ('rain','heavy rain')
while not all(rains(wet_hour+timedelta(hours=k)) for k in range(3)):wet_hour+=timedelta(hours=1)
at(wet_hour-timedelta(hours=2));say(handwork.pile(st,lot('flax',.2,.0),.2));say(handwork.pile(st,wood_id,6))
h2=handwork.ensure(st)['heaps'][-1];h2['lit']=True
for k in range(3):at(wet_hour+timedelta(hours=k));handwork.advance(st,1.)
assert not h2['lit'] and handwork._fuel(h2)>1, 'the rain put it out with wood still in it'
# Knapping: glassy stone struck with stone gives sharp flakes now and then; plain stone on plain stone does not.
flakes=0
for i in range(30):
    at(T[0]+timedelta(minutes=7));r=say(handwork.strike(st,('lot',flint),('lot',stone)))
    flakes+='flake sprang off' in r['text']
assert flakes>=3 and any(l.get('form')=='flakes' for l in st['stock']['lots'])
r=say(handwork.strike(st,('lot',stone),('lot',lot('stone',1,0.))));assert 'Nothing else happened' in r['text']
# Practice makes knapping surer.
assert handwork._skill(st,'knapping')>handwork._skill(st,'nothing')
# Through his real choice: interact, then strike, by his own words.
at(dry_day(T[0]+timedelta(hours=1)));st['location']='workbench';st['paused']=False
say(handwork.pile(st,lot('flax',.2,0.),.2));say(handwork.pile(st,wood_id,2))
words=handwork.to_hand(st);fw=next(w for w,v in words.items() if v==('lot',flint));hp=list(handwork.heaps_here(st))[0]
app.model_call=lambda p,s,*a,**k:({'hypothesis':'','prediction':'','what':fw,'against':'my axe','heap':hp},1)
d=app.choose_hand_detail({'intention':'see what happens','action':'interact'},'strike')
app.start_action({**app.DECISION_DEFAULTS,'action':'interact','intention':'see','reason':'r',**d},1);st['pending']['remaining']=0
m=app.finish_action(None);texts.append(m['event']);assert 'park' in m['event']
# Nothing he is told names a recipe, a skill, the material, or what to try.
for t in texts:
    for pat in FORBIDDEN:assert not re.search(pat,t.lower()),(pat,t)
print('PASS v0.32.0: sparks only from glassy stone on steel; only dry stems catch; fires burn, warm and go out; rain douses; flakes by practice; all sensory.')
