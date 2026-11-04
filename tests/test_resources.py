"""v0.31.2: raw materials placed once in his woods, seen only by looking, never named; gathered only from places he
has seen; finite where they should be; plants grow back in season; what he takes becomes lots in his stock."""
import contextlib, copy, importlib.util, io, json, re, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
NAMES=['clay','flax','nettle','flint','iron','copper','tin\b','ore\b']   # reeds and sand are words anyone knows
def load(name):
    td=tempfile.mkdtemp();shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location(name,Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    return app
app=load('crow_res');import resources, materials, ecology
app.CLOCK_OVERRIDE=lambda:datetime(2026,12,19,11,0,tzinfo=app.TZ);app.clock();st=app.state
nodes=st['built_world']['resources'];kinds={n['kind'] for n in nodes.values()}
assert len(nodes)==14 and {'clay_bed','reeds','flax','nettles','flint','iron_hollow','copper_outcrop','tin_stones','sand_gravel'}==kinds
# Placed once, the same every time, beside everything already there; trees untouched; running again changes nothing.
trees=copy.deepcopy(st['built_world']['trees']);before=copy.deepcopy(nodes)
resources.ensure(st);assert nodes==before and st['built_world']['trees']==trees
assert load('crow_res2').state['built_world']['resources']==before, 'same seed, same places'
for n in nodes.values():
    assert all((n['x']-t['x'])**2+(n['z']-t['z'])**2>2.4**2 for t in trees.values()), n['id']
    area=resources.kinds()[n['kind']]['area'];assert ecology.in_area(area,n['x'],n['z']) or area=='woodland_edge', n
far=lambda k:min((v['x']**2+v['z']**2)**.5 for v in nodes.values() if v['kind']==k)
assert far('tin_stones')>far('copper_outcrop')-5>far('iron_hollow')-15 and far('tin_stones')>40
# Seen only by looking, by look and season, never named; nothing in the dark.
for when,dl in ((datetime(2026,12,19,11),1.),(datetime(2026,7,10,11),1.)):
    app.CLOCK_OVERRIDE=lambda w=when:w.replace(tzinfo=app.TZ);app.clock()
    for area in ecology.AREAS:
        for _,t in resources.facts(st,ecology,area,dl):
            assert not any(re.search(r'\b'+n,t.lower()) for n in NAMES), t
assert resources.facts(st,ecology,'spring_side',.05)==[]
winter=resources.look({'clock':{'iso':'2026-12-19T11:00:00'}},next(v for v in nodes.values() if v['kind']=='flax'))
summer=resources.look({'clock':{'iso':'2026-07-10T11:00:00'}},next(v for v in nodes.values() if v['kind']=='flax'))
assert winter!=summer and 'dead' in winter and 'blue' in summer
# Gathered only from a place he has seen; what he takes is a lot in his stock; the place has less.
app.CLOCK_OVERRIDE=lambda:datetime(2026,12,19,11,0,tzinfo=app.TZ);app.clock();st['daylight']=1.
clay=next(v for v in nodes.values() if v['kind']=='clay_bed')
assert resources.gather(st,clay['id'])['success'] is False and resources.known(st)=={}
r=ecology.observe(st,'spring_side','anything not yet recorded',353,1.,limit=8)
assert any('slick grey-brown mud' in f['text'] for f in r['findings']), [f['text'][:60] for f in r['findings']]
assert clay['id'] in resources.known(st) or any(i in resources.known(st) for i in nodes if nodes[i]['kind']=='clay_bed')
cid=next(i for i in resources.known(st) if nodes[i]['kind']=='clay_bed');c=nodes[cid];left=c['stock']
got=resources.gather(st,cid);assert got['success'] and c['stock']==round(left-4,2) and 'clings to my fingers' in got['text']
assert materials.totals(st)['clay']==4. and st['stock']['lots'][-1]['source']==cid and st['stock']['lots'][-1]['moisture']==.35
# Through the real decision path: the details offer only places he has seen, as he names them.
d={**app.DECISION_DEFAULTS,'action':'gather','intention':'take some','reason':'r'}
instr,props,ctx=app.parameter_request(d)
assert props['from_place']['enum'][1:]==sorted(set(resources.known(st).values()))
st['paused']=False;app.start_action({**d,'from_place':resources.kinds()['clay_bed']['label']},1);st['pending']['remaining']=0
m=app.finish_action(None);assert 'grey-brown mud' in m['event'] and materials.totals(st)['clay']==8.
# Finite: stone and ore never return; plants grow back only in their months; clay seeps back slowly.
tin=next(v for v in nodes.values() if v['kind']=='tin_stones');tin['stock']=0.;flax=next(v for v in nodes.values() if v['kind']=='flax');flax['stock']=0.
resources.advance(st,24*30);assert tin['stock']==0 and flax['stock']==0, 'nothing grows in December'
app.CLOCK_OVERRIDE=lambda:datetime(2027,5,1,11,0,tzinfo=app.TZ);app.clock();resources.advance(st,24*10)
assert 0<flax['stock']<=flax['capacity'] and tin['stock']==0
# Too dark without a lantern; nothing taken.
st['daylight']=0.;assert not resources.gather(st,cid)['success']
# Reading never changes his life.
before=json.dumps(st,sort_keys=True,default=str);resources.view(st);resources.known(st);resources.facts(st,ecology,'spring_side',1.)
assert json.dumps(st,sort_keys=True,default=str)==before
print('PASS v0.31.2: raw materials placed once, seen by look and season, gathered only where seen, finite or regrowing, kept as lots.')
