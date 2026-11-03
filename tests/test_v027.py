"""v0.27: gold and silver; plain notes beside things the world got wrong; sleep from what he does, waking when rested; no 'night' label."""
import contextlib, importlib.util, io, json, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import town, story, life
assert town.money(3.5)=='3 gold 5 silver' and town.money(.5)=='5 silver' and town.money(2)=='2 gold' and town.money(0)=='nothing'
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_v027',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,28,11,0,tzinfo=app.TZ);app.clock();st=app.state
    ctx=app.decision_context();assert 'night' not in ctx['clock'] and 'gold' in json.dumps(ctx['notes_from_the_world'])
    assert 'gold' in json.dumps(town.board(st)) and 'credit' not in json.dumps(town.board(st))
    st['trading']['credit']=1.5;r=town.trade(st,'buy','provisions_bundle',1,'2026-11-28T11:00')
    assert 'Not enough money' in r['text'] and '1 gold 5 silver' in r['text'], r
    assert 'gold' in st['trading']['ledger'][0]['text'] or any('gold and silver' in l['text'] for l in st['trading']['ledger'])
    # Phantoms: his words kept, a plain note added once.
    st['phantoms_annotated']=False
    t=story.add_thread(st,'Whether Tam has repaired the cracked board','post',1,'t')
    p=story.add_promise(st,'I will find the solid part rule before Monday','Edda Thorne','t')
    story.annotate_phantoms(st)
    assert t['text']=='Whether Tam has repaired the cracked board' and 'no Tam' in t['world_note']
    assert 'never a "solid part" rule' in p['world_note']
    assert any('note_from_the_world' in x for x in story.open_items(st)['promises'])
    # Sleep: an idle day makes him far less sleepy than a working one, and he wakes when rested.
    b=st['body'];b['sleep_debt']=0;life.advance(st,8*3600,'read');idle=b['sleep_debt']
    b['sleep_debt']=0;life.advance(st,8*3600,'fell_tree');worked=b['sleep_debt']
    assert idle<4<worked, (idle,worked)
    b['sleep_debt']=8.;long=life.sleep_needed_seconds(st);b['sleep_debt']=1.;short=life.sleep_needed_seconds(st)
    assert 6*3600<long<9*3600 and short<2*3600, (long,short)
    d={**app.DECISION_DEFAULTS,'action':'sleep','intention':'sleep','reason':'r'};st['paused']=False;b['sleep_debt']=2.
    app.start_action(d,1);assert st['pending']['duration']<3*3600, 'a nap by day lasts as long as he needs, not a set time'
print('PASS v0.27: gold and silver; plain notes beside the phantoms; tiredness from what he does; waking when rested; no night label.')
