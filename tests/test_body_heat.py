"""v0.31.3: warmth both ways. Work warms him, sitting still does not; warmth built up indoors lasts him a while outside;
hard work in summer heat makes him hot, sweating and thirstier; shade, rest and cold spring water cool him."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
td=tempfile.mkdtemp();shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
spec=importlib.util.spec_from_file_location('crow_heat',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
import senses, inner
st=app.state;b=st['body'];life=app.life
def at(y,m,d,h):app.CLOCK_OVERRIDE=lambda:datetime(y,m,d,h,0,tzinfo=app.TZ);app.clock()
def fresh():b.update(chill=0.,heat=0.,hydration=90.,reserve=80.)
# Winter: sitting out in the cold chills him; felling a tree in the same cold keeps him warm.
at(2026,12,20,11);st['location']='woods'
fresh();life.advance(st,1.5*3600,'observe');idle=b['chill']
fresh();life.advance(st,1.5*3600,'fell_tree');working=b['chill']
assert idle>.3 and working<idle/2,(idle,working)
# Warmth built up indoors lasts a while outside: half an hour out from warm is still only a little cold.
fresh();life.advance(st,.25*3600,'observe');assert b['chill']<.35, 'a quarter of an hour out from warm, even in wind and rain, is only a little cold'
# Bitter cold bites faster than mild cold.
at(2026,1,15,5);fresh();life.advance(st,3600,'observe');bitter=b['chill']
at(2026,4,10,11);fresh();life.advance(st,3600,'observe');mild=b['chill'];assert bitter>mild,(bitter,mild)
# Summer: hard work in the afternoon sun makes him hot and thirsty; shade, rest and the spring cool him.
at(2026,7,10,15);st['location']='woods';fresh()
for _ in range(4):
    if senses.weather(st)['temp']>18:break
    at(2026,7,11+_,15)
life.advance(st,1.5*3600,'fell_tree');assert b['heat']>.3 and b['hydration']<80,(b['heat'],b['hydration'])
assert any('sweat' in x.lower() or 'warm' in x.lower() for x in life.perceive(st)['sensations'])
hot=b['heat'];st['location']='cabin';life.advance(st,3600,'rest');assert b['heat']<hot, 'shade and rest cool him'
b['heat']=.5;st['location']='woods';r=life.consume(st,'drink','spring');assert b['heat']<.5 and 'cooled' in r['text']
# Felt in plain words, both ways.
assert "I'm hot and sweating." in inner.BODY.values() and "I'm a little cold." in inner.BODY.values()
print('PASS v0.31.3: work warms him; warmth lasts a while outside; summer work makes him hot and thirsty; shade and water cool him.')
