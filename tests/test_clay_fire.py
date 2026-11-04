"""v0.33.0 (phase 2b): press, wet, cover, take, rub; clay dried and fired; earth over a fire; cuts and burns; edges.

All outcomes come from the world's rules and are told as what he sees and feels, never by name or as a hint.
"""
import contextlib, importlib.util, io, re, shutil, sys, tempfile
from datetime import datetime, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
td=tempfile.mkdtemp();shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
spec=importlib.util.spec_from_file_location('crow_clay',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
import handwork, materials, senses, life
FORBIDDEN=[r'\bunlock',r'\byou (can|could) now\b',r'\blearn(ed|t) (how|to)\b',r'\brecipe',r'\bcrafting\b',r'\btry (making|building)\b',
           r'\byou should\b',r'\bhint\b',r'\btip:',r'\bcharcoal\b',r'\bclay\b',r'\bkiln\b',r'\bpot(tery)?\b',r'\bbrick',r'\bceramic',r'\bsharpen',r'\bwhetstone\b']
texts=[]
def say(r):texts.append(r['text']);return r
T=[datetime(2026,12,21,11,0)]
def at(dt):T[0]=dt;app.CLOCK_OVERRIDE=lambda:T[0].replace(tzinfo=app.TZ);app.clock()
def dry_hour(d):
    while senses.weather({'clock':{'iso':d.isoformat()}})['rain']:d+=timedelta(hours=1)
    return d
at(dry_hour(datetime(2026,12,21,11)));st=app.state;st['location']='cabin';st['daylight']=1.
lot=lambda m,kg,moist,**k:materials.add(st,m,kg,moisture=moist,**k)['id']
L=lambda i:handwork._lot(st,i)
axe=('tool','axe')
def fire(wood=6.):
    f=lot('flax',.2,.02);w=lot('mixed_wood',wood,.1);flint=lot('flint',1,0.)
    hid=handwork.pile(st,f,.2)['heap'];handwork.pile(st,w,wood);h=handwork._heap(st,hid)
    for i in range(80):
        at(T[0]+timedelta(minutes=3));handwork.strike(st,('lot',flint),axe,h['id'])
        if h['lit']:return h
    raise SystemExit('no fire')

# Pressing: too dry crumbles, too wet slumps, damp enough takes the shape he describes.
dry=lot('clay',1,.05);wet_=lot('clay',1,.6);good=lot('clay',2,.3)
assert 'crumbled' in say(handwork.press(st,dry,'a small bowl'))['text'] and not L(dry).get('shape')
assert 'slumped' in say(handwork.press(st,wet_,'a small bowl'))['text'] and not L(wet_).get('shape')
sand=lot('sand',2,0.)
r=say(handwork.press(st,good,'a small round bowl',sand,.4,1.5));assert r['success'] and 'grittier' in r['text']
shaped=next(l for l in st['stock']['lots'] if l.get('shape')=='a small round bowl')
assert abs(shaped['mass_kg']-1.9)<1e-6 and shaped['temper']=={'sand':.4} and abs(L(good)['mass_kg']-.5)<1e-6
assert any('a small round bowl' in w for w in handwork.to_hand(st)), 'he knows it by his own words'
# Wet clay in a fire bursts; dried, a long time in the fire changes it for good.
damp=lot('clay',1,.3);handwork.press(st,damp,'a flat slab')
damp_lot=next(l for l in st['stock']['lots'] if l.get('shape')=='a flat slab')
h=fire(12.)
r=say(handwork.heat(st,h['id'],damp_lot['id'],60));assert 'burst' in r['text'] and damp_lot['material']=='fired_clay' and damp_lot['form']=='broken shards'
shaped['moisture']=.02
r=say(handwork.heat(st,h['id'],shaped['id'],90));assert shaped['material']=='fired_clay' and shaped['form'] in ('fired','cracked'), r
# Still hot: picking it up burns, and he lets go.
assert shaped['temperature']>100 and 'still hot' in ' '.join(handwork.to_hand(st))
r=say(handwork.pile(st,shaped['id'],1));assert not r['success'] and 'burned' in r['text']
assert any(i['kind']=='burn' for i in st['body']['injuries'])
handwork._cool(st,2);assert not shaped.get('temperature')
r=say(handwork.wet(st,shaped['id'],.3));assert 'stayed hard' in r['text']
# Fired pieces ring when struck.
stone=lot('stone',2,0.)
r=say(handwork.strike(st,('lot',shaped['id']),('lot',stone)));assert 'ringing' in r['text'] or 'broke' in r['text']
# Wetting a dried unfired shape turns it back to mud.
mud=lot('clay',1,.3);handwork.press(st,mud,'a cup');cup=next(l for l in st['stock']['lots'] if l.get('shape')=='a cup')
r=say(handwork.wet(st,cup['id'],1));assert 'shape is gone' in r['text'] and not cup.get('shape')
# Earth heaped over a burning fire: it smoulders, and the wood turns to light black lumps that burn hotter.
h2=fire(8.)
earth=lot('sand',3,.2);r=say(handwork.cover(st,h2['id'],earth,3));assert h2['covered'] and 'smoke seeps' in r['text']
for i in range(10):
    at(T[0]+timedelta(hours=1));handwork.advance(st,1)
assert not h2['lit'], 'it goes out when the wood is done'
r=say(handwork.take(st,h2['id']));assert r['success']
black=[l for l in st['stock']['lots'] if l['material']=='charcoal']
assert black and 1.5<sum(l['kg'] if 'kg' in l else l['mass_kg'] for l in black)<2.2, black
assert any('covered fire' in w for w in handwork.to_hand(st))
# Reaching into an open fire burns.
h=fire(6.);r=say(handwork.take(st,h['id']));assert not r['success'] and 'burned' in r['text']
# The lumps make a hotter fire.
for l in black:handwork.feed(st,h['id'],l['id'],l['mass_kg'])
assert handwork._hot_fire(h)
# Edges: the glassy stone wears the steel; ordinary stone, wet, brings it back.
st['tool_condition']['axe']=.5;fl=lot('flint',1,0.)
for i in range(5):handwork.strike(st,('lot',fl),axe)
assert st['tool_condition']['axe']<.5
before=st['tool_condition']['axe'];whet=lot('stone',1,0.)
handwork.wet(st,whet,.2);r=say(handwork.rub(st,axe,('lot',whet),60))
assert st['tool_condition']['axe']>before+.15 and 'brightened' in r['text'], (before,st['tool_condition'])
r=say(handwork.rub(st,axe,('lot',fl),10));assert 'scratches' in r['text']
# Two sticks rubbed together: heat and scorching, no ember.
w1=lot('hazel',1,.1);w2=lot('birch',1,.1);assert 'No ember' in say(handwork.rub(st,('lot',w1),('lot',w2),30))['text']
# Cuts and burns slow his hands and heal by themselves.
st['body']['injuries']=[];life.injure(st,'cut','thumb',.4);slow=life.hand_rate(st);assert slow<.7
assert any('cut on my thumb' in x for x in life.perceive(st)['sensations'])
life.heal(st,24*5);assert not st['body']['injuries'] and life.hand_rate(st)==1
d={'verb':'press','interaction_params':{}};base=app.handwork_duration(d);life.injure(st,'burn','hand',.5)
assert app.handwork_duration(d)>base
for t in texts:
    for p in FORBIDDEN:assert not re.search(p,t.lower()),(p,t)
for w in handwork.to_hand(st):
    for p in FORBIDDEN:assert not re.search(p,w.lower()),(p,w)
print('PASS v0.33.0: mud shaped, dried, burst or changed in the fire; smothered fires leave black lumps; edges wear and are rubbed keen; cuts and burns heal.')
