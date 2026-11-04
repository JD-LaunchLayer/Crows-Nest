"""v0.30.17: weather, warmth, sky and woodland sounds, perceived plainly, by day and by night alike."""
import json, re, sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import senses, inner
NAMES=['robin','blackbird','owl','fox','woodpecker','pigeon','rook','cuckoo','deer']
FEELINGS=['lovely','beautiful','pleasant ','nice','gloomy','dreary','miserable','cosy','peaceful']
seen=set();kinds={'rain':0,'frost':0,'stars':0,'moon':0,'sun':0}
for month,days in ((12,31),(7,31),(4,30)):
    for d in range(1,days+1):
        for h,dl in ((3,0),(8,.5),(14,.9),(22,0)):
            st={'clock':{'iso':datetime(2026,month,d,h,0).isoformat()},'daylight':dl,'location':'woods'}
            before=json.dumps(st,sort_keys=True);t=senses.outside(st)
            assert json.dumps(st,sort_keys=True)==before, 'reading never changes his life'
            assert t==senses.outside(st), 'the same moment reads the same'
            assert not re.search(r'\d',t), t
            assert not any(n in t.lower() for n in NAMES), t
            assert not any(f in t.lower() for f in FEELINGS), t
            kinds['rain']+=' falling' in t;kinds['frost']+='Frost' in t;kinds['stars']+='stars' in t
            kinds['moon']+='moon' in t;kinds['sun']+='sun' in t
            seen.add(t)
assert all(kinds.values()), kinds
assert len(seen)>200, 'the world varies from day to day and hour to hour'
# Night is given as much to notice as day.
night=[senses.outside({'clock':{'iso':datetime(2026,12,d,23).isoformat()},'daylight':0,'location':'woods'}) for d in range(1,29)]
day=[senses.outside({'clock':{'iso':datetime(2026,12,d,13).isoformat()},'daylight':.9,'location':'woods'}) for d in range(1,29)]
assert abs(sum(map(len,night))-sum(map(len,day)))<.35*sum(map(len,day))
# Indoors he hears it from inside; and it is part of what he sees each moment.
st={'clock':{'iso':'2026-12-18T02:00:00','date':'Fri 18 Dec','time':'02:00'},'daylight':0,'location':'cabin'}
assert 'From inside I can hear' in senses.outside(st)
assert senses.outside(st) in inner.scene(st,{},{})
print('PASS v0.30.17: weather, warmth, sky and sounds by day and night, plainly, unchanged by reading.')
# v0.30.18: warmth where he is: cold in the open and (no fire) in his cabin; warm in bed, the cafe, the reading cabin.
import contextlib, importlib.util, io, shutil, tempfile
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_cold',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,20,2,0,tzinfo=app.TZ);app.clock();st=app.state;b=st['body']
    st['location']='woods';b['chill']=0;app.life.advance(st,3*3600,'explore');out=b['chill']
    assert out>.35 and any('cold' in x.lower() for x in app.life.perceive(st)['sensations']), out
    st['location']='cabin';app.life.advance(st,3*3600,'sleep');assert b['chill']<.05, 'under the covers he warms up'
    st['location']='cafe';b['chill']=.8;app.life.advance(st,3600,'browse');assert b['chill']<.1
    st['location']='cabin';line=senses.outside(st);assert 'no fire' in line and 'bed is the warm place' in line, line
    st['location']='cafe';assert 'warm in here from the stove' in senses.outside(st)
    assert "I'm cold" in inner.BODY['Cold; hands and feet numb.']
print('PASS v0.30.18: cold in the open and his fireless cabin; warm in bed and by the stoves.')
# v0.30.19: a stove on Edda's shelves; once his, he lights and feeds it with his own wood, and it warms the cabin while it burns.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_stove',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,20,22,0,tzinfo=app.TZ);app.clock();st=app.state;b=st['body']
    t=app.town;assert 'stove' in t.ensure(st)['stock'] and 'kilo and a half an hour' in t.ITEM_KNOWLEDGE['stove']
    st['trading']['credit']=20.;r=t.trade(st,'buy','stove',1,app.now().isoformat());assert r['success'] and st['possessions']['stove']==1
    st['location']='cabin';assert 'the stove is cold' in senses.outside(st)
    st['materials']=0.;r=t.use_item(st,'stove','','');assert not r['success'] and 'no wood' in r['text']
    st['materials']=10.;r=t.use_item(st,'stove','','put in 3 kg');assert r['success'] and st['materials']==7. and 'about 2 hours' in r['text'], r
    assert senses.stove_lit(st) and senses.felt_temp(st)==16. and 'stove is burning' in senses.outside(st)
    b['chill']=.8;app.life.advance(st,3600,'rest');assert b['chill']<.1, 'warm by the stove'
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,21,1,0,tzinfo=app.TZ);app.clock()
    assert not senses.stove_lit(st), 'it goes out when the wood is gone'
    st['paused']=False;d={**app.DECISION_DEFAULTS,'action':'use_item','use_item':'stove','use_how':'','intention':'warm up','reason':'cold'}
    app.start_action(d,1);assert st['location']=='cabin'
print('PASS v0.30.19: a stove he can buy, light and feed with his own wood; warm while it burns, cold when it is out.')
# v0.30.20: resting in bed under the covers is warm; sitting up awake in the cold cabin is not.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_inbed',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,20,3,0,tzinfo=app.TZ);app.clock();st=app.state;b=st['body'];st['paused']=False
    for words,warm in (('Stay under the covers in my cabin and rest',True),('Sit quietly at the table',False)):
        d={**app.DECISION_DEFAULTS,'action':'rest','intention':words,'reason':'r'};app.start_action(d,1);st['pending']=None
        b['chill']=.6;app.life.advance(st,3600,'rest');assert (b['chill']<.1)==warm,(words,b['chill'])
print('PASS v0.30.20: resting under the covers is warm; sitting up in a cold cabin is not.')
