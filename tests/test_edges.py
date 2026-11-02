"""v0.21.6: the edge of what can be seen is stated plainly, and logged for the world builder only."""
import sys, tempfile, shutil, importlib.util, contextlib, io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import ecology
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_edges',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    st=app.state
    area='grove';tree=next(t for t in st['built_world']['trees'].values() if t['stage']=='standing' and ecology.in_area(area,t['x'],t['z']))
    first=ecology.observe(st,area,f'close look at {tree["id"]}',312,1.)
    assert first['edge'] is None and 'by eye' not in first['text']
    again=ecology.observe(st,area,f'close look at {tree["id"]}',312,1.)
    assert again['edge']['kind']=='seen_all' and 'by eye has been seen before' in again['text']
    other=next(t for t in st['built_world']['trees'].values() if not ecology.in_area(area,t['x'],t['z']))
    wrong=ecology.observe(st,area,f'look at {other["id"]}',312,1.)
    assert wrong['edge']['kind']=='not_here' and f'{other["id"]} is not in' in wrong['text']
    missing=ecology.observe(st,area,'mushrooms fungi toadstools',312,1.)
    assert missing['edge']['kind']=='not_found' and 'Nothing matching' in missing['text']
    for r in (again,again,wrong,missing):ecology.note_gap(st,r['edge'],'2026-11-08T10:00','observe')
    g={(x['kind'],x['target']):x for x in st['world_gaps']}
    assert g[('seen_all',tree['id'])]['times']==2 and len(st['world_gaps'])==3
    # Any inspectable thing: the second identical look says so.
    app.state['pending']=None
    def inspect(ident):
        d={**app.DECISION_DEFAULTS,'action':'inspect','object_id':ident,'intention':'look','reason':'r'}
        app.state['pending']={'decision':d,'action':'inspect','duration':60,'remaining':0,'start':app.now().isoformat(),'project_id':-1}
        app.finish_action()
        return app.state['memories'][-1]['event']
    obj=next(iter(st['built_world']['objects']))
    assert 'by eye' not in inspect(obj) and 'by eye has been seen before' in inspect(obj)
    # The log is never part of his decisions.
    assert 'world_gaps' not in __import__('json').dumps(app.decision_context())
print('PASS v0.21.6: seen-all, wrong place and not-found edges stated plainly; gaps logged for the builder, never for him.')
