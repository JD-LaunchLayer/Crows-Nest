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
