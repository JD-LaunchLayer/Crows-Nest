"""v0.24: the harp (stock, Edda's knowledge, notation, measured playing, practice, sheet music) and honest exploring."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import music, town
notes,problems=music.parse('C4:1 E4:0.5 Bb3:1 F#4:2 R:1 C6:1 X9:1')
assert [n for n,_ in notes]==[60,64,58,66,None] and len(problems)==2 and 'outside' in problems[0]
assert music.write(notes).startswith('C4:1 E4:0.5 A#3:1')
for t in music.SONGBOOK:assert music.parse(t['notes'])[1]==[], t['title']
assert 'lever' in town.ITEM_KNOWLEDGE['harp'] and 'harp' not in town.KEEPER_PERSONA.lower(), 'Edda knows harps; nothing pushes him to ask'
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_harp',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    from datetime import datetime
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,11,12,0,tzinfo=app.TZ)  # daylight, whatever the real time
    st=app.state;app.state['paused']=False
    assert st['trading']['stock']['harp']['price']==12 and 'sheet_music' in st['built_world']['objects']
    assert 'play_music' not in app.available_actions()
    st['possessions']['harp']=1;assert 'play_music' in app.available_actions()
    base={**app.DECISION_DEFAULTS,'action':'play_music','reason':'r','intention':'i'}
    # Compose: the piece is kept, played once, measured.
    app.start_action({**base,'music_mode':'compose','title':'First tune','notes':'C4:1 D4:1 E4:1 G4:2 E4:1 D4:1 C4:2','tempo':80},1)
    perf=st['pending']['music']['performance'];assert len(perf['played'])==7
    app.tick(1800);m=app.finish_action();assert 'Played "First tune"' in m['event'] and st['music']['pieces'][0]['times_played']==1
    # Practice makes it steadier: over many performances, slips fall with hours and familiarity.
    for i in range(2):
        app.start_action({**base,'music_mode':'practise','piece_id':1},1);app.tick(1800);app.finish_action()
    piece=st['music']['pieces'][0];hours=st['music']['hours'];plays=piece['times_played']
    early=sum(music.perform(st,{**piece,'times_played':0},0,s)['slips'] for s in range(40))
    st['music']['hours']=60
    late=sum(music.perform(st,{**piece,'times_played':40},0,s)['slips'] for s in range(40))
    assert late<early/3,(early,late);st['music']['hours']=hours
    # Learning from sheet music needs to have seen the shelf.
    assert 'learn' not in app.parameter_request({**base})[1]['music_mode']['enum']
    d={**app.DECISION_DEFAULTS,'action':'inspect','object_id':'sheet_music','intention':'look','reason':'r'}
    st['daylight']=1;app.start_action(d,1);app.tick(60);ev=app.finish_action()['event'];assert 'Ode to Joy' in ev and st['music']['songbook_seen']
    app.start_action({**base,'music_mode':'learn','songbook':music.SONGBOOK[2]['title']},1);app.tick(1800);app.finish_action()
    assert any(p['source']=='sheet music' for p in st['music']['pieces'])
    # Unplayable writing is reported, not guessed.
    app.start_action({**base,'music_mode':'compose','title':'x','notes':'Z9:1'},1);app.tick(300);ev=app.finish_action()['event']
    assert 'could not play' in ev
    # Exploring walks through a place and notices things, as its description says.
    st['daylight']=1;app.start_action({**app.DECISION_DEFAULTS,'action':'explore','explore_area':'deeper_woods','reason':'r','intention':'i'},1)
    app.tick(1200);ev=app.finish_action()['event'];assert ev.startswith('Walked through the deeper woods') and 'Gathered' in ev
print('PASS v0.24: harp in stock, Edda knows it unprompted; notation; measured playing improves with practice; sheet music; honest exploring.')
